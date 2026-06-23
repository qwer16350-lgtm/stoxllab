from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result
from company_context_store import clear_handoff_context_store
from company_persistent_memory import append_memory_record


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
    "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def seed(memory_dir: str) -> None:
    append_memory_record(
        "recent_item",
        {
            "item_type": "web_reference",
            "type": "web_reference_support_program_candidates",
            "agent": "kasumi",
            "title": "지원사업 후보",
            "summary": "Kasumi support candidates",
            "content": (
                "[SUPPORT_PROGRAM_VERIFICATION]\n"
                "Candidate 1:\n"
                "- title: 서울 디자인개발 지원사업\n"
                "- deadline: 확인 필요\n"
                "[/SUPPORT_PROGRAM_VERIFICATION]"
            ),
            "status": "open",
        },
        memory_dir,
    )


def test_recent_context_policy_bypass_flags_are_explicit() -> None:
    with tempfile.TemporaryDirectory() as memory_dir:
        os.environ["HERMES_COMPANY_MEMORY_DIR"] = memory_dir
        clear_handoff_context_store()
        seed(memory_dir)
        result = build_company_agent_message_result(
            "meiko-검토",
            "!meiko 이 지원사업 넣을만한지 봐줘",
            env=WEB_ENV,
        )
    assert_true(result["recent_context_intent_detected"] is True, "recent intent")
    assert_true(result["policy_gate_skipped_for_recent_context"] is True, "policy bypass")
    assert_true(result["blocked_by_policy"] is False, "not blocked")
    assert_true(result["tavily_called"] is False, "no Tavily")
    assert_true(result["llm_api_called"] is False, "no LLM")
    assert_true(result["rag_called"] is False, "no RAG")
    assert_true(result["embedding_called"] is False, "no embedding")
    assert_true(result["external_execution"] is False, "no external")
    assert_true("blocked by policy" not in result["response"]["content"].lower(), "policy not in response")


def test_fresh_meiko_web_bridge_still_possible_without_recent_phrase() -> None:
    calls = {"count": 0}

    def mock_search(_agent_id: str, _queries: list[str], _limit: int) -> dict:
        calls["count"] += 1
        return {
            "search_succeeded": False,
            "failure_reason": "web_reference_provider_exception",
            "provider": "mock",
            "results": [],
        }

    result = build_company_agent_message_result(
        "meiko-검토",
        "!meiko 현재 신청 가능한 디자인 지원사업 검증해줘",
        env=WEB_ENV,
        web_search_runner=mock_search,
    )
    assert_true(result.get("recent_context_intent_detected") is not True, "not recent context")
    assert_true(result["agent_command_web_bridge"] is True, "web bridge remains possible")
    assert_true(result["web_reference_bridge_attempted"] is True, "web bridge attempted")
    assert_true(calls["count"] == 1, "search called once")


def main() -> int:
    test_recent_context_policy_bypass_flags_are_explicit()
    print("PASS test_recent_context_policy_bypass_flags_are_explicit")
    test_fresh_meiko_web_bridge_still_possible_without_recent_phrase()
    print("PASS test_fresh_meiko_web_bridge_still_possible_without_recent_phrase")
    print("All Meiko policy bypass tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
