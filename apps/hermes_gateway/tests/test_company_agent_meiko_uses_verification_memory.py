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


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_meiko_uses_recent_kasumi_verification_memory() -> None:
    with tempfile.TemporaryDirectory() as memory_dir:
        os.environ["HERMES_COMPANY_MEMORY_DIR"] = memory_dir
        clear_handoff_context_store()
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
        result = build_company_agent_message_result(
            "meiko-검토",
            "!meiko 방금 Kasumi가 찾은 지원사업 중 넣을만한 후보를 추천/보류/비추천으로 판단해줘",
            env={"HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "false"},
        )
    response = result.get("response", {})
    assert_true(result["selected_agent"] == "meiko", "Meiko selected")
    assert_true(result["handoff_context_used"] is True, "context used")
    assert_true(result["handoff_context_priority"] == "persistent_memory", "persistent memory priority")
    assert_true(response.get("handoff_context_used") is True, "response used context")
    assert_true("2026 디자인개발 지원사업" in response.get("content", ""), "verification content referenced")


def main() -> int:
    test_meiko_uses_recent_kasumi_verification_memory()
    print("PASS test_meiko_uses_recent_kasumi_verification_memory")
    print("All company agent Meiko verification memory tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
