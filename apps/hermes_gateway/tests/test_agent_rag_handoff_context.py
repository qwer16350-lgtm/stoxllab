from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_rag import build_handoff_rag_context, retrieve_agent_rag_context


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_results(_query: str, **_kwargs: object) -> dict[str, object]:
    return {"mode": "hybrid", "results": [{"source_label": "Grant", "relative_path": "research/grant.md", "media_type": "document", "chunk_id": "doc#1", "score": 0.8, "snippet": "grant checklist"}]}


def test_handoff_rag_context_is_bounded_metadata() -> None:
    context = retrieve_agent_rag_context(agent_name="kasumi", user_message="[RAG] 지원사업", env={"HERMES_AGENT_RAG_ENABLED": "true"}, search_fn=mock_results)
    handoff = build_handoff_rag_context(context)
    assert_true(handoff["result_count"] == 1, "result count")
    assert_true("sources" in handoff and "snippet" not in handoff["sources"][0], "metadata only")
    assert_true(handoff["raw_vector_logged"] is False, "no vector")


def main() -> int:
    test_handoff_rag_context_is_bounded_metadata()
    print("PASS test_handoff_rag_context_is_bounded_metadata")
    print("All agent RAG handoff context tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
