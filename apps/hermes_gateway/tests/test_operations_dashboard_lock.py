from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from operations_dashboard_lock import build_operations_dashboard_lock, render_operations_dashboard_lock_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_operations_dashboard_lock_success_fixture() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["dashboard_lock_available"] is True, "Dashboard lock available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase34_private_test_mvp_complete"] is True, "MVP complete")
    assert_true(report["phase35a_safety_audit_passed"] is True, "35A passed")
    assert_true(report["phase35b_dry_previews_available"] is True, "35B available")
    assert_true(report["phase35c_agent_prompt_previews_available"] is True, "35C available")
    assert_true(report["phase35d_review_approval_previews_available"] is True, "35D available")
    assert_true(report["phase35e_operator_rehearsal_available"] is True, "35E available")


def test_operations_dashboard_lock_final_counts() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["total_llm_call_count"] == 1, "One total LLM call in final lock fixture")
    assert_true(report["send_retry_llm_call_count"] == 0, "No send retry LLM")
    assert_true(report["final_discord_message_sent_count"] == 1, "One final Discord message in final lock fixture")
    assert_true(report["sent_channel_scope"] == "private_test_only", "Private test only")


def test_operations_dashboard_lock_safety_false() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["current_live_gates_off"] is True, "Live gates off")
    assert_true(report["public_team_blocked"] is True, "Public/team blocked")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["embedding_vector_disabled"] is True, "No embedding/vector")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["ready_for_live_runtime"] is False, "No live readiness")


def test_operations_dashboard_lock_phase36_post_call_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase36f_no_send_final_lock_passed"] is True, "36F passed")
    assert_true(report["phase36g_post_llm_dashboard_lock_available"] is True, "36G available")
    assert_true(report["phase36_total_llm_call_count"] == 1, "Phase 36 LLM count")
    assert_true(report["phase36_total_discord_message_sent_count"] == 0, "Phase 36 Discord count")
    assert_true(report["ready_for_phase37_entry_gate"] is True, "Ready for 37 gate")


def test_operations_dashboard_lock_phase38_entry_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase38e_live_send_entry_gate_available"] is True, "38E available")
    assert_true(report["phase39_not_started"] is True, "Phase 39 not started")
    assert_true(report["ready_for_phase39_live_execution"] is False, "No Phase 39 live readiness")


def test_operations_dashboard_lock_phase39a_blocked_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase39a_actual_send_path_available"] is True, "39A path available")
    assert_true(report["phase39a_blocked"] is True, "39A blocked")
    assert_true(report["phase39a_actual_private_test_send_executed"] is False, "39A no actual send")
    assert_true(report["phase39a_discord_message_sent"] is False, "39A no Discord message")
    assert_true(report["ready_for_phase39b_manual_one_shot_send"] is False, "No 39B readiness")


def test_operations_dashboard_lock_phase39b_no_send_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase39b_actual_send_not_executed_yet"] is True, "39B not executed")
    assert_true(report["phase39b_actual_discord_send_count"] == 0, "39B send count 0")
    assert_true(report["phase39b_discord_message_sent"] is False, "39B no message")
    assert_true(report["phase39c_closeout_not_available"] is True, "39C unavailable")
    assert_true(report["ready_for_phase39c_send_closeout"] is False, "No 39C ready")


def test_operations_dashboard_lock_phase39c_closeout_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase39c_closeout_completed"] is True, "39C closeout complete")
    assert_true(report["phase39c_actual_discord_send_count_locked"] == 1, "39C locked count 1")
    assert_true(report["phase39c_repeat_send_allowed"] is False, "39C no repeat")
    assert_true(report["phase39c_automatic_retry_allowed"] is False, "39C no auto retry")
    assert_true(report["phase39c_ready_for_repeat_send"] is False, "39C no repeat readiness")
    assert_true(report["phase39c_gate_off_verified"] is True, "39C gate off")
    assert_true(report["phase39c_additional_send_count"] == 0, "39C no additional send")


def test_operations_dashboard_lock_phase40_runtime_readiness_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase40_runtime_readiness_available"] is True, "40 readiness available")
    assert_true(report["phase40_actual_discord_send_count_locked"] == 1, "40 locked count")
    assert_true(report["phase40_additional_discord_send_count"] == 0, "40 no additional send")
    assert_true(report["phase40_live_runtime_started"] is False, "40 no runtime")
    assert_true(report["phase40_discord_gateway_connected"] is False, "40 no gateway")
    assert_true(report["phase40_discord_api_send_called"] is False, "40 no API send")
    assert_true(report["phase40_discord_message_sent"] is False, "40 no message")
    assert_true(report["phase40_message_sent_count"] == 0, "40 message count 0")
    assert_true(report["phase40_synthetic_replay_only"] is True, "40 synthetic replay")
    assert_true(report["phase40_outbound_queue_enabled"] is False, "40 queue off")
    assert_true(report["phase40_send_worker_enabled"] is False, "40 worker off")
    assert_true(report["phase40_duplicate_message_id_guard"] is True, "40 dedupe")
    assert_true(report["phase40_live_runtime_start_allowed"] is False, "40 live blocked")
    assert_true(report["phase40_ready_for_live_runtime_execution"] is False, "40 no live execution")
    assert_true(report["phase40_safe_to_review_next_morning"] is True, "40 safe overnight")


def test_operations_dashboard_lock_no_sensitive_values() -> None:
    text = json.dumps(build_operations_dashboard_lock(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_operations_dashboard_lock_markdown() -> None:
    assert_true("Operations Dashboard Lock" in render_operations_dashboard_lock_markdown(build_operations_dashboard_lock()), "Markdown")


def main() -> int:
    tests = [
        test_operations_dashboard_lock_success_fixture,
        test_operations_dashboard_lock_final_counts,
        test_operations_dashboard_lock_safety_false,
        test_operations_dashboard_lock_phase36_post_call_state,
        test_operations_dashboard_lock_phase38_entry_state,
        test_operations_dashboard_lock_phase39a_blocked_state,
        test_operations_dashboard_lock_phase39b_no_send_state,
        test_operations_dashboard_lock_phase39c_closeout_state,
        test_operations_dashboard_lock_phase40_runtime_readiness_state,
        test_operations_dashboard_lock_no_sensitive_values,
        test_operations_dashboard_lock_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All operations dashboard lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
