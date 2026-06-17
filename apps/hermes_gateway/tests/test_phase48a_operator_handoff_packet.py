from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase48a_operator_handoff_packet import build_phase48a_operator_handoff_packet


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase48a_operator_handoff_counts() -> None:
    report = build_phase48a_operator_handoff_packet()
    assert_true(report["report_type"] == "phase48a_operator_handoff_packet", "Report type")
    assert_true(report["completed_once"]["phase41b_private_test_reply"] is True, "41B complete")
    assert_true(report["completed_once"]["phase42_supervised_private_test_session"] is True, "42 complete")
    assert_true(report["completed_once"]["phase45_llm_openrouter_call"] is True, "45 complete")
    assert_true(report["counts"]["phase41b_reply_count"] == 1, "41B count")
    assert_true(report["counts"]["phase42_message_sent_count"] == 1, "42 count")
    assert_true(report["counts"]["phase45_llm_call_count"] == 1, "45 count")
    assert_true(report["counts"]["discord_send_after_llm_count"] == 0, "No Discord after LLM")


def test_phase48a_operator_handoff_blocks_and_options() -> None:
    report = build_phase48a_operator_handoff_packet()
    blocked = report["blocked_disabled"]
    assert_true(blocked["phase41b_repeat_allowed"] is False, "41B repeat")
    assert_true(blocked["phase42_repeat_allowed"] is False, "42 repeat")
    assert_true(blocked["phase45_repeat_llm_call_allowed"] is False, "45 repeat")
    assert_true(blocked["automatic_retry_allowed"] is False, "No retry")
    assert_true(blocked["automatic_discord_send_allowed"] is False, "No Discord")
    assert_true(blocked["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(blocked["raw_output_dump_allowed"] is False, "No raw dump")
    assert_true(blocked["production_unattended_mode_ready"] is False, "No production unattended")
    assert_true("Option A: archive / human review only finish" in report["next_decision_options"], "Option A")
    assert_true("Option B: Phase48B retry Manual Gate design" in report["next_decision_options"], "Option B")
    assert_true("Option C: Phase48C Discord send review gate design" in report["next_decision_options"], "Option C")
    assert_true("Option D: Phase49 production-readiness audit" in report["next_decision_options"], "Option D")
    assert_true(report["phase48a_implements_option_b"] is False, "No B")
    assert_true(report["phase48a_implements_option_c"] is False, "No C")
    assert_true(report["phase48a_implements_option_d"] is False, "No D")


def test_phase48a_operator_handoff_no_execution() -> None:
    report = build_phase48a_operator_handoff_packet()
    assert_true(report["external_action_freeze_active"] is True, "Freeze")
    assert_true(report["future_external_action_requires_new_manual_gate"] is True, "Manual gate")
    assert_true(report["blocked_llm_output_raw_included"] is False, "No raw")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_called"] is False, "No LLM")
    assert_true(report["discord_api_send_called"] is False, "No Discord API")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")


def test_phase48a_operator_handoff_no_sensitive_values() -> None:
    text = json.dumps(build_phase48a_operator_handoff_packet(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase48a_operator_handoff_counts,
        test_phase48a_operator_handoff_blocks_and_options,
        test_phase48a_operator_handoff_no_execution,
        test_phase48a_operator_handoff_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase48A operator handoff tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
