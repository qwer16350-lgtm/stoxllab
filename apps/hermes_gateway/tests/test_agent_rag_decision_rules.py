from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_rag import should_use_agent_rag


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_internal_document_question_enables_auto_rag() -> None:
    env = {"HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_RAG_AUTO_ENABLED": "true"}
    decision = should_use_agent_rag(agent_name="hermes", user_message="기존 홈페이지 프로젝트 결정사항 정리해줘", env=env)
    assert_true(decision.use_rag is True, "auto RAG")
    assert_true(decision.reason == "internal_project_context_required", "project reason")


def test_simple_ping_does_not_use_rag() -> None:
    env = {"HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_RAG_AUTO_ENABLED": "true"}
    decision = should_use_agent_rag(agent_name="hermes", user_message="ping", env=env)
    assert_true(decision.use_rag is False, "no RAG")
    assert_true(decision.reason == "simple_message_no_internal_context", "simple reason")


def main() -> int:
    test_internal_document_question_enables_auto_rag()
    print("PASS test_internal_document_question_enables_auto_rag")
    test_simple_ping_does_not_use_rag()
    print("PASS test_simple_ping_does_not_use_rag")
    print("All agent RAG decision rule tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
