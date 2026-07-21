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


def failing_search(_query: str, **_kwargs: object) -> dict[str, object]:
    raise RuntimeError("hidden internal failure")


def test_rag_runtime_exception_falls_back_without_raw_error() -> None:
    context = retrieve_agent_rag_context(agent_name="kasumi", user_message="[RAG] 지원사업", env={"HERMES_AGENT_RAG_ENABLED": "true"}, search_fn=failing_search)
    assert_true(context.rag_used is False, "not used")
    assert_true(context.agent_rag_fallback is True, "fallback")
    assert_true(context.fallback_reason == "rag_runtime_exception", "safe reason")
    assert_true("hidden" not in context.prompt_context, "raw exception hidden")


def main() -> int:
    test_rag_runtime_exception_falls_back_without_raw_error()
    print("PASS test_rag_runtime_exception_falls_back_without_raw_error")
    print("All agent RAG runtime exception fallback tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
