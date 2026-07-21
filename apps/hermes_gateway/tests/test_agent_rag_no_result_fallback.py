from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_rag import retrieve_agent_rag_context
from company_agent_runtime import build_company_agent_message_result


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_empty(_query: str, **_kwargs: object) -> dict[str, object]:
    return {"mode": "hybrid", "results": []}


def test_no_result_context_falls_back_without_blocking_response() -> None:
    context = retrieve_agent_rag_context(agent_name="marin", user_message="[RAG] 없는 자료", env={"HERMES_AGENT_RAG_ENABLED": "true"}, search_fn=mock_empty)
    result = build_company_agent_message_result("marketing-brief", "!marin [RAG OFF] 없는 자료", env={"HERMES_AGENT_RAG_ENABLED": "true"})
    assert_true(context.rag_used is False, "no context")
    assert_true(context.agent_rag_fallback is True, "fallback")
    assert_true(context.fallback_reason == "rag_no_results", "no result reason")
    assert_true(result["reply_prepared"] is True, "response continued")


def main() -> int:
    test_no_result_context_falls_back_without_blocking_response()
    print("PASS test_no_result_context_falls_back_without_blocking_response")
    print("All agent RAG no-result fallback tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
