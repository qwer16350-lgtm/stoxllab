"""Read-only NAS metadata scan and local keyword index for STOXL RAG v0.8A."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import warnings
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".docx",
    ".xlsx",
    ".pptx",
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".tiff",
    ".bmp",
    ".heic",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".bmp", ".heic"}
TEXT_PREVIEW_EXTENSIONS = {".md", ".txt", ".csv", ".json"}
DEFAULT_MAX_FILES = 500
MAX_ALLOWED_FILES = 50000
DEFAULT_MAX_TOTAL_BYTES = 0
DEFAULT_MAX_FILE_SIZE_MB = 25
DEFAULT_MAX_IMAGE_FILE_SIZE_MB = 25
DEFAULT_MAX_IMAGE_PIXELS = 80_000_000
MAX_ALLOWED_FILE_SIZE_MB = 512
MAX_ALLOWED_IMAGE_PIXELS = 200_000_000
MAX_HASH_BYTES = 1024 * 1024
MAX_PREVIEW_BYTES = 32 * 1024
INDEX_FILE_NAME = "nas_rag_index.json"
SKIP_IMAGE_PIXEL_TOO_LARGE = "[image_pixel_too_large]"
MAX_RAG_QUERY_CHARS = 200


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _base_report(report_type: str) -> dict[str, Any]:
    return {
        "report_type": report_type,
        "nas_root_value_logged": False,
        "nas_write_attempted": False,
        "nas_file_modified": False,
        "nas_file_deleted": False,
        "embedding_called": False,
        "vector_index_created": False,
        "llm_called": False,
        "llm_api_called": False,
        "web_search_called": False,
        "vision_api_called": False,
        "ocr_called": False,
        "external_execution": False,
        "secret_value_logged": False,
        "raw_nas_root_logged": False,
        "raw_nas_absolute_path_logged": False,
    }


def _env(env: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict(os.environ if env is None else env)


def _nas_root(env: dict[str, Any] | None = None) -> Path | None:
    value = _env(env).get("HERMES_RAG_NAS_ROOT")
    return Path(str(value)) if value else None


def _index_dir(env: dict[str, Any] | None = None) -> Path:
    value = _env(env).get("HERMES_RAG_INDEX_DIR")
    if value:
        return Path(str(value))
    return Path(__file__).resolve().parent / "local" / "rag_index"


def _safe_count_limit(env: dict[str, Any] | None = None) -> int:
    env_map = _env(env)
    raw = env_map.get("HERMES_RAG_MAX_FILES", env_map.get("HERMES_RAG_SCAN_MAX_FILES", DEFAULT_MAX_FILES))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_FILES
    return max(1, min(value, MAX_ALLOWED_FILES))


def _safe_int_env(name: str, default: int, env: dict[str, Any] | None = None, *, minimum: int = 0, maximum: int = 10**12) -> int:
    raw = _env(env).get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(value, maximum))


def _safe_size_mb(name: str, default: int, env: dict[str, Any] | None = None) -> int:
    return _safe_int_env(name, default, env, minimum=1, maximum=MAX_ALLOWED_FILE_SIZE_MB)


def _max_total_bytes(env: dict[str, Any] | None = None) -> int:
    return _safe_int_env("HERMES_RAG_MAX_TOTAL_BYTES", DEFAULT_MAX_TOTAL_BYTES, env, minimum=0, maximum=10**13)


def _max_file_size_bytes(env: dict[str, Any] | None = None) -> int:
    return _safe_size_mb("HERMES_RAG_MAX_FILE_SIZE_MB", DEFAULT_MAX_FILE_SIZE_MB, env) * 1024 * 1024


def _max_image_file_size_bytes(env: dict[str, Any] | None = None) -> int:
    return _safe_size_mb("HERMES_RAG_MAX_IMAGE_FILE_SIZE_MB", DEFAULT_MAX_IMAGE_FILE_SIZE_MB, env) * 1024 * 1024


def _max_image_pixels(env: dict[str, Any] | None = None) -> int:
    return _safe_int_env(
        "HERMES_RAG_MAX_IMAGE_PIXELS",
        DEFAULT_MAX_IMAGE_PIXELS,
        env,
        minimum=1,
        maximum=MAX_ALLOWED_IMAGE_PIXELS,
    )


def _is_accessible_dir(path: Path | None) -> bool:
    if path is None:
        return False
    try:
        return path.exists() and path.is_dir()
    except OSError:
        return False


def _hash_path_label(relative_path: str) -> str:
    return hashlib.sha256(relative_path.replace("\\", "/").encode("utf-8", errors="ignore")).hexdigest()[:16]


def _safe_relative_path(value: Any) -> str:
    raw = str(value or "").replace("\\", "/").strip()
    parts = [part for part in raw.split("/") if part not in {"", ".", ".."}]
    return "/".join(parts)[:500]


def _source_label(file_name: str) -> str:
    stem = Path(str(file_name or "document")).stem.replace("_", " ").replace("-", " ").strip()
    return (stem or str(file_name or "document")).strip()[:120]


def _content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    remaining = MAX_HASH_BYTES
    try:
        with path.open("rb") as handle:
            while remaining > 0:
                chunk = handle.read(min(65536, remaining))
                if not chunk:
                    break
                digest.update(chunk)
                remaining -= len(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _text_preview(path: Path, extension: str) -> str:
    if extension not in TEXT_PREVIEW_EXTENSIONS:
        return ""
    try:
        raw = path.read_bytes()[:MAX_PREVIEW_BYTES]
    except OSError:
        return ""
    return raw.decode("utf-8", errors="ignore")[:2000]


def _pptx_preview(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as deck:
            slide_names = sorted(
                name
                for name in deck.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            lines = [f"[PPTX] {path.name[:180]}"]
            for index, name in enumerate(slide_names[:80], start=1):
                try:
                    root = ElementTree.fromstring(deck.read(name))
                except (ElementTree.ParseError, KeyError, OSError):
                    continue
                texts = [
                    node.text.strip()
                    for node in root.iter()
                    if node.tag.endswith("}t") and node.text and node.text.strip()
                ]
                if texts:
                    lines.append(f"Slide {index}: {' '.join(texts)[:1000]}")
            return "\n".join(lines)[:4000]
    except (OSError, zipfile.BadZipFile):
        return ""
    return ""


def _png_dimensions(header: bytes) -> tuple[int | None, int | None]:
    if len(header) >= 24 and header.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", header[16:24])
    return None, None


def _gif_dimensions(header: bytes) -> tuple[int | None, int | None]:
    if len(header) >= 10 and (header.startswith(b"GIF87a") or header.startswith(b"GIF89a")):
        return struct.unpack("<HH", header[6:10])
    return None, None


def _jpeg_dimensions(path: Path) -> tuple[int | None, int | None]:
    try:
        with path.open("rb") as handle:
            if handle.read(2) != b"\xff\xd8":
                return None, None
            while True:
                marker_prefix = handle.read(1)
                if not marker_prefix:
                    return None, None
                if marker_prefix != b"\xff":
                    continue
                marker = handle.read(1)
                while marker == b"\xff":
                    marker = handle.read(1)
                if marker in {b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"}:
                    segment = handle.read(7)
                    if len(segment) >= 7:
                        height, width = struct.unpack(">HH", segment[3:7])
                        return width, height
                    return None, None
                length_raw = handle.read(2)
                if len(length_raw) != 2:
                    return None, None
                length = struct.unpack(">H", length_raw)[0]
                if length < 2:
                    return None, None
                handle.seek(length - 2, 1)
    except OSError:
        return None, None


def _image_dimensions(path: Path, extension: str) -> tuple[int | None, int | None]:
    try:
        from PIL.Image import DecompressionBombWarning  # type: ignore
        from PIL import Image  # type: ignore

        with warnings.catch_warnings():
            warnings.simplefilter("error", DecompressionBombWarning)
            with Image.open(path) as image:
                width, height = image.size
                return int(width), int(height)
    except Exception:
        pass
    try:
        header = path.read_bytes()[:64]
    except OSError:
        return None, None
    if extension == ".png":
        return _png_dimensions(header)
    if extension == ".gif":
        return _gif_dimensions(header)
    if extension in {".jpg", ".jpeg"}:
        return _jpeg_dimensions(path)
    return None, None


def _image_pixel_too_large(width: int | None, height: int | None, max_image_pixels: int) -> bool:
    if width is None or height is None:
        return False
    return width * height > max_image_pixels


def _content_preview(path: Path, extension: str) -> str:
    if extension == ".pptx":
        return _pptx_preview(path)
    return _text_preview(path, extension)


def _file_record(root: Path, path: Path, dimensions: tuple[int | None, int | None] | None = None) -> dict[str, Any]:
    try:
        relative = str(path.relative_to(root))
    except ValueError:
        relative = path.name
    extension = path.suffix.lower()
    try:
        stat = path.stat()
    except OSError:
        stat = None
    parent_name = path.parent.name if path.parent != root else ""
    width, height = dimensions if dimensions is not None else _image_dimensions(path, extension) if extension in IMAGE_EXTENSIONS else (None, None)
    return {
        "path_hash": _hash_path_label(relative),
        "file_name": path.name[:240],
        "folder_name": parent_name[:160],
        "relative_path": _safe_relative_path(relative),
        "source_label": _source_label(path.name),
        "chunk_index": 0,
        "extension": extension,
        "asset_type": "image_metadata" if extension in IMAGE_EXTENSIONS else "document_metadata",
        "media_type": "image" if extension in IMAGE_EXTENSIONS else "document",
        "size_bytes": int(stat.st_size) if stat else 0,
        "modified_at_present": stat is not None,
        "content_hash": _content_hash(path),
        "width": width,
        "height": height,
        "content_preview": _content_preview(path, extension),
        "vision_api_called": False,
        "ocr_called": False,
        "raw_nas_absolute_path_logged": False,
    }


def _rag_runtime_safety_fields() -> dict[str, Any]:
    return {
        "rag_runtime_command": True,
        "rag_mode": "keyword_only",
        "nas_write_attempted": False,
        "nas_file_modified": False,
        "nas_file_deleted": False,
        "index_write_attempted_from_runtime": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "llm_called": False,
        "llm_api_called": False,
        "web_search_called": False,
        "vision_api_called": False,
        "ocr_called": False,
        "external_execution": False,
        "raw_nas_absolute_path_logged": False,
        "raw_index_absolute_path_logged": False,
        "secret_value_logged": False,
    }


def _iter_files(root: Path, max_files: int) -> tuple[list[Path], bool]:
    selected: list[Path] = []
    truncated = False
    stack = [root]
    while stack and len(selected) < max_files:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir(), key=lambda item: item.name.lower())
        except OSError:
            continue
        for entry in entries:
            if len(selected) >= max_files:
                truncated = True
                break
            try:
                if entry.is_dir():
                    stack.append(entry)
                elif entry.is_file():
                    selected.append(entry)
            except OSError:
                continue
    if stack:
        truncated = True
    return selected, truncated


def scan_nas_files(*, dry_run: bool = True, env: dict[str, Any] | None = None) -> dict[str, Any]:
    root = _nas_root(env)
    root_present = root is not None
    root_accessible = _is_accessible_dir(root)
    max_total_bytes = _max_total_bytes(env)
    max_file_size_bytes = _max_file_size_bytes(env)
    max_image_size_bytes = _max_image_file_size_bytes(env)
    max_image_pixels = _max_image_pixels(env)
    report = {
        **_base_report("rag_scan_nas_dry_run" if dry_run else "rag_scan_nas"),
        "nas_root_present": root_present,
        "nas_root_accessible": root_accessible,
        "files_seen": 0,
        "files_supported": 0,
        "files_skipped": 0,
        "skip_summary": {},
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "image_extensions_supported": sorted(IMAGE_EXTENSIONS),
        "would_write_index": False,
        "scan_truncated": False,
        "max_files": _safe_count_limit(env),
        "max_total_bytes": max_total_bytes,
        "max_file_size_mb": max_file_size_bytes // (1024 * 1024),
        "max_image_file_size_mb": max_image_size_bytes // (1024 * 1024),
        "max_image_pixels": max_image_pixels,
        "image_pixel_limit_enabled": True,
        "decompression_bomb_warning_suppressed": True,
        "sample_assets": [],
    }
    if not root_accessible or root is None:
        return report
    files, truncated = _iter_files(root, int(report["max_files"]))
    skip_summary: dict[str, int] = {}
    sample_assets: list[dict[str, Any]] = []
    supported = 0
    total_bytes_seen = 0
    total_cap_reached = False
    for path in files:
        extension = path.suffix.lower()
        try:
            size_bytes = path.stat().st_size
        except OSError:
            size_bytes = 0
        if max_total_bytes and total_bytes_seen + size_bytes > max_total_bytes:
            total_cap_reached = True
            break
        total_bytes_seen += size_bytes
        if extension not in SUPPORTED_EXTENSIONS:
            skip_summary[extension or "[no_extension]"] = skip_summary.get(extension or "[no_extension]", 0) + 1
            continue
        selected_size_limit = max_image_size_bytes if extension in IMAGE_EXTENSIONS else max_file_size_bytes
        if size_bytes > selected_size_limit:
            key = "[image_too_large]" if extension in IMAGE_EXTENSIONS else "[file_too_large]"
            skip_summary[key] = skip_summary.get(key, 0) + 1
            continue
        dimensions = _image_dimensions(path, extension) if extension in IMAGE_EXTENSIONS else (None, None)
        if extension in IMAGE_EXTENSIONS and _image_pixel_too_large(dimensions[0], dimensions[1], max_image_pixels):
            skip_summary[SKIP_IMAGE_PIXEL_TOO_LARGE] = skip_summary.get(SKIP_IMAGE_PIXEL_TOO_LARGE, 0) + 1
            continue
        supported += 1
        if len(sample_assets) < 10:
            record = _file_record(root, path, dimensions)
            sample_assets.append(
                {
                    "path_hash": record["path_hash"],
                    "file_name": record["file_name"],
                    "folder_name": record["folder_name"],
                    "extension": record["extension"],
                    "asset_type": record["asset_type"],
                    "size_bytes": record["size_bytes"],
                    "modified_at_present": record["modified_at_present"],
                    "content_hash_present": bool(record["content_hash"]),
                    "width": record["width"],
                    "height": record["height"],
                    "vision_api_called": False,
                    "ocr_called": False,
                    "raw_nas_absolute_path_logged": False,
                }
            )
    report.update(
        {
            "files_seen": len(files),
            "files_supported": supported,
            "files_skipped": len(files) - supported,
            "skip_summary": skip_summary,
            "scan_truncated": truncated or total_cap_reached,
            "total_bytes_seen": total_bytes_seen,
            "sample_assets": sample_assets,
        }
    )
    return report


def _index_dir_is_inside_nas(index_dir: Path, nas_root: Path) -> bool:
    try:
        index_resolved = index_dir.resolve()
        nas_resolved = nas_root.resolve()
    except OSError:
        return False
    return index_resolved == nas_resolved or nas_resolved in index_resolved.parents


def build_nas_index(*, allow_write: bool = False, env: dict[str, Any] | None = None) -> dict[str, Any]:
    root = _nas_root(env)
    root_present = root is not None
    root_accessible = _is_accessible_dir(root)
    index_dir = _index_dir(env)
    base = {
        **_base_report("rag_index_nas"),
        "nas_root_present": root_present,
        "nas_root_accessible": root_accessible,
        "index_dir_present": bool(_env(env).get("HERMES_RAG_INDEX_DIR")),
        "index_dir_value_logged": False,
        "allow_rag_index_write": bool(allow_write),
        "blocked": False,
        "blocked_reason": "",
        "index_write_attempted": False,
        "index_file_written": False,
        "index_record_count": 0,
        "max_files": _safe_count_limit(env),
        "max_total_bytes": _max_total_bytes(env),
        "max_file_size_mb": _max_file_size_bytes(env) // (1024 * 1024),
        "max_image_file_size_mb": _max_image_file_size_bytes(env) // (1024 * 1024),
        "max_image_pixels": _max_image_pixels(env),
        "image_pixel_limit_enabled": True,
        "decompression_bomb_warning_suppressed": True,
        "skip_summary": {},
        "nas_originals_modified": False,
        "nas_cache_created": False,
        "thumbnail_created_on_nas": False,
        "thumbnail_created_local": False,
        "vector_index_created": False,
    }
    if not allow_write:
        return {**base, "blocked": True, "blocked_reason": "allow_rag_index_write_missing"}
    if not root_accessible or root is None:
        return {**base, "blocked": True, "blocked_reason": "nas_root_missing_or_inaccessible"}
    if _index_dir_is_inside_nas(index_dir, root):
        return {**base, "blocked": True, "blocked_reason": "index_dir_inside_nas_root_forbidden"}
    files, truncated = _iter_files(root, _safe_count_limit(env))
    records: list[dict[str, Any]] = []
    max_total_bytes = _max_total_bytes(env)
    max_file_size_bytes = _max_file_size_bytes(env)
    max_image_size_bytes = _max_image_file_size_bytes(env)
    max_image_pixels = _max_image_pixels(env)
    total_bytes_seen = 0
    total_cap_reached = False
    skip_summary: dict[str, int] = {}
    for path in files:
        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            continue
        try:
            size_bytes = path.stat().st_size
        except OSError:
            size_bytes = 0
        if max_total_bytes and total_bytes_seen + size_bytes > max_total_bytes:
            total_cap_reached = True
            break
        total_bytes_seen += size_bytes
        selected_size_limit = max_image_size_bytes if extension in IMAGE_EXTENSIONS else max_file_size_bytes
        if size_bytes > selected_size_limit:
            key = "[image_too_large]" if extension in IMAGE_EXTENSIONS else "[file_too_large]"
            skip_summary[key] = skip_summary.get(key, 0) + 1
            continue
        dimensions = _image_dimensions(path, extension) if extension in IMAGE_EXTENSIONS else (None, None)
        if extension in IMAGE_EXTENSIONS and _image_pixel_too_large(dimensions[0], dimensions[1], max_image_pixels):
            skip_summary[SKIP_IMAGE_PIXEL_TOO_LARGE] = skip_summary.get(SKIP_IMAGE_PIXEL_TOO_LARGE, 0) + 1
            continue
        records.append(_file_record(root, path, dimensions))
    payload = {
        "index_type": "stoxl_nas_rag_metadata_index_v08a",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
        "scan_truncated": truncated,
        "raw_nas_absolute_path_logged": False,
        "secret_value_logged": False,
    }
    try:
        index_dir.mkdir(parents=True, exist_ok=True)
        (index_dir / INDEX_FILE_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return {**base, "blocked": True, "blocked_reason": "local_index_write_failed", "index_write_attempted": True}
    return {
        **base,
        "index_write_attempted": True,
        "index_file_written": True,
        "index_record_count": len(records),
        "files_seen": len(files),
        "files_supported": len(records),
        "files_skipped": len(files) - len(records),
        "skip_summary": skip_summary,
        "scan_truncated": truncated or total_cap_reached,
        "total_bytes_seen": total_bytes_seen,
    }


def _load_index_payload(env: dict[str, Any] | None = None) -> tuple[dict[str, Any] | None, str]:
    index_path = _index_dir(env) / INDEX_FILE_NAME
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "local_index_missing"
    except (OSError, json.JSONDecodeError):
        return None, "local_index_unreadable"
    return payload if isinstance(payload, dict) else {}, ""


def get_rag_index_status(*, env: dict[str, Any] | None = None) -> dict[str, Any]:
    payload, failure_reason = _load_index_payload(env)
    records = payload.get("records") if isinstance(payload, dict) else []
    if not isinstance(records, list):
        records = []
    return {
        **_base_report("rag_index_status"),
        **_rag_runtime_safety_fields(),
        "index_available": failure_reason == "",
        "index_present": failure_reason == "",
        "record_count": len(records) if failure_reason == "" else 0,
        "mode": "keyword_only",
        "blocked": failure_reason != "",
        "blocked_reason": failure_reason,
        "index_dir_value_logged": False,
        "raw_index_absolute_path_logged": False,
    }


def _snippet_for_record(record: dict[str, Any], query_terms: list[str], limit: int = 240) -> str:
    preview = str(record.get("content_preview") or "").replace("\r", " ").strip()
    if not preview:
        if str(record.get("media_type") or record.get("asset_type") or "").startswith("image"):
            width = record.get("width")
            height = record.get("height")
            size = f" {width}x{height}" if width and height else ""
            return f"Image asset metadata.{size}".strip()[:limit]
        return "Document metadata."
    folded = preview.casefold()
    start = 0
    for term in query_terms:
        found = folded.find(term)
        if found >= 0:
            start = max(0, found - 50)
            break
    return preview[start : start + limit].strip().replace("\n", " ")[:limit]


def _record_score(record: dict[str, Any], query_terms: list[str]) -> float:
    haystack = " ".join(
        str(record.get(key) or "")
        for key in (
            "source_label",
            "relative_path",
            "file_name",
            "folder_name",
            "extension",
            "asset_type",
            "media_type",
            "content_preview",
        )
    ).casefold()
    score = 0.0
    for term in query_terms:
        count = haystack.count(term)
        score += 1.0 + min(count, 8) if count else 0.0
    return round(score, 2)


def _search_result_from_record(record: dict[str, Any], query_terms: list[str]) -> dict[str, Any]:
    file_name = str(record.get("file_name") or "document")
    folder_name = str(record.get("folder_name") or "")
    relative_path = _safe_relative_path(record.get("relative_path") or "/".join(part for part in (folder_name, file_name) if part))
    media_type = str(record.get("media_type") or "")
    asset_type = str(record.get("asset_type") or "")
    is_image = media_type == "image" or asset_type == "image_metadata"
    chunk_index = int(record.get("chunk_index") or 0)
    return {
        "source_label": str(record.get("source_label") or _source_label(file_name)),
        "relative_path": relative_path,
        "file_name": file_name[:240],
        "folder_name": folder_name[:160],
        "extension": str(record.get("extension") or ""),
        "asset_type": asset_type or ("image_metadata" if is_image else "document_metadata"),
        "media_type": "image" if is_image else "document",
        "chunk_index": chunk_index,
        "chunk_id": f"{'image' if is_image else 'doc'}#{chunk_index}",
        "score": _record_score(record, query_terms),
        "snippet": _snippet_for_record(record, query_terms),
        "width": record.get("width") if is_image else None,
        "height": record.get("height") if is_image else None,
        "path_hash": record.get("path_hash"),
        "raw_nas_absolute_path_logged": False,
        "raw_index_absolute_path_logged": False,
    }


def search_rag_index(query: str, *, env: dict[str, Any] | None = None, limit: int = 5) -> dict[str, Any]:
    query_text = str(query or "").strip()
    base = {
        **_base_report("rag_search_nas_index"),
        **_rag_runtime_safety_fields(),
        "query_present": bool(query_text),
        "query_too_long": len(query_text) > MAX_RAG_QUERY_CHARS,
        "index_dir_value_logged": False,
        "index_present": False,
        "search_attempted": False,
        "result_count": 0,
        "results": [],
        "mode": "keyword_only",
        "limit": max(1, min(int(limit or 5), 10)),
    }
    if not query_text:
        return {**base, "blocked": True, "blocked_reason": "query_missing"}
    if len(query_text) > MAX_RAG_QUERY_CHARS:
        return {**base, "blocked": True, "blocked_reason": "query_too_long", "query": query_text[:MAX_RAG_QUERY_CHARS]}
    payload, failure_reason = _load_index_payload(env)
    if failure_reason:
        return {**base, "blocked": True, "blocked_reason": failure_reason}
    records = payload.get("records") if isinstance(payload, dict) else []
    if not isinstance(records, list):
        records = []
    query_terms = [part.casefold() for part in query_text.split() if part.strip()]
    matches: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        haystack = " ".join(
            str(record.get(key) or "")
            for key in (
                "source_label",
                "relative_path",
                "file_name",
                "folder_name",
                "extension",
                "asset_type",
                "media_type",
                "content_preview",
            )
        ).casefold()
        if all(term in haystack for term in query_terms):
            matches.append(_search_result_from_record(record, query_terms))
    matches.sort(key=lambda item: float(item.get("score") or 0), reverse=True)
    selected = matches[: int(base["limit"])]
    return {
        **base,
        "blocked": False,
        "blocked_reason": "",
        "query": query_text,
        "index_present": True,
        "index_available": True,
        "search_attempted": True,
        "record_count": len(records),
        "result_count": len(selected),
        "results": selected,
    }


def search_nas_index(query: str, *, env: dict[str, Any] | None = None, limit: int = 10) -> dict[str, Any]:
    return search_rag_index(query, env=env, limit=limit)


def _display_query(query: str) -> str:
    return str(query or "").replace("\r", " ").replace("\n", " ").strip()[:120]


def format_rag_status_for_discord(status: dict[str, Any]) -> str:
    if not status.get("index_available"):
        return (
            "[HERMES_STOXL] RAG status\n\n"
            "index: not available\n"
            "Please build the local NAS index from CLI first.\n\n"
            "python apps\\hermes_gateway\\cli.py --rag-index-nas --json --allow-rag-index-write\n\n"
            "nas write: false\n"
            "llm: false\n"
            "embedding: false\n"
            "vision: false\n"
            "ocr: false"
        )
    return (
        "[HERMES_STOXL] RAG status\n\n"
        "index: available\n"
        f"records: {int(status.get('record_count') or 0)}\n"
        "mode: keyword_only\n"
        "nas write: false\n"
        "llm: false\n"
        "embedding: false\n"
        "vision: false\n"
        "ocr: false\n\n"
        "commands:\n"
        "!rag-search <query>\n"
        "!docs <query>\n"
        "!recall-doc <query>"
    )


def format_rag_search_results_for_discord(result: dict[str, Any]) -> str:
    query = _display_query(str(result.get("query") or ""))
    reason = str(result.get("blocked_reason") or "")
    if reason == "query_missing":
        return (
            "[HERMES_STOXL]\n"
            "Please enter a search query.\n\n"
            "Examples:\n"
            "!rag-search brand guide\n"
            "!docs homepage copy\n"
            "!recall-doc support documents"
        )
    if reason == "query_too_long":
        return "[HERMES_STOXL]\nRAG query is too long.\nreason: query_too_long"
    if reason:
        return (
            "[HERMES_STOXL]\n"
            "RAG index is not available.\n"
            "Please build the local index from CLI first.\n"
            "reason: local_index_missing"
        )
    results = list(result.get("results") or [])
    if not results:
        return (
            "[HERMES_STOXL] RAG search results\n\n"
            f"query: {query}\n"
            "results: 0\n"
            "mode: keyword_only\n\n"
            "No matching results found. Try another keyword."
        )
    lines = [
        "[HERMES_STOXL] RAG search results",
        "",
        f"query: {query}",
        f"results: {len(results)}",
        "mode: keyword_only",
        "",
    ]
    for index, item in enumerate(results, start=1):
        lines.extend(
            [
                f"{index}. {item.get('source_label')}",
                f"   path: {item.get('relative_path')}",
                f"   type: {item.get('media_type')}",
                f"   chunk: {item.get('chunk_id')}",
                f"   score: {item.get('score')}",
            ]
        )
        if item.get("media_type") == "image" and item.get("width") and item.get("height"):
            lines.append(f"   size: {item.get('width')}x{item.get('height')}")
        lines.extend([f"   snippet: {item.get('snippet')}", ""])
    return "\n".join(lines).strip()


def build_rag_discord_command_response(command: str, query: str = "", *, env: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = str(command or "").strip().lower()
    try:
        if normalized == "rag-status":
            status = get_rag_index_status(env=env)
            return {
                **status,
                "response_type": "rag_discord_command_response",
                "reply_text_source": "rag_status",
                "command": normalized,
                "content": format_rag_status_for_discord(status),
            }
        search = search_rag_index(query, env=env, limit=5)
        return {
            **search,
            "response_type": "rag_discord_command_response",
            "reply_text_source": "rag_search",
            "command": normalized,
            "content": format_rag_search_results_for_discord(search),
        }
    except Exception:
        return {
            **_base_report("rag_discord_runtime_exception"),
            **_rag_runtime_safety_fields(),
            "response_type": "rag_discord_command_response",
            "reply_text_source": "rag_runtime_exception",
            "command": normalized,
            "blocked": True,
            "blocked_reason": "rag_search_runtime_exception",
            "content": "[HERMES_STOXL]\nRAG search failed.\nreason: rag_search_runtime_exception",
        }


def parse_rag_discord_command(content: str) -> dict[str, Any]:
    lines = [line.strip() for line in str(content or "").replace("\r\n", "\n").split("\n")]
    for line in lines:
        if not line.startswith("!"):
            continue
        parts = line.split(maxsplit=1)
        command = parts[0].lstrip("!").strip().lower()
        if command not in {"rag-status", "rag-search", "docs", "recall-doc"}:
            continue
        return {
            "rag_runtime_command": True,
            "command": command,
            "query": parts[1].strip() if len(parts) > 1 else "",
        }
    return {"rag_runtime_command": False, "command": "", "query": ""}
