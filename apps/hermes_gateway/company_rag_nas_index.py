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
        "extension": extension,
        "asset_type": "image_metadata" if extension in IMAGE_EXTENSIONS else "document_metadata",
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


def search_nas_index(query: str, *, env: dict[str, Any] | None = None, limit: int = 10) -> dict[str, Any]:
    index_path = _index_dir(env) / INDEX_FILE_NAME
    report = {
        **_base_report("rag_search_nas_index"),
        "query_present": bool(str(query or "").strip()),
        "index_dir_value_logged": False,
        "index_present": False,
        "search_attempted": False,
        "result_count": 0,
        "results": [],
        "vector_index_created": False,
    }
    if not report["query_present"]:
        return {**report, "blocked": True, "blocked_reason": "query_missing"}
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {**report, "blocked": True, "blocked_reason": "local_index_missing"}
    records = payload.get("records") if isinstance(payload, dict) else []
    if not isinstance(records, list):
        records = []
    query_terms = [part.casefold() for part in str(query or "").split() if part.strip()]
    matches: list[dict[str, Any]] = []
    for record in records:
        haystack = " ".join(
            str(record.get(key) or "")
            for key in ("file_name", "folder_name", "extension", "asset_type", "content_preview")
        ).casefold()
        if all(term in haystack for term in query_terms):
            matches.append(
                {
                    "path_hash": record.get("path_hash"),
                    "file_name": record.get("file_name"),
                    "folder_name": record.get("folder_name"),
                    "extension": record.get("extension"),
                    "asset_type": record.get("asset_type"),
                    "size_bytes": record.get("size_bytes"),
                    "raw_nas_absolute_path_logged": False,
                }
            )
        if len(matches) >= max(1, min(limit, 50)):
            break
    return {
        **report,
        "blocked": False,
        "index_present": True,
        "search_attempted": True,
        "result_count": len(matches),
        "results": matches,
    }
