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


def mock_keyword_fallback(_query: str, **_kwargs: object) -> dict[str, object]:
    return {
        "mode": "keyword_only_fallback",
        "keyword_fallback": True,
        "fallback_reason": "vector_index_missing",
        "results": [{"source_label": "Ops", "relative_path": "ops/checklist.md", "media_type": "document", "chunk_id": "doc#1", "score": 0.7, "snippet": "checklist"}],
    }


def test_vector_unavailable_uses_keyword_fallback_context() -> None:
    context = retrieve_agent_rag_context(agent_name="meiko", user_message="[RAG] 체크리스트", env={"HERMES_AGENT_RAG_ENABLED": "true"}, search_fn=mock_keyword_fallback)
    assert_true(context.rag_used is True, "context still used")
    assert_true(context.keyword_fallback is True, "keyword fallback")
    assert_true(context.fallback_reason == "vector_index_missing", "fallback reason")


def main() -> int:
    test_vector_unavailable_uses_keyword_fallback_context()
    print("PASS test_vector_unavailable_uses_keyword_fallback_context")
    print("All agent RAG keyword fallback tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
