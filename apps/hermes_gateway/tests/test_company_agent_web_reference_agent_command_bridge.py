from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result
from company_persistent_memory import load_recent_records
from company_web_reference import detect_agent_command_web_intent


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


def mock_search(_agent_id: str, _queries: list[str], _limit: int) -> dict:
    return {
        "search_succeeded": True,
        "failure_reason": "",
        "provider": "mock",
        "results": [
            {
                "title": "2026 디자인개발 지원사업 모집 공고",
                "url": "https://govhelpers.com/reference/1",
                "snippet": "신청기간 2026.05.06 ~ 2026.06.25 지원대상 중소기업 지원내용 디자인개발",
                "institution": "Mock Reference",
            }
        ],
    }


def test_kasumi_agent_command_web_intent_bridges_to_web_reference() -> None:
    with tempfile.TemporaryDirectory() as memory_dir:
        os.environ["HERMES_COMPANY_MEMORY_DIR"] = memory_dir
        message = "!kasumi 이번 달 전국 중소기업 디자인개발 지원사업 후보 찾아줘"
        assert_true(detect_agent_command_web_intent("kasumi", message, {"command": "kasumi"}), "bridge intent")
        result = build_company_agent_message_result("operation-brief", message, env=WEB_ENV, web_search_runner=mock_search)
        recent = load_recent_records("recent_item", 5, memory_dir)
    assert_true(result["selected_agent"] == "kasumi", "Kasumi selected")
    assert_true(result["agent_command_web_bridge"] is True, "agent command bridge")
    assert_true(result["web_reference_bridge_attempted"] is True, "bridge attempted")
    assert_true(result["web_reference_attempted"] is True, "web attempted")
    assert_true(result["web_reference_succeeded"] is True, "web succeeded")
    assert_true(result["agent_scope"] == "research_discovery", "Kasumi scope")
    assert_true(result["outbound_guard_applied"] is True, "outbound guard")
    assert_true(any(record.get("item_type") == "web_reference" for record in recent), "memory written")
    assert_true(result["discord_message_sent"] is False, "no Discord in test")
    assert_true(result["response"]["llm_api_called"] is False, "no LLM")
    assert_true(result["response"]["rag_called"] is False, "no RAG")
    assert_true(result["response"]["external_execution"] is False, "no external")


def test_kasumi_ping_does_not_bridge_to_web_reference() -> None:
    calls = {"count": 0}

    def should_not_run(_agent_id: str, _queries: list[str], _limit: int) -> dict:
        calls["count"] += 1
        return mock_search(_agent_id, _queries, _limit)

    result = build_company_agent_message_result("operation-brief", "!kasumi ping", env=WEB_ENV, web_search_runner=should_not_run)
    assert_true(result["selected_agent"] == "kasumi", "Kasumi selected")
    assert_true(result["web_reference_bridge_attempted"] is False, "no bridge")
    assert_true(result["web_reference_attempted"] is False, "no web")
    assert_true(calls["count"] == 0, "search not called")
    assert_true(result["response"]["reply_text_source"] != "web_reference_bridge_failure", "normal response")


def test_existing_web_command_still_works() -> None:
    result = build_company_agent_message_result(
        "operation-brief",
        "!web 이번 달 전국 중소기업 디자인개발 지원사업 후보 찾아줘",
        env=WEB_ENV,
        web_search_runner=mock_search,
    )
    assert_true(result["command"] == "web", "web command preserved")
    assert_true(result["web_reference_bridge_attempted"] is True, "web path attempted")
    assert_true(result["agent_command_web_bridge"] is False, "not agent bridge")
    assert_true(result["web_reference_succeeded"] is True, "web succeeded")


def main() -> int:
    for test in (
        test_kasumi_agent_command_web_intent_bridges_to_web_reference,
        test_kasumi_ping_does_not_bridge_to_web_reference,
        test_existing_web_command_still_works,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All company agent web reference command bridge tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
