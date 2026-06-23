from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
    "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
    "HERMES_COMPANY_AGENT_LLM_MODE": "off",
    "HERMES_COMPANY_AGENT_REPLY_MODE": "deterministic_fallback",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_search(agent_id: str, _queries: list[str], _limit: int) -> dict:
    return {
        "search_succeeded": True,
        "failure_reason": "",
        "provider": "mock",
        "results": [
            {
                "title": f"{agent_id} web reference",
                "url": "https://example.org/reference",
                "snippet": "최신 확인용 mock reference",
                "institution": "Example",
            }
        ],
    }


def test_agent_command_scope_bridge_for_all_agents() -> None:
    cases = {
        "kasumi": ("operation-brief", "!kasumi 지원사업 후보 찾아줘", "research_discovery"),
        "meiko": ("meiko-검토", "!meiko 지원사업 실제 신청 가능성 검증해줘", "operational_verification"),
        "lucy": ("lucy-검토", "!lucy 최신 표현 리스크 확인해줘", "publication_review"),
        "marin": ("marketing-brief", "!marin 인스타 레퍼런스 찾아줘", "content_reference"),
        "reze": ("reze-전략기획", "!reze 시장 트렌드 찾아줘", "strategy_market_reference"),
    }
    for agent, (channel, message, scope) in cases.items():
        result = build_company_agent_message_result(channel, message, env=WEB_ENV, web_search_runner=mock_search)
        assert_true(result["selected_agent"] == agent, f"{agent} selected")
        assert_true(result["agent_command_web_bridge"] is True, f"{agent} bridge")
        assert_true(result["web_reference_attempted"] is True, f"{agent} attempted")
        assert_true(result["web_reference_succeeded"] is True, f"{agent} succeeded")
        assert_true(result["agent_scope"] == scope, f"{agent} scope")
        assert_true(result["outbound_guard_applied"] is True, f"{agent} guard")
        assert_true(result["discord_message_sent"] is False, f"{agent} no Discord")


def main() -> int:
    test_agent_command_scope_bridge_for_all_agents()
    print("PASS test_agent_command_scope_bridge_for_all_agents")
    print("All company agent web reference scope bridge tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
