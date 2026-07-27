from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result
from company_rag_vector_index import build_rag_vector_index


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_handoff_citation_provenance_is_bounded_metadata() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        Path(index_dir, "nas_rag_index.json").write_text(json.dumps({"records": [{"source_label": "Grant", "relative_path": "research/grant.md", "file_name": "grant.md", "content_hash": "h", "content_preview": "지원사업 자료"}]}), encoding="utf-8")
        env = {"HERMES_RAG_INDEX_DIR": index_dir, "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir, "HERMES_RAG_EMBEDDING_ENABLED": "true", "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock", "HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_RAG_MIN_SCORE": "0"}
        build_rag_vector_index(allow_write=True, env=env)
        result = build_company_agent_message_result("operation-brief", "!kasumi [RAG] 지원사업 자료", env=env)
    provenance = result.get("handoff_citation_provenance") or []
    assert_true(len(provenance) >= 1, "provenance")
    assert_true("snippet" not in provenance[0], "no full text")
    assert_true(provenance[0]["source_id"] == "S1", "invocation source id")


def main() -> int:
    test_handoff_citation_provenance_is_bounded_metadata()
    print("PASS test_handoff_citation_provenance_is_bounded_metadata")
    print("All citation handoff provenance tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
