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


def test_agent_scope_normalization() -> None:
    env = {"HERMES_AGENT_RAG_ENABLED": "true"}
    assert_true(should_use_agent_rag(agent_name="MARIN_STOXL", user_message="[RAG] 브랜드", env=env).scope == "marin", "marin scope")
    assert_true(should_use_agent_rag(agent_name="unknown", user_message="[RAG] 프로젝트", env=env).scope == "hermes", "unknown defaults hermes")


def main() -> int:
    test_agent_scope_normalization()
    print("PASS test_agent_scope_normalization")
    print("All agent RAG agent scope tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
