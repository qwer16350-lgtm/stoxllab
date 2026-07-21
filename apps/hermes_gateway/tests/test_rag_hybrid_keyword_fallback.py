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


class FailingBackend:
    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("hidden failure")


def write_keyword_index(index_dir: str) -> None:
    Path(index_dir, "nas_rag_index.json").write_text(
        json.dumps({"records": [{"source_label": "Brand", "relative_path": "brand.md", "file_name": "brand.md", "content_preview": "brand guide"}]}),
        encoding="utf-8",
    )


def test_missing_vector_index_uses_keyword_fallback() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        write_keyword_index(index_dir)
        result = search_rag_hybrid("brand", env={"HERMES_RAG_INDEX_DIR": index_dir, "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir})
    assert_true(result["keyword_fallback"] is True, "keyword fallback")
    assert_true(result["fallback_reason"] == "vector_index_missing", "missing vector reason")
    assert_true(result["result_count"] == 1, "keyword result")


def test_query_embedding_failure_uses_keyword_fallback() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        write_keyword_index(index_dir)
        env = {"HERMES_RAG_INDEX_DIR": index_dir, "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir, "HERMES_RAG_EMBEDDING_ENABLED": "true", "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock"}
        build_rag_vector_index(allow_write=True, env=env)
        result = search_rag_hybrid("brand", env=env, embedding_backend=FailingBackend())
    assert_true(result["keyword_fallback"] is True, "keyword fallback")
    assert_true(result["fallback_reason"] == "query_embedding_failed", "query embedding failed")
    assert_true("hidden failure" not in json.dumps(result), "raw exception hidden")


def main() -> int:
    test_missing_vector_index_uses_keyword_fallback()
    print("PASS test_missing_vector_index_uses_keyword_fallback")
    test_query_embedding_failure_uses_keyword_fallback()
    print("PASS test_query_embedding_failure_uses_keyword_fallback")
    print("All RAG hybrid keyword fallback tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
