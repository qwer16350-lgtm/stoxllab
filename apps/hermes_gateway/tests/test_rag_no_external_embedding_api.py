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


def test_vector_build_and_search_never_call_external_embedding_api() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        Path(index_dir, "nas_rag_index.json").write_text(
            json.dumps({"records": [{"source_label": "Doc", "relative_path": "doc.md", "file_name": "doc.md", "content_preview": "brand text"}]}),
            encoding="utf-8",
        )
        env = {"HERMES_RAG_INDEX_DIR": index_dir, "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir, "HERMES_RAG_EMBEDDING_ENABLED": "true", "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock"}
        build = build_rag_vector_index(allow_write=True, env=env)
        search = search_rag_hybrid("brand", env=env)
    assert_true(build["external_embedding_api_called"] is False, "build no external embedding")
    assert_true(search["external_embedding_api_called"] is False, "search no external embedding")
    assert_true(build["web_search_called"] is False and search["web_search_called"] is False, "no web")
    assert_true(build["llm_called"] is False and search["llm_called"] is False, "no LLM")
    assert_true(build["external_execution"] is False and search["external_execution"] is False, "no external execution")


def main() -> int:
    test_vector_build_and_search_never_call_external_embedding_api()
    print("PASS test_vector_build_and_search_never_call_external_embedding_api")
    print("All RAG no external embedding API tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
