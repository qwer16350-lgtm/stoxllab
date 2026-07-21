"""Local embedding/vector and hybrid retrieval foundation for STOXL RAG v0.8C."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from company_rag_nas_index import (
    IMAGE_EXTENSIONS,
    INDEX_FILE_NAME,
    format_rag_search_results_for_discord,
    get_rag_index_status,
    search_rag_index,
)


VECTOR_MANIFEST_NAME = "vector_manifest.json"
VECTOR_RECORDS_NAME = "records.jsonl"
VECTORS_JSON_NAME = "vectors.json"
BUILD_REPORT_NAME = "build_report.json"
DEFAULT_EMBEDDING_BACKEND = "local_sentence_transformers"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_VECTOR_INDEX_VERSION = "v0.8C"
DEFAULT_VECTOR_DIMENSION = 384
MAX_QUERY_CHARS = 200
_MODEL_CACHE: dict[tuple[str, str], Any] = {}


class EmbeddingBackend(Protocol):
    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        ...


def _env(env: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict(os.environ if env is None else env)


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _float_env(env: dict[str, Any], name: str, default: float) -> float:
    try:
        return float(env.get(name, default))
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = 512) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _keyword_index_dir(env: dict[str, Any]) -> Path:
    value = env.get("HERMES_RAG_INDEX_DIR")
    if value:
        return Path(str(value))
    return Path(__file__).resolve().parent / "local" / "rag_index"


def _vector_index_dir(env: dict[str, Any]) -> Path:
    value = env.get("HERMES_RAG_VECTOR_INDEX_DIR")
    if value:
        return Path(str(value))
    return Path(__file__).resolve().parent / "local" / "rag_vector_index"


def _load_keyword_records(env: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    try:
        payload = json.loads((_keyword_index_dir(env) / INDEX_FILE_NAME).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [], "local_index_missing"
    except (OSError, json.JSONDecodeError):
        return [], "local_index_unreadable"
    records = payload.get("records") if isinstance(payload, dict) else []
    if not isinstance(records, list):
        return [], "local_index_unreadable"
    return [record for record in records if isinstance(record, dict)], ""


def _load_vector_index(env: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[list[float]], str]:
    root = _vector_index_dir(env)
    try:
        manifest = json.loads((root / VECTOR_MANIFEST_NAME).read_text(encoding="utf-8"))
        records = [json.loads(line) for line in (root / VECTOR_RECORDS_NAME).read_text(encoding="utf-8").splitlines() if line.strip()]
        vectors = json.loads((root / VECTORS_JSON_NAME).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [], [], "vector_index_missing"
    except (OSError, json.JSONDecodeError):
        return {}, [], [], "vector_index_unreadable"
    if not isinstance(manifest, dict) or not isinstance(records, list) or not isinstance(vectors, list):
        return {}, [], [], "vector_index_unreadable"
    return manifest, records, vectors, ""


def _base_safety(report_type: str) -> dict[str, Any]:
    return {
        "report_type": report_type,
        "nas_write_attempted": False,
        "nas_file_modified": False,
        "nas_file_deleted": False,
        "vector_index_written_local_only": False,
        "external_embedding_api_called": False,
        "local_embedding_model_used": False,
        "llm_called": False,
        "web_search_called": False,
        "vision_api_called": False,
        "ocr_called": False,
        "external_execution": False,
        "raw_nas_absolute_path_logged": False,
        "raw_index_absolute_path_logged": False,
        "raw_vector_logged": False,
        "secret_value_logged": False,
    }


def _embedding_config(env: dict[str, Any]) -> dict[str, Any]:
    return {
        "embedding_enabled": _flag(env.get("HERMES_RAG_EMBEDDING_ENABLED"), False),
        "embedding_backend": str(env.get("HERMES_RAG_EMBEDDING_BACKEND") or DEFAULT_EMBEDDING_BACKEND),
        "embedding_model": str(env.get("HERMES_RAG_EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL),
        "embedding_batch_size": _safe_int(env.get("HERMES_RAG_EMBEDDING_BATCH_SIZE"), 32, 1, 256),
        "embedding_device": str(env.get("HERMES_RAG_EMBEDDING_DEVICE") or "cpu"),
        "vector_index_dir_present": bool(env.get("HERMES_RAG_VECTOR_INDEX_DIR")),
        "vector_index_dir_value_logged": False,
    }


def build_rag_embedding_preflight(env: dict[str, Any] | None = None) -> dict[str, Any]:
    env_map = _env(env)
    sentence_transformers_available = importlib.util.find_spec("sentence_transformers") is not None
    vector_status = get_rag_vector_status(env_map)
    return {
        **_base_safety("rag_embedding_preflight"),
        **_embedding_config(env_map),
        "default_embedding_enabled": False,
        "sentence_transformers_dependency_available": sentence_transformers_available,
        "embedding_dependency_lazy_import": True,
        "model_file_committed": False,
        "model_download_requires_allow_flag": True,
        "vector_index_available": bool(vector_status.get("vector_index_available")),
        "vector_record_count": int(vector_status.get("vector_record_count") or 0),
        "blocked": False,
        "blocked_reason": "",
    }


def _source_id(record: dict[str, Any]) -> str:
    raw = "|".join(str(record.get(key) or "") for key in ("path_hash", "relative_path", "file_name", "content_hash"))
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _safe_relative_path(value: Any) -> str:
    raw = str(value or "").replace("\\", "/")
    parts = [part for part in raw.split("/") if part not in {"", ".", ".."}]
    return "/".join(parts)[:500]


def _record_text(record: dict[str, Any]) -> str:
    extension = str(record.get("extension") or "").lower()
    if extension in IMAGE_EXTENSIONS or str(record.get("asset_type") or "") == "image_metadata":
        size = ""
        if record.get("width") and record.get("height"):
            size = f"size: {record.get('width')}x{record.get('height')}."
        return " ".join(
            part
            for part in (
                "Image asset.",
                f"file: {record.get('file_name')}.",
                f"folder: {record.get('folder_name')}.",
                f"path: {_safe_relative_path(record.get('relative_path'))}.",
                f"type: {record.get('asset_type') or 'image_metadata'}.",
                size,
                str(record.get("content_preview") or ""),
            )
            if str(part).strip()
        )[:4000]
    return " ".join(
        part
        for part in (
            f"source: {record.get('source_label') or record.get('file_name')}.",
            f"path: {_safe_relative_path(record.get('relative_path'))}.",
            f"type: {record.get('asset_type') or 'document_metadata'}.",
            str(record.get("content_preview") or ""),
        )
        if str(part).strip()
    )[:4000]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(float(value) * float(value) for value in vector))
    if norm <= 0:
        return [0.0 for _ in vector]
    return [round(float(value) / norm, 8) for value in vector]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b))


class HashEmbeddingBackend:
    def __init__(self, dimension: int = DEFAULT_VECTOR_DIMENSION) -> None:
        self.dimension = dimension

    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            buckets = [0.0] * self.dimension
            for token in str(text or "").casefold().split():
                digest = hashlib.sha256(token.encode("utf-8", errors="ignore")).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimension
                buckets[index] += 1.0
            vectors.append(_normalize(buckets))
        return vectors


class SentenceTransformersBackend:
    def __init__(self, model: Any) -> None:
        self.model = model

    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        encoded = self.model.encode(texts, normalize_embeddings=True)
        return [[float(value) for value in vector] for vector in encoded]


def _load_sentence_transformer_class() -> Any | None:
    if not importlib.util.find_spec("sentence_transformers"):
        return None
    from sentence_transformers import SentenceTransformer  # type: ignore

    return SentenceTransformer


def _cache_model(model_name: str, device: str, model: Any) -> Any:
    _MODEL_CACHE[(model_name, device)] = model
    return model


def _load_cached_huggingface_snapshot(model_name: str) -> str | None:
    if not importlib.util.find_spec("huggingface_hub"):
        return None
    try:
        from huggingface_hub import snapshot_download  # type: ignore

        return str(snapshot_download(repo_id=model_name, local_files_only=True))
    except Exception:
        return None


def load_local_embedding_model(
    model_name: str,
    device: str,
    allow_download: bool,
    *,
    model_factory: Any | None = None,
) -> tuple[Any | None, str]:
    cache_key = (model_name, device)
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key], ""

    model_cls = model_factory or _load_sentence_transformer_class()
    if model_cls is None:
        return None, "local_embedding_model_not_available"

    if not allow_download:
        try:
            model = model_cls(model_name, device=device, local_files_only=True)
            return _cache_model(model_name, device, model), ""
        except TypeError:
            snapshot_path = _load_cached_huggingface_snapshot(model_name)
            if snapshot_path:
                try:
                    model = model_cls(snapshot_path, device=device)
                    return _cache_model(model_name, device, model), ""
                except Exception:
                    return None, "local_embedding_model_not_available"
        except Exception:
            pass
        return None, "local_embedding_model_not_available"

    try:
        model = model_cls(model_name, device=device)
        return _cache_model(model_name, device, model), ""
    except Exception:
        return None, "local_embedding_model_not_available"


def _resolve_backend(
    env: dict[str, Any],
    *,
    allow_local_model_download: bool,
    embedding_backend: EmbeddingBackend | None,
) -> tuple[EmbeddingBackend | None, str]:
    if embedding_backend is not None:
        return embedding_backend, ""
    if str(env.get("HERMES_RAG_EMBEDDING_BACKEND") or "").strip().lower() == "deterministic_hash_mock":
        return HashEmbeddingBackend(), ""
    model, failure_reason = load_local_embedding_model(
        str(env.get("HERMES_RAG_EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL),
        str(env.get("HERMES_RAG_EMBEDDING_DEVICE") or "cpu"),
        allow_local_model_download,
    )
    if model is None:
        return None, failure_reason or "local_embedding_model_not_available"
    return SentenceTransformersBackend(model), ""


def _chunked(values: list[Any], size: int) -> list[list[Any]]:
    return [values[index : index + size] for index in range(0, len(values), max(1, size))]


def _vector_dir_is_inside_keyword_index(vector_dir: Path, keyword_dir: Path) -> bool:
    try:
        vector_resolved = vector_dir.resolve()
        keyword_resolved = keyword_dir.resolve()
    except OSError:
        return False
    return vector_resolved == keyword_resolved or keyword_resolved in vector_resolved.parents


def build_rag_vector_index(
    *,
    allow_write: bool = False,
    allow_local_model_download: bool = False,
    env: dict[str, Any] | None = None,
    embedding_backend: EmbeddingBackend | None = None,
) -> dict[str, Any]:
    env_map = _env(env)
    config = _embedding_config(env_map)
    base = {
        **_base_safety("rag_vector_index_build"),
        **config,
        "allow_rag_vector_index_write": bool(allow_write),
        "allow_local_model_download": bool(allow_local_model_download),
        "blocked": False,
        "blocked_reason": "",
        "records_seen": 0,
        "vectors_reused": 0,
        "vectors_created": 0,
        "vectors_removed": 0,
        "records_skipped": 0,
        "incremental_build": True,
        "full_rebuild": False,
        "index_file_written": False,
    }
    if not allow_write:
        return {**base, "blocked": True, "blocked_reason": "allow_rag_vector_index_write_missing"}
    if not bool(config["embedding_enabled"]):
        return {**base, "blocked": True, "blocked_reason": "embedding_disabled"}
    records, failure_reason = _load_keyword_records(env_map)
    if failure_reason:
        return {**base, "blocked": True, "blocked_reason": failure_reason}
    backend, backend_failure = _resolve_backend(env_map, allow_local_model_download=allow_local_model_download, embedding_backend=embedding_backend)
    if backend is None:
        reason = "local_model_download_not_allowed" if backend_failure == "local_embedding_model_not_available" and not allow_local_model_download else backend_failure
        return {**base, "blocked": True, "blocked_reason": reason or "local_embedding_model_not_available"}
    vector_dir = _vector_index_dir(env_map)
    if _vector_dir_is_inside_keyword_index(vector_dir, _keyword_index_dir(env_map)):
        return {**base, "blocked": True, "blocked_reason": "vector_index_dir_inside_keyword_index_forbidden"}

    previous_manifest, previous_records, previous_vectors, _previous_failure = _load_vector_index(env_map)
    previous_by_key: dict[tuple[str, str, str, str], tuple[dict[str, Any], list[float]]] = {}
    for old_record, old_vector in zip(previous_records, previous_vectors):
        key = (
            str(old_record.get("source_id") or ""),
            str(old_record.get("chunk_id") or ""),
            str(old_record.get("content_hash") or ""),
            str(old_record.get("embedding_model") or ""),
        )
        previous_by_key[key] = (old_record, old_vector)

    vector_records: list[dict[str, Any]] = []
    vectors: list[list[float]] = []
    pending: list[tuple[dict[str, Any], str]] = []
    model_name = str(config["embedding_model"])
    for record in records:
        text = _record_text(record)
        if not text.strip():
            continue
        source_id = _source_id(record)
        is_image = str(record.get("extension") or "").lower() in IMAGE_EXTENSIONS or str(record.get("asset_type") or "") == "image_metadata"
        vector_record = {
            "source_id": source_id,
            "chunk_id": f"{'image' if is_image else 'doc'}#{int(record.get('chunk_index') or 0)}",
            "content_hash": str(record.get("content_hash") or hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()),
            "embedding_model": model_name,
            "embedding_model_version": DEFAULT_VECTOR_INDEX_VERSION,
            "source_label": str(record.get("source_label") or record.get("file_name") or "document")[:120],
            "relative_path": _safe_relative_path(record.get("relative_path") or record.get("file_name")),
            "asset_type": str(record.get("asset_type") or ("image_metadata" if is_image else "document_metadata")),
            "media_type": "image" if is_image else "document",
            "snippet": text[:240],
            "width": record.get("width") if is_image else None,
            "height": record.get("height") if is_image else None,
            "raw_nas_absolute_path_logged": False,
        }
        key = (source_id, vector_record["chunk_id"], vector_record["content_hash"], model_name)
        if key in previous_by_key:
            old_record, old_vector = previous_by_key[key]
            vector_records.append({**old_record, **vector_record})
            vectors.append(old_vector)
            continue
        vector_records.append(vector_record)
        pending.append((vector_record, text))

    batch_size = int(config["embedding_batch_size"])
    created_vectors: list[list[float]] = []
    for batch in _chunked([text for _record, text in pending], batch_size):
        created_vectors.extend(_normalize(vector) for vector in backend.encode_texts(batch))
    pending_iter = iter(created_vectors)
    final_vectors: list[list[float]] = []
    created_index = 0
    for record in vector_records:
        existing = None
        key = (record["source_id"], record["chunk_id"], record["content_hash"], model_name)
        if key in previous_by_key:
            existing = previous_by_key[key][1]
        if existing is not None:
            final_vectors.append(existing)
        else:
            final_vectors.append(next(pending_iter))
            created_index += 1

    dimension = len(final_vectors[0]) if final_vectors else DEFAULT_VECTOR_DIMENSION
    manifest = {
        "index_version": DEFAULT_VECTOR_INDEX_VERSION,
        "backend": str(config["embedding_backend"]),
        "model_name": model_name,
        "dimension": dimension,
        "record_count": len(vector_records),
        "normalized_vectors": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "raw_nas_path_stored": False,
        "external_embedding_api_called": False,
    }
    try:
        vector_dir.mkdir(parents=True, exist_ok=True)
        (vector_dir / VECTOR_MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (vector_dir / VECTORS_JSON_NAME).write_text(json.dumps(final_vectors, ensure_ascii=False), encoding="utf-8")
        with (vector_dir / VECTOR_RECORDS_NAME).open("w", encoding="utf-8") as handle:
            for record in vector_records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        return {**base, "blocked": True, "blocked_reason": "local_vector_index_write_failed"}

    report = {
        **base,
        "blocked": False,
        "blocked_reason": "",
        "records_seen": len(records),
        "vectors_reused": len(final_vectors) - created_index,
        "vectors_created": created_index,
        "vectors_removed": max(0, len(previous_records) - len(final_vectors)),
        "records_skipped": max(0, len(records) - len(vector_records)),
        "full_rebuild": not bool(previous_manifest),
        "vector_index_written_local_only": True,
        "local_embedding_model_used": True,
        "vector_index_created": True,
        "embedding_called": True,
        "index_file_written": True,
        "manifest": manifest,
    }
    try:
        (vector_dir / BUILD_REPORT_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    return report


def get_rag_vector_status(env: dict[str, Any] | None = None) -> dict[str, Any]:
    env_map = _env(env)
    manifest, records, _vectors, failure_reason = _load_vector_index(env_map)
    return {
        **_base_safety("rag_vector_status"),
        **_embedding_config(env_map),
        "vector_index_available": failure_reason == "",
        "vector_index_present": failure_reason == "",
        "vector_record_count": len(records) if failure_reason == "" else 0,
        "embedding_backend": manifest.get("backend") or _embedding_config(env_map)["embedding_backend"],
        "embedding_model": manifest.get("model_name") or _embedding_config(env_map)["embedding_model"],
        "dimension": manifest.get("dimension") if failure_reason == "" else None,
        "mode": "hybrid_available" if failure_reason == "" else "keyword_only_fallback",
        "blocked": failure_reason != "",
        "blocked_reason": failure_reason,
        "external_embedding_api_called": False,
        "raw_vector_logged": False,
        "raw_index_absolute_path_logged": False,
    }


def _weights(env: dict[str, Any]) -> tuple[float, float, float]:
    semantic = max(0.0, _float_env(env, "HERMES_RAG_HYBRID_SEMANTIC_WEIGHT", 0.65))
    keyword = max(0.0, _float_env(env, "HERMES_RAG_HYBRID_KEYWORD_WEIGHT", 0.25))
    metadata = max(0.0, _float_env(env, "HERMES_RAG_HYBRID_METADATA_WEIGHT", 0.10))
    total = semantic + keyword + metadata
    if total <= 0:
        return 0.65, 0.25, 0.10
    return semantic / total, keyword / total, metadata / total


def _keyword_score(record: dict[str, Any], query_terms: list[str]) -> float:
    haystack = " ".join(str(record.get(key) or "") for key in ("source_label", "relative_path", "asset_type", "snippet")).casefold()
    if not query_terms:
        return 0.0
    hits = sum(1 for term in query_terms if term in haystack)
    return min(1.0, hits / len(query_terms))


def _metadata_score(record: dict[str, Any], query_terms: list[str]) -> float:
    path = str(record.get("relative_path") or "").casefold()
    label = str(record.get("source_label") or "").casefold()
    score = 0.0
    for term in query_terms:
        if term in path:
            score += 0.7
        if term in label:
            score += 0.3
    return min(1.0, score)


def _manifest_compatibility_failure(manifest: dict[str, Any], env: dict[str, Any]) -> str:
    if not bool(manifest.get("normalized_vectors")):
        return "vector_manifest_incompatible"
    expected_backend = str(env.get("HERMES_RAG_EMBEDDING_BACKEND") or DEFAULT_EMBEDDING_BACKEND)
    manifest_backend = str(manifest.get("backend") or "")
    if manifest_backend and manifest_backend != expected_backend:
        return "vector_manifest_incompatible"
    expected_model = str(env.get("HERMES_RAG_EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL)
    if str(manifest.get("model_name") or "") != expected_model:
        return "embedding_model_mismatch"
    try:
        dimension = int(manifest.get("dimension") or 0)
    except (TypeError, ValueError):
        return "vector_manifest_incompatible"
    if dimension <= 0:
        return "vector_manifest_incompatible"
    return ""


def _result_from_vector_record(record: dict[str, Any], score: float, semantic_score: float, keyword_score: float, metadata_score: float) -> dict[str, Any]:
    return {
        "source_label": record.get("source_label"),
        "relative_path": record.get("relative_path"),
        "asset_type": record.get("asset_type"),
        "media_type": record.get("media_type"),
        "chunk_id": record.get("chunk_id"),
        "score": round(score, 3),
        "semantic_score": round(semantic_score, 3),
        "keyword_score": round(keyword_score, 3),
        "metadata_score": round(metadata_score, 3),
        "snippet": str(record.get("snippet") or "")[:240],
        "width": record.get("width"),
        "height": record.get("height"),
        "raw_nas_absolute_path_logged": False,
        "raw_vector_logged": False,
    }


def search_rag_hybrid(
    query: str,
    *,
    env: dict[str, Any] | None = None,
    mode: str = "hybrid",
    limit: int = 5,
    embedding_backend: EmbeddingBackend | None = None,
) -> dict[str, Any]:
    env_map = _env(env)
    query_text = str(query or "").strip()
    base = {
        **_base_safety("rag_hybrid_search"),
        "query_present": bool(query_text),
        "query_too_long": len(query_text) > MAX_QUERY_CHARS,
        "mode": mode,
        "keyword_fallback": False,
        "result_count": 0,
        "results": [],
        "limit": max(1, min(int(limit or 5), 10)),
    }
    if not query_text:
        return {**base, "blocked": True, "blocked_reason": "query_missing"}
    if len(query_text) > MAX_QUERY_CHARS:
        return {**base, "blocked": True, "blocked_reason": "query_too_long", "query": query_text[:MAX_QUERY_CHARS]}

    manifest, records, vectors, vector_failure = _load_vector_index(env_map)
    if vector_failure:
        keyword = search_rag_index(query_text, env=env_map, limit=limit)
        return {**base, **keyword, "report_type": "rag_hybrid_search", "mode": "keyword_only_fallback", "keyword_fallback": True, "fallback_reason": vector_failure}

    manifest_failure = _manifest_compatibility_failure(manifest, env_map)
    if manifest_failure:
        keyword = search_rag_index(query_text, env=env_map, limit=limit)
        return {
            **base,
            **keyword,
            "report_type": "rag_hybrid_search",
            "mode": "keyword_only_fallback",
            "keyword_fallback": True,
            "fallback_reason": manifest_failure,
            "vector_index_available": True,
            "vector_record_count": len(records),
            "record_count": len(records),
        }

    backend, backend_failure = _resolve_backend(env_map, allow_local_model_download=False, embedding_backend=embedding_backend)
    if backend is None:
        keyword = search_rag_index(query_text, env=env_map, limit=limit)
        return {
            **base,
            **keyword,
            "report_type": "rag_hybrid_search",
            "mode": "keyword_only_fallback",
            "keyword_fallback": True,
            "fallback_reason": backend_failure or "query_embedding_failed",
            "vector_index_available": True,
            "vector_record_count": len(records),
            "record_count": len(records),
        }
    try:
        query_vector = _normalize(backend.encode_texts([query_text])[0])
    except Exception:
        keyword = search_rag_index(query_text, env=env_map, limit=limit)
        return {
            **base,
            **keyword,
            "report_type": "rag_hybrid_search",
            "mode": "keyword_only_fallback",
            "keyword_fallback": True,
            "fallback_reason": "query_embedding_failed",
            "vector_index_available": True,
            "vector_record_count": len(records),
            "record_count": len(records),
        }

    try:
        manifest_dimension = int(manifest.get("dimension") or 0)
    except (TypeError, ValueError):
        manifest_dimension = 0
    if manifest_dimension != len(query_vector):
        keyword = search_rag_index(query_text, env=env_map, limit=limit)
        return {
            **base,
            **keyword,
            "report_type": "rag_hybrid_search",
            "mode": "keyword_only_fallback",
            "keyword_fallback": True,
            "fallback_reason": "embedding_dimension_mismatch",
            "vector_index_available": True,
            "vector_record_count": len(records),
            "record_count": len(records),
        }

    query_terms = [term.casefold() for term in query_text.split() if term.strip()]
    semantic_weight, keyword_weight, metadata_weight = _weights(env_map)
    scored: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for record, vector in zip(records, vectors):
        source_key = str(record.get("source_id") or record.get("relative_path") or record.get("source_label"))
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        semantic_score = max(0.0, _dot(query_vector, vector))
        keyword_score = _keyword_score(record, query_terms)
        metadata_score = _metadata_score(record, query_terms)
        if mode == "semantic":
            hybrid_score = semantic_score
        else:
            hybrid_score = semantic_score * semantic_weight + keyword_score * keyword_weight + metadata_score * metadata_weight
        scored.append(_result_from_vector_record(record, hybrid_score, semantic_score, keyword_score, metadata_score))
    scored.sort(key=lambda item: float(item.get("score") or 0), reverse=True)
    selected = scored[: int(base["limit"])]
    return {
        **base,
        "blocked": False,
        "blocked_reason": "",
        "query": query_text,
        "mode": "semantic" if mode == "semantic" else "hybrid",
        "result_count": len(selected),
        "results": selected,
        "vector_index_available": True,
        "vector_record_count": len(records),
        "record_count": len(records),
        "embedding_model": manifest.get("model_name"),
        "local_embedding_model_used": True,
        "embedding_called": True,
        "query_embedding_created": True,
        "query_embedding_dimension": len(query_vector),
        "fallback_reason": "",
        "external_embedding_api_called": False,
        "raw_vector_logged": False,
    }


def format_hybrid_results_for_discord(result: dict[str, Any]) -> str:
    if result.get("keyword_fallback"):
        fallback = format_rag_search_results_for_discord(result)
        return "[HERMES_STOXL]\nSemantic RAG index is not available.\nUsing keyword search fallback.\n\n" + fallback
    reason = str(result.get("blocked_reason") or "")
    if reason:
        return f"[HERMES_STOXL]\nRAG hybrid search failed.\nreason: {reason}"
    lines = [
        "[HERMES_STOXL] RAG Hybrid search results",
        "",
        f"query: {str(result.get('query') or '')[:120]}",
        f"mode: {result.get('mode')}",
        f"results: {int(result.get('result_count') or 0)}",
        "",
    ]
    for index, item in enumerate(list(result.get("results") or []), start=1):
        lines.extend(
            [
                f"{index}. {item.get('source_label')}",
                f"   path: {item.get('relative_path')}",
                f"   type: {item.get('asset_type')}",
                f"   score: {item.get('score')}",
                f"   semantic: {item.get('semantic_score')}",
                f"   keyword: {item.get('keyword_score')}",
                f"   chunk: {item.get('chunk_id')}",
            ]
        )
        if item.get("media_type") == "image" and item.get("width") and item.get("height"):
            lines.append(f"   size: {item.get('width')}x{item.get('height')}")
        lines.extend([f"   snippet: {item.get('snippet')}", ""])
    return "\n".join(lines).strip()


def format_vector_status_for_discord(env: dict[str, Any] | None = None) -> str:
    keyword = get_rag_index_status(env=env)
    vector = get_rag_vector_status(env=env)
    return (
        "[HERMES_STOXL] RAG status\n\n"
        f"keyword index: {'available' if keyword.get('index_available') else 'not available'}\n"
        f"keyword records: {int(keyword.get('record_count') or 0)}\n\n"
        f"vector index: {'available' if vector.get('vector_index_available') else 'not available'}\n"
        f"vector records: {int(vector.get('vector_record_count') or 0)}\n"
        f"embedding backend: {vector.get('embedding_backend')}\n"
        f"mode: {vector.get('mode')}\n\n"
        "nas write: false\n"
        "external embedding api: false\n"
        "llm: false\n"
        "vision: false\n"
        "ocr: false"
    )


def build_rag_vector_discord_command_response(command: str, query: str = "", *, env: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = str(command or "").strip().lower()
    try:
        if normalized == "rag-vector-status":
            status = get_rag_vector_status(env)
            return {
                **status,
                "response_type": "rag_discord_command_response",
                "reply_text_source": "rag_vector_status",
                "command": normalized,
                "content": format_vector_status_for_discord(env),
            }
        mode = "semantic" if normalized == "rag-semantic" else "hybrid"
        result = search_rag_hybrid(query, env=env, mode=mode, limit=5)
        return {
            **result,
            "response_type": "rag_discord_command_response",
            "reply_text_source": "rag_hybrid_search",
            "command": normalized,
            "content": format_hybrid_results_for_discord(result),
        }
    except Exception:
        return {
            **_base_safety("rag_hybrid_runtime_exception"),
            "response_type": "rag_discord_command_response",
            "reply_text_source": "rag_hybrid_runtime_exception",
            "command": normalized,
            "blocked": True,
            "blocked_reason": "rag_hybrid_runtime_exception",
            "content": "[HERMES_STOXL]\nRAG hybrid search failed.\nreason: rag_hybrid_runtime_exception",
        }
