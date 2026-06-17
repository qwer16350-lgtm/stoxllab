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


def test_operations_dashboard_lock_phase41b_45a_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase41b_one_shot_available"] is True, "41B available")
    assert_true(report["phase41b_actual_runtime_path_available"] is True, "41B runtime path")
    assert_true(report["phase41b_actual_runtime_executed"] is False, "41B no runtime")
    assert_true(report["phase41b_real_discord_send_adapter_wired"] is True, "41B real adapter wired")
    assert_true(report["phase41b_fake_adapter_contract_passed"] is True, "41B fake contract")
    assert_true(report["phase41b_default_blocked"] is True, "41B blocked")
    assert_true(report["phase41b_message_sent_count"] == 0, "41B no send")
    assert_true(report["phase41c_closeout_available"] is True, "41C available")
    assert_true(report["phase41c_actual_private_test_reply_verified"] is True, "41C success observed")
    assert_true(report["phase41c_message_sent_count"] == 1, "41C observed count 1")
    assert_true(report["phase41c_sent_scope"] == "private_test_only", "41C private scope")
    assert_true(report["phase41c_repeat_send_blocked"] is True, "41C repeat locked")
    assert_true(report["phase41c_discord_api_send_called_during_phase41c"] is False, "41C no API")
    assert_true(report["phase41c_discord_message_sent_during_phase41c"] is False, "41C no message")
    assert_true(report["phase42_session_preflight_available"] is True, "42 available")
    assert_true(report["phase42_default_blocked"] is True, "42 default blocked")
    assert_true(report["phase42_blocked"] is True, "42 blocked")
    assert_true(report["phase42_manual_gate_required"] is True, "42 manual gate required")
    assert_true(report["phase42_manual_gate_open"] is False, "42 manual gate closed")
    assert_true(report["phase42_actual_supervised_session_executed"] is False, "42 no supervised session")
    assert_true(report["phase42_actual_runtime_executed"] is False, "42 no runtime")
    assert_true(report["phase42_ready_for_manual_supervised_session"] is False, "42 no manual readiness")
    assert_true(report["phase42_ready_for_phase41b_repeat_send"] is False, "42 no 41B repeat")
    assert_true(report["phase42_public_team_blocked"] is True, "42 public/team blocked")
    assert_true(report["phase42_session_lock_active"] is True, "42 session lock")
    assert_true(report["phase42_discord_api_send_called"] is False, "42 no API")
    assert_true(report["phase43_public_team_blocked"] is True, "43 public/team blocked")
    assert_true(report["phase43_phase41b_repeat_send_locked"] is True, "43 41B repeat locked")
    assert_true(report["phase43_phase42_manual_gate_open"] is False, "43 42 gate closed")
    assert_true(report["phase43_ready_for_phase42_actual_supervised_session"] is False, "43 no 42 actual")
    assert_true(report["phase44_actual_llm_api_call"] is False, "44 no LLM")
    assert_true(report["phase44_fake_output_schema_valid"] is True, "44 fake valid")
    assert_true(report["phase45_actual_llm_api_call"] is False, "45 no LLM")


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


def test_operations_dashboard_lock_phase40j_n_readonly_entry_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase40j_readonly_preflight_available"] is True, "40J preflight")
    assert_true(report["phase40j_ready_for_manual_readonly_runtime_launch"] is False, "40J not ready")
    assert_true(report["phase40k_manual_launch_only"] is True, "40K manual only")
    assert_true(report["phase40k_codex_must_not_launch"] is True, "40K codex no launch")
    assert_true(report["phase40k_planned_command_executed_by_codex"] is False, "40K command not executed")
    assert_true(report["phase40l_capture_closeout_available"] is True, "40L closeout")
    assert_true(report["phase40l_live_capture_observed"] is False, "40L no capture")
    assert_true(report["phase40l_captured_event_count"] == 0, "40L no events")
    assert_true(report["phase40m_manual_abort_available"] is True, "40M abort")
    assert_true(report["phase40m_abort_on_any_send_attempt"] is True, "40M send abort")
    assert_true(report["phase40n_phase41_reply_runtime_entry_gate_available"] is True, "40N gate")
    assert_true(report["phase40n_phase41_reply_runtime_allowed"] is False, "40N blocked")
    assert_true(report["phase40n_reply_send_allowed"] is False, "40N no reply")
    assert_true(report["phase40n_ready_for_phase41_reply_runtime"] is False, "40N not ready")


def test_operations_dashboard_lock_phase40o_s_review_pipeline_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase40o_manual_launch_only"] is True, "40O manual")
    assert_true(report["phase40o_codex_must_not_launch"] is True, "40O codex no launch")
    assert_true(report["phase40o_ready_for_manual_readonly_runtime_launch"] is False, "40O not ready")
    assert_true(report["phase40p_capture_schema_available"] is True, "40P schema")
    assert_true(report["phase40p_raw_content_logged"] is False, "40P raw false")
    assert_true(report["phase40p_secret_values_logged"] is False, "40P secrets false")
    assert_true(report["phase40q_capture_file_present"] is False, "40Q no file")
    assert_true(report["phase40q_capture_review_completed"] is False, "40Q no review")
    assert_true(report["phase40q_message_sent_count"] == 0, "40Q no send")
    assert_true(report["phase40r_phase41_reply_runtime_allowed"] is False, "40R blocked")
    assert_true(report["phase40r_discord_reply_send_allowed"] is False, "40R no reply")
    assert_true(report["phase40r_llm_reply_allowed"] is False, "40R no LLM")
    assert_true(report["phase40r_rag_reply_allowed"] is False, "40R no RAG")
    assert_true(report["phase40s_safe_to_review_next_morning"] is True, "40S safe")
    assert_true(report["phase40s_requires_user_confirmation"] is True, "40S confirmation")
    assert_true(report["phase40s_additional_discord_send_count"] == 0, "40S no send")
    assert_true(report["phase40t_command_available"] is True, "40T command")
    assert_true(report["phase40t_blocked_by_default"] is True, "40T blocked")
    assert_true(report["phase40t_manual_runtime_launch_allowed"] is False, "40T no launch by default")
    assert_true(report["phase40t_codex_runtime_launch_forbidden"] is True, "40T codex forbidden")
    assert_true(report["phase40t_live_runtime_started"] is False, "40T no live")
    assert_true(report["phase40t_discord_gateway_connected"] is False, "40T no gateway")
    assert_true(report["phase40t_discord_api_send_called"] is False, "40T no API")
    assert_true(report["phase40t_discord_message_sent"] is False, "40T no message")
    assert_true(report["phase40t_message_sent_count"] == 0, "40T count 0")
    assert_true(report["phase40t_preflight_snapshot_preserved"] is True, "40T snapshot")
    assert_true(report["phase40t_presence_consistency_verified"] is True, "40T consistency")
    assert_true(report["phase40t_login_attempt_requires_token_and_channel"] is True, "40T login requires token/channel")
    assert_true(report["phase40t_execution_gate_available"] is True, "40T-1 gate")
    assert_true(report["phase40t_execute_flag_required"] is True, "40T-1 execute required")
    assert_true(report["phase40t_execute_flag_present"] is False, "40T-1 execute absent")
    assert_true(report["phase40t_execution_gate_blocked_by_default"] is True, "40T-1 blocked")
    assert_true(report["phase40t_redacted_capture_only"] is True, "40T-1 redacted")
    assert_true(report["phase40t_capture_raw_content_allowed"] is False, "40T-1 no raw")
    assert_true(report["phase40t_closeout_started"] is False, "40T-1 closeout not started")
    assert_true(report["phase40t_closeout_gateway_connected"] is False, "40T-1 closeout no gateway")
    assert_true(report["phase40t_closeout_message_sent_count"] == 0, "40T-1 closeout no send")
    assert_true(report["phase40t_login_failure_closeout_available"] is True, "40T-2 login failure closeout")
    assert_true(report["phase40t_login_failure_gateway_connected"] is False, "40T-2 no gateway")
    assert_true(report["phase40t_login_failure_discord_api_send_called"] is False, "40T-2 no API")
    assert_true(report["phase40t_login_failure_discord_message_sent"] is False, "40T-2 no message")
    assert_true(report["phase40t_login_failure_message_sent_count"] == 0, "40T-2 count 0")
    assert_true(report["phase40t_login_failure_retry_attempted"] is False, "40T-2 no retry")
    assert_true(report["phase40t_login_failure_traceback_included"] is False, "40T-2 no traceback")
    assert_true(report["phase40t_login_failure_preflight_snapshot_preserved"] is True, "40T-3 failure snapshot")
    assert_true(report["phase40t_login_failure_presence_consistency_verified"] is True, "40T-3 failure consistency")


def test_operations_dashboard_lock_phase40u_41a_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase40t_gateway_connect_verified"] is True, "40U Gateway verified")
    assert_true(report["phase40u_closeout_ready"] is True, "40U closeout ready")
    assert_true(report["phase40u_discord_api_send_called"] is False, "40U no API send")
    assert_true(report["phase40u_discord_message_sent"] is False, "40U no message")
    assert_true(report["phase40u_message_sent_count"] == 0, "40U count 0")
    assert_true(report["phase40x_reply_dry_run_ready"] is True, "40X dry-run ready")
    assert_true(report["phase40x_discord_api_send_called"] is False, "40X no API send")
    assert_true(report["phase40x_discord_message_sent"] is False, "40X no message")
    assert_true(report["phase40x_message_sent_count"] == 0, "40X count 0")
    assert_true(report["phase41_actual_reply_default_blocked"] is True, "41 default blocked")
    assert_true(report["phase41_actual_reply_send_executed"] is False, "41 no actual reply")
    assert_true(report["phase41_discord_api_send_called"] is False, "41 no API send")
    assert_true(report["phase41_discord_message_sent"] is False, "41 no message")
    assert_true(report["phase41_message_sent_count"] == 0, "41 count 0")
    assert_true(report["phase40z_handoff_ready"] is True, "40Z handoff ready")
    assert_true(report["phase41a_preflight_default_blocked"] is True, "41A default blocked")
    assert_true(report["phase41a_ready_for_manual_private_test_reply"] is False, "41A not ready")


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
        test_operations_dashboard_lock_phase41b_45a_state,
        test_operations_dashboard_lock_phase36_post_call_state,
        test_operations_dashboard_lock_phase38_entry_state,
        test_operations_dashboard_lock_phase39a_blocked_state,
        test_operations_dashboard_lock_phase39b_no_send_state,
        test_operations_dashboard_lock_phase39c_closeout_state,
        test_operations_dashboard_lock_phase40_runtime_readiness_state,
        test_operations_dashboard_lock_phase40j_n_readonly_entry_state,
        test_operations_dashboard_lock_phase40o_s_review_pipeline_state,
        test_operations_dashboard_lock_phase40u_41a_state,
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
