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


def mock_hybrid(query: str, **kwargs: object) -> dict[str, object]:
    assert_true(kwargs.get("mode") == "hybrid", "hybrid mode")
    return {
        "mode": "hybrid",
        "keyword_fallback": False,
        "results": [{"source_label": "Design", "relative_path": "brand/design.md", "media_type": "document", "chunk_id": "doc#1", "score": 0.88, "snippet": f"reference for {query[:20]}"}],
    }


def test_hybrid_index_path_uses_hybrid_retrieval() -> None:
    env = {"HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_RAG_MODE": "hybrid"}
    context = retrieve_agent_rag_context(agent_name="marin", user_message="[RAG] 전시 공간", env=env, search_fn=mock_hybrid)
    assert_true(context.rag_used is True, "used")
    assert_true(context.mode == "hybrid", "hybrid")
    assert_true(context.keyword_fallback is False, "not fallback")


def main() -> int:
    test_hybrid_index_path_uses_hybrid_retrieval()
    print("PASS test_hybrid_index_path_uses_hybrid_retrieval")
    print("All agent RAG hybrid retrieval tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
