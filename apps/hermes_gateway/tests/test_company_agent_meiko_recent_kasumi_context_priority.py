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
    "HERMES_COMPANY_AGENT_LLM_MODE": "off",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def seed_kasumi_memory(memory_dir: str) -> None:
    append_memory_record(
        "recent_item",
        {
            "item_type": "web_reference",
            "type": "web_reference_support_program_candidates",
            "agent": "kasumi",
            "title": "디자인 지원사업 후보",
            "summary": "Kasumi web reference 2건",
            "content": (
                "[SUPPORT_PROGRAM_VERIFICATION]\n"
                "candidate_count: 2\n"
                "Candidate 1:\n"
                "- title: 2026 디자인개발 지원사업 모집 공고\n"
                "- deadline: 2026년 6월 25일\n"
                "- confidence: 높음\n"
                "[/SUPPORT_PROGRAM_VERIFICATION]"
            ),
            "status": "open",
        },
        memory_dir,
    )


def test_meiko_recent_context_priority_skips_web_bridge() -> None:
    with tempfile.TemporaryDirectory() as memory_dir:
        os.environ["HERMES_COMPANY_MEMORY_DIR"] = memory_dir
        clear_handoff_context_store()
        seed_kasumi_memory(memory_dir)

        def should_not_search(_agent_id: str, _queries: list[str], _limit: int) -> dict:
            raise AssertionError("web search must not run")

        result = build_company_agent_message_result(
            "meiko-검토",
            "!meiko 방금 Kasumi가 찾은 지원사업 검토해줘",
            env=WEB_ENV,
            web_search_runner=should_not_search,
        )

    content = result["response"]["content"]
    assert_true(result["selected_agent"] == "meiko", "Meiko selected")
    assert_true(result["recent_context_intent_detected"] is True, "recent context intent")
    assert_true(result["recent_context_lookup_succeeded"] is True, "lookup succeeded")
    assert_true(result["web_bridge_skipped_for_recent_context"] is True, "web bridge skipped")
    assert_true(result["policy_gate_skipped_for_recent_context"] is True, "policy skipped")
    assert_true(result["blocked_by_policy"] is False, "not blocked")
    assert_true(result["web_reference_attempted"] is False, "no web reference")
    assert_true("blocked by policy" not in content.lower(), "no policy text")
    assert_true("판단 요약:" in content, "judgement summary")
    assert_true("- 추천:" in content and "- 보류:" in content and "- 비추천:" in content, "three-way judgement")
    assert_true("2026 디자인개발 지원사업" in content, "candidate referenced")


def test_meiko_recent_context_priority_accepts_korean_kasumi_alias() -> None:
    with tempfile.TemporaryDirectory() as memory_dir:
        os.environ["HERMES_COMPANY_MEMORY_DIR"] = memory_dir
        clear_handoff_context_store()
        seed_kasumi_memory(memory_dir)
        result = build_company_agent_message_result(
            "meiko-검토",
            "!meiko 방금 카스미가 찾은 지원사업 검토해줘",
            env=WEB_ENV,
        )
    assert_true(result["recent_context_lookup_succeeded"] is True, "Korean alias lookup")
    assert_true(result["response"]["reply_text_source"] == "recent_kasumi_verification_context", "recent context source")


def main() -> int:
    test_meiko_recent_context_priority_skips_web_bridge()
    print("PASS test_meiko_recent_context_priority_skips_web_bridge")
    test_meiko_recent_context_priority_accepts_korean_kasumi_alias()
    print("PASS test_meiko_recent_context_priority_accepts_korean_kasumi_alias")
    print("All Meiko recent Kasumi context priority tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
