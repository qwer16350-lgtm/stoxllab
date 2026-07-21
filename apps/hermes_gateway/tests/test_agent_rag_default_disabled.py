from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_rag import retrieve_agent_rag_context, should_use_agent_rag


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_agent_rag_disabled_by_default() -> None:
    decision = should_use_agent_rag(agent_name="marin", user_message="[내부자료] 기존 브랜드 자료 참고해줘", env={})
    context = retrieve_agent_rag_context(agent_name="marin", user_message="[내부자료] 기존 브랜드 자료 참고해줘", env={})
    assert_true(decision.use_rag is False, "default disabled")
    assert_true(decision.reason == "agent_rag_disabled", "disabled reason")
    assert_true(context.rag_used is False, "no context")


def main() -> int:
    test_agent_rag_disabled_by_default()
    print("PASS test_agent_rag_disabled_by_default")
    print("All agent RAG default disabled tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
