from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_agent_web_bridge_decision_trace, build_company_agent_message_result


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
    "HERMES_COMPANY_AGENT_LLM_ENABLED": "true",
    "HERMES_COMPANY_AGENT_LLM_MODE": "manual_command_only",
    "HERMES_COMPANY_AGENT_REPLY_MODE": "llm_with_deterministic_fallback",
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
                "title": f"{agent_id} official reference",
                "url": "https://www.bizinfo.go.kr/web/reference",
                "snippet": "공식 출처 우선 mock 결과",
                "institution": "Mock Official",
            }
        ],
    }


def test_agent_command_web_bridge_selected_before_llm_path() -> None:
    message = "!kasumi 이번 달 지원사업 후보 찾아줘"
    trace = build_agent_web_bridge_decision_trace("operation-brief", message, WEB_ENV)
    result = build_company_agent_message_result("operation-brief", message, env=WEB_ENV, web_search_runner=mock_search)

    assert_true(trace["agent_command_detected"] is True, "agent command detected")
    assert_true(trace["selected_agent"] == "kasumi", "Kasumi selected")
    assert_true(trace["web_intent_detected"] is True, "web intent detected")
    assert_true(trace["web_reference_enabled"] is True, "web enabled")
    assert_true(trace["agent_web_bridge_selected"] is True, "bridge selected")
    assert_true(result["agent_web_bridge_selected"] is True, "result bridge selected")
    assert_true(result["normal_agent_path_skipped_for_web_bridge"] is True, "normal path skipped")
    assert_true(result["llm_path_skipped_for_web_bridge"] is True, "LLM path skipped")
    assert_true(result["response"]["reply_text_source"] == "web_reference", "web response source")
    assert_true(result["response"]["llm_api_call_attempted"] is False, "no LLM attempted")
    assert_true(result["response"]["rag_called"] is False, "no RAG")
    assert_true(result["response"]["external_execution"] is False, "no external")
    assert_true(result["discord_message_sent"] is False, "no Discord send in test")


def test_kasumi_ping_does_not_select_agent_web_bridge() -> None:
    calls = {"count": 0}

    def should_not_search(agent_id: str, queries: list[str], limit: int) -> dict:
        calls["count"] += 1
        return mock_search(agent_id, queries, limit)

    trace = build_agent_web_bridge_decision_trace("operation-brief", "!kasumi ping", WEB_ENV)
    result = build_company_agent_message_result("operation-brief", "!kasumi ping", env=WEB_ENV, web_search_runner=should_not_search)
    assert_true(trace["agent_command_detected"] is True, "agent command detected")
    assert_true(trace["web_intent_detected"] is False, "no web intent")
    assert_true(trace["agent_web_bridge_selected"] is False, "no bridge")
    assert_true(result["agent_web_bridge_selected"] is False, "result no bridge")
    assert_true(result["web_reference_bridge_attempted"] is False, "web not attempted")
    assert_true(calls["count"] == 0, "search not called")


def test_web_command_path_is_preserved() -> None:
    result = build_company_agent_message_result(
        "operation-brief",
        "!web 이번 달 지원사업 후보 찾아줘",
        env=WEB_ENV,
        web_search_runner=mock_search,
    )
    assert_true(result["command"] == "web", "web command preserved")
    assert_true(result["web_reference_bridge_attempted"] is True, "web path attempted")
    assert_true(result["agent_command_web_bridge"] is False, "not agent bridge")
    assert_true(result["agent_web_bridge_selected"] is False, "not agent bridge selected")
    assert_true(result["web_reference_succeeded"] is True, "web succeeded")


def main() -> int:
    test_agent_command_web_bridge_selected_before_llm_path()
    print("PASS test_agent_command_web_bridge_selected_before_llm_path")
    test_kasumi_ping_does_not_select_agent_web_bridge()
    print("PASS test_kasumi_ping_does_not_select_agent_web_bridge")
    test_web_command_path_is_preserved()
    print("PASS test_web_command_path_is_preserved")
    print("All company agent runtime web bridge wiring tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
