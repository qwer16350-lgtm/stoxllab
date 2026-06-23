from __future__ import annotations

import inspect
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import company_agent_runtime
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
                "title": f"{agent_id} scoped reference",
                "url": "https://www.bizinfo.go.kr/web/reference",
                "snippet": "scope mock",
                "institution": "Mock Official",
            }
        ],
    }


def raising_search(_agent_id: str, _queries: list[str], _limit: int) -> dict:
    raise RuntimeError("provider exception with hidden detail")


def test_runtime_on_message_calls_ack_before_replied_message_fetch() -> None:
    source = inspect.getsource(company_agent_runtime._run_discord_client)
    ack_index = source.index("_maybe_send_agent_web_bridge_ack")
    replied_index = source.index("_referenced_message_content")
    result_index = source.index("build_company_agent_message_result")
    assert_true(ack_index < replied_index < result_index, "ACK precedes replied fetch and result build")


def test_agent_scope_bridge_for_all_explicit_agents() -> None:
    cases = {
        "kasumi": ("operation-brief", "!kasumi 지원사업 후보 찾아줘", "research_discovery"),
        "meiko": ("meiko-검토", "!meiko 지원사업 실제 신청 가능성 검증해줘", "operational_verification"),
        "lucy": ("lucy-검토", "!lucy 최신 표현 리스크 확인해줘", "publication_review"),
        "marin": ("marketing-brief", "!marin 인스타 레퍼런스 찾아줘", "content_reference"),
        "reze": ("reze-전략기획", "!reze 시장 트렌드 찾아줘", "strategy_market_reference"),
    }
    for agent, (channel, message, scope) in cases.items():
        trace = build_agent_web_bridge_decision_trace(channel, message, WEB_ENV)
        result = build_company_agent_message_result(channel, message, env=WEB_ENV, web_search_runner=mock_search)
        assert_true(trace["agent_web_bridge_selected"] is True, f"{agent} trace bridge")
        assert_true(result["selected_agent"] == agent, f"{agent} selected")
        assert_true(result["agent_web_bridge_selected"] is True, f"{agent} result bridge")
        assert_true(result["agent_scope"] == scope, f"{agent} scope")
        assert_true(result["response"]["reply_text_source"] == "web_reference", f"{agent} web response")
        assert_true(result["response"]["llm_api_call_attempted"] is False, f"{agent} no LLM")
        assert_true(result["response"]["external_execution"] is False, f"{agent} no external")


def test_agent_bridge_failure_uses_guarded_fallback_and_skips_llm() -> None:
    result = build_company_agent_message_result(
        "operation-brief",
        "!kasumi 지원사업 후보 찾아줘",
        env=WEB_ENV,
        web_search_runner=raising_search,
    )
    content = result["response"]["content"]
    assert_true(result["agent_web_bridge_selected"] is True, "bridge selected")
    assert_true(result["normal_agent_path_skipped_for_web_bridge"] is True, "normal skipped")
    assert_true(result["llm_path_skipped_for_web_bridge"] is True, "LLM skipped")
    assert_true(result["web_reference_succeeded"] is False, "web failed")
    assert_true(result["web_reference_failure_reason"] == "web_reference_runtime_exception", "bounded failure")
    assert_true(result["response"]["reply_text_source"] == "web_reference_bridge_failure", "fallback source")
    assert_true("web_reference_runtime_exception" in content, "bounded reason visible")
    assert_true("hidden detail" not in content, "raw exception hidden")
    assert_true(result["response"]["llm_api_called"] is False, "no LLM called")
    assert_true(result["response"]["rag_called"] is False, "no RAG")
    assert_true(result["response"]["external_execution"] is False, "no external")
    assert_true(result["outbound_guard_applied"] is True, "guard applied")


def main() -> int:
    test_runtime_on_message_calls_ack_before_replied_message_fetch()
    print("PASS test_runtime_on_message_calls_ack_before_replied_message_fetch")
    test_agent_scope_bridge_for_all_explicit_agents()
    print("PASS test_agent_scope_bridge_for_all_explicit_agents")
    test_agent_bridge_failure_uses_guarded_fallback_and_skips_llm()
    print("PASS test_agent_bridge_failure_uses_guarded_fallback_and_skips_llm")
    print("All company agent runtime web bridge order tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
