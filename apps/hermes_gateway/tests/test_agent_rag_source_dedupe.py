from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_rag import retrieve_agent_rag_context


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_same_source(_query: str, **_kwargs: object) -> dict[str, object]:
    return {
        "mode": "hybrid",
        "results": [
            {"source_label": "Brand", "relative_path": "brand.md", "media_type": "document", "chunk_id": f"doc#{i}", "score": 0.9 - i * 0.01, "snippet": f"chunk {i}"}
            for i in range(5)
        ],
    }


def test_same_source_chunk_limit() -> None:
    env = {"HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_RAG_MAX_CHUNKS_PER_SOURCE": "2", "HERMES_AGENT_RAG_MAX_RESULTS": "5"}
    context = retrieve_agent_rag_context(agent_name="marin", user_message="[RAG] 브랜드", env=env, search_fn=mock_same_source)
    assert_true(context.result_count == 2, "same source chunk limit")


def main() -> int:
    test_same_source_chunk_limit()
    print("PASS test_same_source_chunk_limit")
    print("All agent RAG source dedupe tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
