from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase48a_human_review_final_closeout import build_phase48a_human_review_final_closeout


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase48a_final_closeout_contract() -> None:
    report = build_phase48a_human_review_final_closeout()
    assert_true(report["report_type"] == "phase48a_human_review_final_closeout", "Report type")
    assert_true(report["final_closeout_mode"] == "human_review_only", "Human review mode")
    assert_true(report["external_action_freeze_active"] is True, "External action freeze")
    assert_true(report["actual_discord_reply_completed_once"] is True, "Reply completed once")
    assert_true(report["actual_supervised_discord_session_completed_once"] is True, "Session completed once")
    assert_true(report["actual_llm_call_completed_once"] is True, "LLM completed once")
    assert_true(report["blocked_llm_output_raw_included"] is False, "No raw blocked output")
    assert_true(report["discord_send_after_llm"] is False, "No Discord after LLM")
    assert_true(report["automatic_retry_allowed"] is False, "No auto retry")
    assert_true(report["future_external_action_requires_new_manual_gate"] is True, "Future manual gate")
    assert_true(report["ready_for_production_unattended_mode"] is False, "No production unattended")


def test_phase48a_final_closeout_history_and_freeze() -> None:
    report = build_phase48a_human_review_final_closeout()
    assert_true(report["phase41b_private_test_reply_completed"] is True, "Phase41B completed")
    assert_true(report["phase41b_reply_count"] == 1, "Phase41B count")
    assert_true(report["phase42_supervised_session_completed"] is True, "Phase42 completed")
    assert_true(report["phase42_message_sent_count"] == 1, "Phase42 count")
    assert_true(report["phase45_actual_llm_call_completed"] is True, "Phase45 completed")
    assert_true(report["phase45_llm_call_count"] == 1, "Phase45 count")
    assert_true(report["phase45_output_safety_blocked"] is True, "Phase45 blocked")
    assert_true(report["phase41b_repeat_allowed"] is False, "Phase41B repeat frozen")
    assert_true(report["phase42_repeat_allowed"] is False, "Phase42 repeat frozen")
    assert_true(report["phase45_repeat_llm_call_allowed"] is False, "Phase45 repeat frozen")
    assert_true(report["automatic_discord_send_allowed"] is False, "No auto Discord")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")


def test_phase48a_final_closeout_no_execution() -> None:
    report = build_phase48a_human_review_final_closeout()
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_called"] is False, "No LLM call")
    assert_true(report["additional_llm_api_call"] is False, "No extra LLM")
    assert_true(report["discord_api_send_called"] is False, "No Discord API")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["option_b_phase48b_retry_manual_gate_design_implemented"] is False, "No option B")
    assert_true(report["option_c_phase48c_discord_send_review_gate_design_implemented"] is False, "No option C")
    assert_true(report["option_d_phase49_production_readiness_audit_implemented"] is False, "No option D")


def test_phase48a_final_closeout_no_sensitive_values() -> None:
    text = json.dumps(build_phase48a_human_review_final_closeout(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase48a_final_closeout_contract,
        test_phase48a_final_closeout_history_and_freeze,
        test_phase48a_final_closeout_no_execution,
        test_phase48a_final_closeout_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase48A human-review final closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
