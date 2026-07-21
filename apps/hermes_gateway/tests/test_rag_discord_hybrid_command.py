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


def prepare_indexes(index_dir: str, vector_dir: str) -> dict[str, str]:
    Path(index_dir, "nas_rag_index.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_label": "Brand Direction",
                        "relative_path": "01_BRAND/brand.md",
                        "file_name": "brand.md",
                        "content_hash": "brand",
                        "asset_type": "document_metadata",
                        "media_type": "document",
                        "content_preview": "brand industrial future",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    env = {
        "HERMES_RAG_INDEX_DIR": index_dir,
        "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
        "HERMES_RAG_EMBEDDING_ENABLED": "true",
        "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock",
    }
    build_rag_vector_index(allow_write=True, env=env)
    return env


def test_discord_rag_hybrid_and_vector_status_commands() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        env = prepare_indexes(index_dir, vector_dir)
        status = build_company_agent_message_result("operation-brief", "!rag-vector-status", env=env)
        hybrid = build_company_agent_message_result("operation-brief", "!rag-hybrid brand", env=env)
        docs = build_company_agent_message_result("operation-brief", "!docs brand", env=env)
    assert_true(status["selected_agent"] == "hermes", "Hermes status")
    assert_true("vector index: available" in status["response"]["content"], "vector status available")
    assert_true(hybrid["response"]["reply_text_source"] == "rag_hybrid_search", "hybrid source")
    assert_true("RAG Hybrid search results" in hybrid["response"]["content"], "hybrid content")
    assert_true(hybrid["outbound_guard_applied"] is True, "outbound guard")
    assert_true(hybrid["index_write_attempted_from_runtime"] is False, "runtime does not build index")
    assert_true(hybrid["llm_called"] is False, "no LLM")
    assert_true(hybrid["external_embedding_api_called"] is False, "no external embedding")
    assert_true(docs["response"]["reply_text_source"] == "rag_hybrid_search", "docs uses hybrid when vector exists")
    assert_true(docs["response"].get("keyword_fallback") is False, "docs no fallback when vector exists")


def main() -> int:
    test_discord_rag_hybrid_and_vector_status_commands()
    print("PASS test_discord_rag_hybrid_and_vector_status_commands")
    print("All RAG Discord hybrid command tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
