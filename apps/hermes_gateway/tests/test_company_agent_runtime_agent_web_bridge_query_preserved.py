from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import company_agent_runtime
from company_agent_runtime import (
    build_agent_web_bridge_execution_result_from_decision,
    detect_agent_web_bridge_decision,
)


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
    "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
    "HERMES_COMPANY_AGENT_LLM_MODE": "off",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_kasumi_query_agent_and_scope_are_preserved() -> None:
    decision = detect_agent_web_bridge_decision(
        "operation-brief",
        "!kasumi 이번 달 한국 중소기업 디자인 개발 지원사업 후보 찾아줘",
        WEB_ENV,
    )
    assert_true(decision.selected is True, "bridge selected")
    assert_true(decision.selected_agent == "kasumi", "agent preserved")
    assert_true(decision.agent_scope == "research_discovery", "scope preserved")
    assert_true(decision.query == "이번 달 한국 중소기업 디자인 개발 지원사업 후보 찾아줘", "query preserved")
    assert_true("!kasumi" not in decision.query, "prefix removed")


def test_agent_command_query_is_preserved() -> None:
    decision = detect_agent_web_bridge_decision(
        "operation-brief",
        "!agent kasumi 이번 달 지원사업 후보 찾아줘",
        WEB_ENV,
    )
    assert_true(decision.selected is True, "agent command bridge selected")
    assert_true(decision.selected_agent == "kasumi", "generic agent preserved")
    assert_true(decision.query == "이번 달 지원사업 후보 찾아줘", "generic query preserved")


def test_execution_pipeline_receives_preserved_query() -> None:
    captured: dict[str, Any] = {}
    original = company_agent_runtime.build_company_agent_web_reference_one_shot

    def fake_one_shot(agent_id: str, message: str, **kwargs: Any) -> dict[str, Any]:
        captured["agent_id"] = agent_id
        captured["message"] = message
        captured["allow_web_reference"] = kwargs.get("allow_web_reference")
        return {
            "web_search_attempted": True,
            "web_search_succeeded": False,
            "failure_reason": "web_reference_provider_exception",
            "agent_scope": "research_discovery",
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "llm_api_called": False,
            "rag_called": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }

    company_agent_runtime.build_company_agent_web_reference_one_shot = fake_one_shot
    try:
        decision = detect_agent_web_bridge_decision(
            "operation-brief",
            "!kasumi 이번 달 한국 중소기업 디자인 개발 지원사업 후보 찾아줘",
            WEB_ENV,
        )
        result = build_agent_web_bridge_execution_result_from_decision(decision, env=WEB_ENV)
    finally:
        company_agent_runtime.build_company_agent_web_reference_one_shot = original

    assert_true(captured["agent_id"] == "kasumi", "pipeline agent")
    assert_true(captured["message"] == "이번 달 한국 중소기업 디자인 개발 지원사업 후보 찾아줘", "pipeline query")
    assert_true(captured["allow_web_reference"] is True, "pipeline web allowed")
    assert_true(result["agent_scope"] == "research_discovery", "result scope")
    assert_true(result["response"]["reply_text_source"] == "web_reference_bridge_failure", "bounded fallback")
    assert_true(result["response"]["llm_api_called"] is False, "no LLM")
    assert_true(result["response"]["rag_called"] is False, "no RAG")
    assert_true(result["response"]["external_execution"] is False, "no external")


def main() -> int:
    test_kasumi_query_agent_and_scope_are_preserved()
    print("PASS test_kasumi_query_agent_and_scope_are_preserved")
    test_agent_command_query_is_preserved()
    print("PASS test_agent_command_query_is_preserved")
    test_execution_pipeline_receives_preserved_query()
    print("PASS test_execution_pipeline_receives_preserved_query")
    print("All company agent runtime web bridge query preservation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
