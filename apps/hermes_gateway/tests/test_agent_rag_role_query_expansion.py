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


def test_all_agent_query_expansions_include_role_terms() -> None:
    env = {"HERMES_AGENT_RAG_ENABLED": "true"}
    expected = {
        "hermes": "프로젝트",
        "kasumi": "지원사업",
        "meiko": "계약",
        "marin": "브랜드",
        "lucy": "홈페이지",
        "reze": "전략",
    }
    for agent, term in expected.items():
        decision = should_use_agent_rag(agent_name=agent, user_message="[내부자료] 기존 자료 정리", env=env)
        assert_true(decision.use_rag is True, f"{agent} forced")
        assert_true(term.casefold() in decision.query.casefold(), f"{agent} expansion")


def main() -> int:
    test_all_agent_query_expansions_include_role_terms()
    print("PASS test_all_agent_query_expansions_include_role_terms")
    print("All agent RAG role query expansion tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
