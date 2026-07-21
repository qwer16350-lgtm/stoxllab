from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_vector_index import build_rag_vector_index, search_rag_hybrid


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_keyword_index(index_dir: str) -> None:
    Path(index_dir, "nas_rag_index.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_label": "Brand",
                        "relative_path": "brand.md",
                        "file_name": "brand.md",
                        "content_hash": "brand",
                        "content_preview": "brand direction",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_manifest_model_mismatch_uses_clear_fallback_reason() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        _write_keyword_index(index_dir)
        env = {
            "HERMES_RAG_INDEX_DIR": index_dir,
            "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
            "HERMES_RAG_EMBEDDING_ENABLED": "true",
            "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock",
        }
        build_rag_vector_index(allow_write=True, env=env)
        result = search_rag_hybrid("brand", env={**env, "HERMES_RAG_EMBEDDING_MODEL": "different-local-model"})
    assert_true(result["keyword_fallback"] is True, "keyword fallback")
    assert_true(result["fallback_reason"] == "embedding_model_mismatch", "model mismatch reason")


def test_manifest_dimension_mismatch_uses_clear_fallback_reason() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        _write_keyword_index(index_dir)
        env = {
            "HERMES_RAG_INDEX_DIR": index_dir,
            "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
            "HERMES_RAG_EMBEDDING_ENABLED": "true",
            "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock",
        }
        build_rag_vector_index(allow_write=True, env=env)
        manifest_path = Path(vector_dir, "vector_manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["dimension"] = 12
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result = search_rag_hybrid("brand", env=env)
    assert_true(result["keyword_fallback"] is True, "keyword fallback")
    assert_true(result["fallback_reason"] == "embedding_dimension_mismatch", "dimension mismatch reason")


def test_hybrid_query_reports_query_embedding_dimension() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        _write_keyword_index(index_dir)
        env = {
            "HERMES_RAG_INDEX_DIR": index_dir,
            "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
            "HERMES_RAG_EMBEDDING_ENABLED": "true",
            "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock",
        }
        build_rag_vector_index(allow_write=True, env=env)
        result = search_rag_hybrid("brand", env=env)
    assert_true(result["mode"] == "hybrid", "hybrid query")
    assert_true(result["query_embedding_created"] is True, "query embedding")
    assert_true(result["query_embedding_dimension"] == 384, "query embedding dimension")


def main() -> int:
    test_manifest_model_mismatch_uses_clear_fallback_reason()
    print("PASS test_manifest_model_mismatch_uses_clear_fallback_reason")
    test_manifest_dimension_mismatch_uses_clear_fallback_reason()
    print("PASS test_manifest_dimension_mismatch_uses_clear_fallback_reason")
    test_hybrid_query_reports_query_embedding_dimension()
    print("PASS test_hybrid_query_reports_query_embedding_dimension")
    print("All RAG vector manifest compatibility tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
