from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

TEST_MEMORY_DIR = tempfile.TemporaryDirectory()
os.environ["HERMES_COMPANY_MEMORY_DIR"] = TEST_MEMORY_DIR.name

from company_agent_llm import build_agent_llm_messages
from company_agent_router import route_company_agent_message
from company_agent_runtime import build_company_agent_message_result
from company_context_store import clear_handoff_context_store
from company_handoff import build_handoff_post_payload
from company_persistent_memory import load_recent_records
from company_web_reference import (
    AGENT_SCOPES,
    build_company_agent_web_reference_dry_run,
    build_company_agent_web_reference_one_shot,
    build_company_agent_web_reference_report,
    detect_web_reference_intent,
    format_agent_web_reference_block,
    resolve_agent_web_scope,
    run_readonly_web_search,
)


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
                "title": "2026 로우테크 디자인 지원 및 시장 사례",
                "url": "https://example.org/reference/low-tech-2026",
                "snippet": "디자인 시제품 지원과 로우테크 가구 시장 사례를 소개합니다.",
                "institution": "디자인시장연구원",
            }
        ],
        "api_key_value_logged": False,
        "rag_called": False,
        "embedding_called": False,
        "external_execution": False,
    }


def test_report_defaults_all_agents_and_scopes() -> None:
    report = build_company_agent_web_reference_report({})
    assert_true(report["web_reference_available"] is True, "available")
    assert_true(report["default_web_reference_enabled"] is False, "default disabled")
    assert_true(report["default_web_reference_mode"] == "off", "default off")
    assert_true(report["supported_modes"] == ["off", "manual_command_only"], "modes")
    assert_true(report["allowed_agents"] == ["lucy", "marin", "meiko", "kasumi", "reze"], "all agents")
    assert_true(report["agent_scopes"] == AGENT_SCOPES, "scope mapping")
    expected = {
        "kasumi": "research_discovery",
        "meiko": "operational_verification",
        "marin": "content_reference",
        "lucy": "publication_review",
        "reze": "strategy_market_reference",
    }
    for agent, scope in expected.items():
        assert_true(resolve_agent_web_scope(agent) == scope, f"{agent} scope")
    assert_true(report["external_execution_allowed"] is False, "no external")


def test_role_scoped_intent_detection() -> None:
    cases = {
        "kasumi": ("지원사업 공모전 찾아줘", {}),
        "meiko": ("이 지원사업 마감과 자격 검증해줘", {}),
        "marin": ("요즘 로우테크 가구 인스타 레퍼런스 보고 문구 줘", {}),
        "lucy": ("이 문구 최신 표현 리스크 검토해줘", {}),
        "reze": ("로우테크 가구 시장 경쟁사 트렌드 봐줘", {}),
    }
    for agent, (message, context) in cases.items():
        assert_true(detect_web_reference_intent(agent, message, context), f"{agent} intent")
    assert_true(detect_web_reference_intent("marin", "문구", {"command": "web"}), "generic web command")
    assert_true(not detect_web_reference_intent("unknown", "시장 검색", {}), "unknown blocked")


def test_generic_commands_route_to_channel_agent() -> None:
    meiko = route_company_agent_message("meiko-검토", "!검증 마감과 자격")
    reze = route_company_agent_message("reze-전략기획", "!search 시장 경쟁사")
    assert_true(meiko["selected_agent"] == "meiko", "verify routes Meiko")
    assert_true(reze["selected_agent"] == "reze", "search routes Reze")
    assert_true(meiko["reason"] == "web_reference_command", "web command reason")


def test_all_agent_dry_runs_are_call_free() -> None:
    messages = {
        "kasumi": "이번 달 디자인 지원사업 후보 찾아줘",
        "meiko": "이 지원사업 마감과 자격 검증해줘",
        "marin": "요즘 인스타 레퍼런스 보고 문구 줘",
        "lucy": "이 문구 최신 표현 리스크 검토해줘",
        "reze": "로우테크 가구 시장 방향성 봐줘",
    }
    for agent, message in messages.items():
        dry = build_company_agent_web_reference_dry_run(agent, message, {"command": agent})
        assert_true(dry["agent_scope"] == AGENT_SCOPES[agent], f"{agent} dry scope")
        assert_true(dry["intent_detected"] is True, f"{agent} intent")
        assert_true(dry["would_search_web"] is True, f"{agent} would search")
        assert_true(dry["actual_web_called"] is False, f"{agent} no web")
        assert_true(dry["llm_api_called"] is False, f"{agent} no LLM")
        assert_true(dry["rag_called"] is False, f"{agent} no RAG")
        assert_true(dry["embedding_called"] is False, f"{agent} no embedding")
        assert_true(dry["external_execution"] is False, f"{agent} no external")


def test_one_shot_gate_and_provider_failures_are_safe() -> None:
    calls = {"count": 0}

    def should_not_run(agent: str, queries: list[str], limit: int) -> dict:
        calls["count"] += 1
        return mock_search(agent, queries, limit)

    blocked = build_company_agent_web_reference_one_shot(
        "kasumi",
        "지원사업 찾아줘",
        allow_web_reference=False,
        env=WEB_ENV,
        search_runner=should_not_run,
        context={"command": "kasumi"},
    )
    assert_true(blocked["failure_reason"] == "blocked_by_policy", "allow required")
    assert_true(blocked["web_search_attempted"] is False, "not attempted")
    assert_true(calls["count"] == 0, "runner not called")

    missing = run_readonly_web_search(
        "kasumi",
        ["지원사업"],
        env={"HERMES_WEB_SEARCH_PROVIDER": "serper", "HERMES_WEB_SEARCH_API_KEY": ""},
    )
    assert_true(missing["failure_reason"] == "api_key_missing", "missing key")
    assert_true(missing["api_key_value_logged"] is False, "key hidden")
    assert_true("HERMES_WEB_SEARCH_API_KEY" not in json.dumps(missing), "env key omitted")


def test_role_outputs_keep_sources_and_unknowns() -> None:
    markers = {
        "kasumi": "지원사업 후보:",
        "meiko": "검증 결과:",
        "marin": "레퍼런스 참고:",
        "lucy": "검토 결과:",
        "reze": "전략 판단:",
    }
    raw = mock_search("kasumi", [], 5)["results"]
    for agent, marker in markers.items():
        text = format_agent_web_reference_block(agent, raw, "로우테크 자료")
        assert_true(text.startswith("[WEB_REFERENCE]"), f"{agent} common block")
        assert_true(marker in text, f"{agent} role output")
        assert_true("https://example.org/reference/low-tech-2026" in text, f"{agent} URL")
        assert_true("최종 사용 전 원문 확인 필요" in text, f"{agent} caveat")
    unknown = format_agent_web_reference_block(
        "meiko",
        [{"title": "후보", "url": "", "snippet": "", "institution": ""}],
        "검증",
    )
    assert_true("근거 URL: 확인 필요" in unknown, "URL not invented")
    assert_true("마감: 확인 필요" in unknown, "deadline not invented")


def test_success_persists_reference_and_llm_block() -> None:
    result = build_company_agent_web_reference_one_shot(
        "reze",
        "로우테크 가구 시장 방향성 봐줘",
        allow_web_reference=True,
        env=WEB_ENV,
        search_runner=mock_search,
        context={"command": "reze", "source_channel": "reze-전략기획"},
    )
    assert_true(result["web_search_succeeded"] is True, "success")
    assert_true(result["persistent_memory_written"] is True, "memory")
    assert_true("[WEB_REFERENCE_RESULTS]" in result["web_reference_results_block"], "results block")
    recent = load_recent_records("recent_item", 10, TEST_MEMORY_DIR.name)
    assert_true(any(record.get("item_type") == "web_reference" for record in recent), "reference persisted")

    prompt = build_agent_llm_messages(
        "reze",
        "!reze 시장 방향",
        {"command": "reze", "web_reference_results_block": result["web_reference_results_block"]},
    )
    text = json.dumps(prompt["messages_preview"], ensure_ascii=False)
    assert_true(prompt["web_reference_context_used"] is True, "LLM context")
    assert_true("[WEB_REFERENCE_RESULTS]" in text, "LLM block")
    assert_true("Preserve source URLs" in prompt["messages_preview"][0]["content"], "source rule")


def test_runtime_all_agents_and_handoff_context() -> None:
    clear_handoff_context_store()
    cases = {
        "kasumi": ("kasumi-리서치", "!kasumi 디자인 지원사업 찾아줘", "지원사업 후보:"),
        "meiko": ("meiko-검토", "!meiko 공고 마감과 자격 검증해줘", "검증 결과:"),
        "marin": ("marketing-brief", "!marin 요즘 인스타 레퍼런스 보고 문구 줘", "레퍼런스 참고:"),
        "lucy": ("lucy-검토", "!lucy 이 문구 최신 표현 리스크 검토해줘", "검토 결과:"),
        "reze": ("reze-전략기획", "!reze 시장 경쟁사 트렌드 봐줘", "전략 판단:"),
    }
    results: dict[str, dict] = {}
    for agent, (channel, message, marker) in cases.items():
        result = build_company_agent_message_result(channel, message, env=WEB_ENV, web_search_runner=mock_search)
        results[agent] = result
        assert_true(result["web_reference_succeeded"] is True, f"{agent} runtime success")
        assert_true(marker in result["response"]["content"], f"{agent} output")
        assert_true(result["response"]["rag_called"] is False, f"{agent} no RAG")
        assert_true(result["response"]["embedding_called"] is False, f"{agent} no embedding")
        assert_true(result["response"]["external_execution"] is False, f"{agent} no external")

    payload = build_handoff_post_payload(results["kasumi"], "지원사업 web reference")
    assert_true(payload["web_reference_summary_included"] is True, "handoff reference metadata")
    assert_true("https://example.org/reference/low-tech-2026" in payload["handoff_message"], "handoff source")
    meiko = build_company_agent_message_result(
        "meiko-검토",
        "!meiko 이 지원사업 넣을만한지 판단해줘",
        env={**WEB_ENV, "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "false"},
    )
    assert_true(meiko["handoff_context_used"] is True, "Meiko uses Kasumi handoff")
    assert_true("2026 로우테크 디자인 지원" in meiko["response"]["content"], "Meiko sees web result")


def test_failure_reason_is_bounded() -> None:
    def failed(_agent: str, _queries: list[str], _limit: int) -> dict:
        return {"search_succeeded": False, "failure_reason": "timeout", "provider": "mock", "results": []}

    result = build_company_agent_web_reference_one_shot(
        "lucy",
        "최신 표현 리스크 검토",
        allow_web_reference=True,
        env=WEB_ENV,
        search_runner=failed,
        context={"command": "lucy"},
    )
    assert_true(result["failure_reason"] == "timeout", "reason code")
    assert_true("reason: timeout" in result["reference_report"], "safe failure")
    assert_true(result["external_execution"] is False, "no external")


def main() -> int:
    tests = [
        test_report_defaults_all_agents_and_scopes,
        test_role_scoped_intent_detection,
        test_generic_commands_route_to_channel_agent,
        test_all_agent_dry_runs_are_call_free,
        test_one_shot_gate_and_provider_failures_are_safe,
        test_role_outputs_keep_sources_and_unknowns,
        test_success_persists_reference_and_llm_block,
        test_runtime_all_agents_and_handoff_context,
        test_failure_reason_is_bounded,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    clear_handoff_context_store()
    TEST_MEMORY_DIR.cleanup()
    print("All company agent role-scoped web reference v0.7 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
