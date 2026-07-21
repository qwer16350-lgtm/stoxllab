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


def test_explicit_disable_wins_over_auto_terms() -> None:
    env = {"HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_RAG_AUTO_ENABLED": "true"}
    decision = should_use_agent_rag(agent_name="lucy", user_message="[RAG OFF] 기존 회사소개 자료 말고 이 문장만 다듬어줘", env=env)
    assert_true(decision.use_rag is False, "disabled")
    assert_true(decision.reason == "explicit_rag_off", "off reason")
    assert_true(decision.disabled_by_user is True, "user disabled")


def main() -> int:
    test_explicit_disable_wins_over_auto_terms()
    print("PASS test_explicit_disable_wins_over_auto_terms")
    print("All agent RAG explicit disable tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
