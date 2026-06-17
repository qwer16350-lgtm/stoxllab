from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from forbidden_behavior_sentinel import build_forbidden_behavior_sentinel, render_forbidden_behavior_sentinel_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def test_forbidden_behavior_sentinel_success_fixture() -> None:
    report = build_forbidden_behavior_sentinel()
    assert_true(report["sentinel_available"] is True, "Sentinel available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["forbidden_behavior_sentinel_passed"] is True, "Sentinel passed")
    assert_true(report["public_team_blocked"] is True, "Public/team blocked")
    assert_true(report["embedding_vector_disabled"] is True, "Embedding/vector disabled")
    assert_true(report["phase39c_actual_discord_send_count_locked"] == 1, "39C locked count")
    assert_true(report["phase39c_no_repeat_lock_active"] is True, "39C no-repeat active")
    assert_true(report["phase40_actual_discord_send_count_locked"] == 1, "40 locked count")
    assert_true(report["phase40_additional_discord_send_count"] == 0, "40 no additional send")
    assert_true(report["phase40_message_sent_count"] == 0, "40 no message count")
    assert_true(report["phase40_synthetic_replay_only"] is True, "40 synthetic replay")
    assert_true(report["phase40_duplicate_message_id_guard"] is True, "40 duplicate guard")
    assert_true(report["phase40j_readonly_preflight_available"] is True, "40J preflight")
    assert_true(report["phase40k_manual_launch_only"] is True, "40K manual")
    assert_true(report["phase40k_codex_must_not_launch"] is True, "40K codex no launch")
    assert_true(report["phase40l_capture_closeout_available"] is True, "40L closeout")
    assert_true(report["phase40m_manual_abort_available"] is True, "40M abort")
    assert_true(report["phase40n_phase41_reply_runtime_entry_gate_available"] is True, "40N gate")
    assert_true(report["phase40o_manual_launch_only"] is True, "40O manual")
    assert_true(report["phase40o_codex_must_not_launch"] is True, "40O codex no launch")
    assert_true(report["phase40p_capture_schema_available"] is True, "40P schema")
    assert_true(report["phase40r_phase41_reply_runtime_entry_available"] is True, "40R matrix")
    assert_true(report["phase40s_safe_to_review_next_morning"] is True, "40S safe")
    assert_true(report["phase40s_requires_user_confirmation"] is True, "40S confirmation")
    assert_true(report["phase40t_command_available"] is True, "40T command")
    assert_true(report["phase40t_blocked_by_default"] is True, "40T blocked")
    assert_true(report["phase40t_codex_runtime_launch_forbidden"] is True, "40T codex forbidden")
    assert_true(report["phase40t_message_sent_count"] == 0, "40T no send")
    assert_true(report["phase40t_execute_flag_required"] is True, "40T execute required")
    assert_true(report["phase40t_execute_flag_present"] is False, "40T execute absent")
    assert_true(report["phase40t_execution_gate_blocked_by_default"] is True, "40T execution blocked")
    assert_true(report["phase40t_closeout_message_sent_count"] == 0, "40T closeout no send")
    assert_true(report["phase40t_login_failure_closeout_available"] is True, "40T login failure closeout")
    assert_true(report["phase40t_login_failure_message_sent_count"] == 0, "40T login failure no send")
    assert_true(report["phase40t_login_failure_retry_attempted"] is False, "40T login failure no retry")
    assert_true(report["phase40t_preflight_snapshot_preserved"] is True, "40T snapshot preserved")
    assert_true(report["phase40t_presence_consistency_verified"] is True, "40T presence consistent")
    assert_true(report["phase40t_login_failure_preflight_snapshot_preserved"] is True, "40T failure snapshot")
    assert_true(report["phase40t_login_failure_presence_consistency_verified"] is True, "40T failure consistency")
    assert_true(report["phase40t_missing_env_before_login_guard"] is True, "40T missing-env guard")
    assert_true(report["phase40u_closeout_ready"] is True, "40U closeout ready")
    assert_true(report["phase40u_message_sent_count"] == 0, "40U no send")
    assert_true(report["phase40x_reply_dry_run_ready"] is True, "40X dry-run ready")
    assert_true(report["phase40x_message_sent_count"] == 0, "40X no send")
    assert_true(report["phase41_actual_reply_default_blocked"] is True, "41 default blocked")
    assert_true(report["phase41_actual_reply_send_executed"] is False, "41 no actual reply")
    assert_true(report["phase41_message_sent_count"] == 0, "41 no send")
    assert_true(report["phase41_public_team_reply_allowed"] is False, "41 public/team blocked")
    assert_true(report["phase41_unattended_auto_reply_allowed"] is False, "41 no unattended")
    assert_true(report["phase41b_one_shot_available"] is True, "41B available")
    assert_true(report["phase41b_actual_runtime_path_available"] is True, "41B runtime path")
    assert_true(report["phase41b_actual_runtime_executed"] is False, "41B no runtime")
    assert_true(report["phase41b_real_discord_send_adapter_wired"] is True, "41B real adapter wired")
    assert_true(report["phase41b_fake_adapter_contract_passed"] is True, "41B fake contract")
    assert_true(report["phase41b_default_blocked"] is True, "41B blocked")
    assert_true(report["phase41b_message_sent_count"] == 0, "41B no send")
    assert_true(report["phase41c_closeout_available"] is True, "41C closeout")
    assert_true(report["phase41c_actual_private_test_reply_verified"] is True, "41C success")
    assert_true(report["phase41c_message_sent_count"] == 1, "41C observed count")
    assert_true(report["phase41c_sent_scope"] == "private_test_only", "41C scope")
    assert_true(report["phase41c_repeat_send_blocked"] is True, "41C repeat locked")
    assert_true(report["phase41c_discord_api_send_called_during_phase41c"] is False, "41C no API")
    assert_true(report["phase41c_discord_message_sent_during_phase41c"] is False, "41C no message")
    assert_true(report["phase42_session_preflight_available"] is True, "42 preflight")
    assert_true(report["phase42_actual_runtime_cli_available"] is True, "42 actual CLI")
    assert_true(report["phase42_allow_flag_available"] is True, "42 allow flag")
    assert_true(report["phase42_runtime_default_blocked"] is True, "42 runtime default blocked")
    assert_true(report["phase42_runtime_allow_flag_present"] is False, "42 allow absent")
    assert_true(report["phase42_runtime_message_sent_count"] == 0, "42 runtime no send")
    assert_true(report["phase42_actual_session_closeout_available"] is True, "42 closeout")
    assert_true(report["phase42_actual_supervised_private_test_session_succeeded"] is True, "42 success")
    assert_true(report["phase42_exactly_once_supervised_success_recorded"] is True, "42 exactly once")
    assert_true(report["phase42_success_message_sent_count"] == 1, "42 observed one send")
    assert_true(report["phase42_success_sent_scope"] == "private_test_only", "42 private-test")
    assert_true(report["phase42_success_session_lock_consumed"] is True, "42 lock consumed")
    assert_true(report["phase42_repeat_supervised_session_locked"] is True, "42 repeat locked")
    assert_true(report["phase42_repeat_supervised_session_allowed"] is False, "42 repeat disallowed")
    assert_true(report["phase42_closeout_discord_api_send_called"] is False, "42 closeout no API")
    assert_true(report["phase42_closeout_discord_message_sent"] is False, "42 closeout no message")
    assert_true(report["phase42_closeout_additional_message_sent_count"] == 0, "42 closeout no extra send")
    assert_true(report["phase42_default_blocked"] is True, "42 default blocked")
    assert_true(report["phase42_blocked"] is True, "42 blocked")
    assert_true(report["phase42_manual_gate_required"] is True, "42 manual gate")
    assert_true(report["phase42_manual_gate_open"] is False, "42 gate closed")
    assert_true(report["phase42_actual_supervised_session_executed"] is False, "42 no supervised session")
    assert_true(report["phase42_discord_api_send_called"] is False, "42 no API")
    assert_true(report["phase42_public_team_blocked"] is True, "42 public/team")
    assert_true(report["phase42_session_lock_active"] is True, "42 session lock")
    assert_true(report["phase43_public_team_blocked"] is True, "43 public/team")
    assert_true(report["phase43_phase41b_repeat_send_locked"] is True, "43 41B repeat")
    assert_true(report["phase43_phase42_repeat_supervised_session_locked"] is True, "43 42 repeat")
    assert_true(report["phase43_phase42_manual_gate_open"] is False, "43 42 gate closed")
    assert_true(report["phase44_provider_preflight_available"] is True, "44 provider")
    assert_true(report["phase44_fake_output_schema_valid"] is True, "44 fake valid")
    assert_true(report["phase45_preflight_available"] is True, "45 preflight")
    assert_true(report["phase45_llm_api_call_count"] == 0, "45 count 0")
    assert_true(report["phase45_actual_llm_call_closeout_available"] is True, "45 closeout")
    assert_true(report["phase45_actual_llm_one_shot_completed"] is True, "45 completed")
    assert_true(report["phase45_actual_llm_call_count"] == 1, "45 historical count")
    assert_true(report["phase45_actual_llm_one_shot_repeat_locked"] is True, "45 repeat locked")
    assert_true(report["phase45_ready_for_repeat_llm_call"] is False, "45 no repeat")
    assert_true(report["phase45_output_safety_blocked"] is True, "45 output blocked")
    assert_true(report["phase45_llm_response_packet_created"] is False, "45 no packet")
    assert_true(report["phase45_closeout_discord_api_send_called"] is False, "45 closeout no API")
    assert_true(report["phase45_closeout_discord_message_sent"] is False, "45 closeout no message")
    assert_true(report["phase45_closeout_message_sent_count"] == 0, "45 closeout count 0")
    assert_true(report["phase46_blocked_llm_output_review_available"] is True, "46 review")
    assert_true(report["phase46_metadata_only"] is True, "46 metadata")
    assert_true(report["phase46_raw_output_included"] is False, "46 no raw")
    assert_true(report["phase46_full_content_included"] is False, "46 no full")
    assert_true(report["phase46_automatic_retry_allowed"] is False, "46 no auto retry")
    assert_true(report["phase46_retry_requires_new_manual_gate"] is True, "46 manual gate")
    assert_true(report["phase46_llm_retry_policy_available"] is True, "46 retry policy")
    assert_true(report["phase46_repeat_phase45_call_allowed"] is False, "46 no repeat")
    assert_true(report["phase46_discord_send_remains_disabled"] is True, "46 Discord disabled")
    assert_true(report["phase46_llm_api_called"] is False, "46 no LLM")
    assert_true(report["phase46_discord_message_sent"] is False, "46 no Discord")
    assert_true(report["phase47_human_review_closeout_available"] is True, "47 closeout")
    assert_true(report["phase47_human_review_required"] is True, "47 human review")
    assert_true(report["phase47_phase45_llm_call_count"] == 1, "47 historical count")
    assert_true(report["phase47_output_safety_blocked"] is True, "47 blocked")
    assert_true(report["phase47_phase45_repeat_llm_call_forbidden"] is True, "47 repeat forbidden")
    assert_true(report["phase47_blocked_output_auto_retry_forbidden"] is True, "47 retry forbidden")
    assert_true(report["phase47_blocked_output_auto_discord_send_forbidden"] is True, "47 auto send forbidden")
    assert_true(report["phase47_raw_output_dump_forbidden"] is True, "47 raw dump forbidden")
    assert_true(report["phase47_automatic_retry_allowed"] is False, "47 no auto retry")
    assert_true(report["phase47_retry_execution_available"] is False, "47 no retry execution")
    assert_true(report["phase47_disabled_retry_gate_design_available"] is True, "47 design")
    assert_true(report["phase47_retry_gate_implemented"] is False, "47 gate disabled")
    assert_true(report["phase47_repeat_phase45_call_allowed"] is False, "47 no repeat")
    assert_true(report["phase47_manual_retry_requires_new_phase"] is True, "47 new phase")
    assert_true(report["phase47_manual_retry_requires_new_approval_phrase"] is True, "47 new phrase")
    assert_true(report["phase47_manual_retry_requires_cost_guard"] is True, "47 cost guard")
    assert_true(report["phase47_manual_retry_requires_call_count_guard"] is True, "47 count guard")
    assert_true(report["phase47_discord_send_remains_disabled"] is True, "47 Discord disabled")


def test_forbidden_behavior_sentinel_flags_false() -> None:
    report = build_forbidden_behavior_sentinel()
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated"):
        assert_true(report[key] is False, f"{key} false")


def test_forbidden_behavior_sentinel_negative_fixtures() -> None:
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated", "discord_api_send_called", "actual_private_test_send_executed", "actual_send_implementation_executed", "new_llm_api_call_attempted", "new_llm_api_called", "llm_api_call_attempted", "llm_api_called", "discord_live_runtime_executed", "ready_for_discord_send", "ready_for_actual_private_test_send", "ready_for_phase37d_actual_private_test_send", "ready_for_phase38_actual_private_test_send_path", "ready_for_phase39_live_execution", "ready_for_phase39b_manual_one_shot_send", "ready_for_phase39b_actual_send_manual_attempt", "ready_for_phase39c_send_closeout", "actual_discord_api_send_called", "actual_discord_message_sent", "api_key_value_logged", "token_value_logged", "discord_token_value_logged", "private_test_channel_id_value_logged", "raw_discord_ids_logged", "approval_phrase_value_logged", "additional_discord_send_called_in_phase39c", "additional_discord_message_sent_in_phase39c", "phase39c_repeat_send_allowed", "phase39c_automatic_retry_allowed", "phase39c_manual_retry_allowed", "phase39c_ready_for_repeat_send", "phase40_live_runtime_started", "phase40_discord_gateway_connected", "phase40_discord_api_send_called", "phase40_discord_message_sent", "phase40_repeat_send_allowed", "phase40_automatic_retry_allowed", "phase40_unattended_auto_reply_allowed", "phase40_public_channel_send_allowed", "phase40_team_channel_send_allowed", "phase40_public_channel_reply_allowed", "phase40_team_channel_reply_allowed", "phase40_llm_api_call_attempted", "phase40_llm_api_called", "phase40_rag_called", "phase40_embedding_api_called", "phase40_vector_index_created", "phase40_external_execution", "phase40_secret_values_logged", "phase40_ready_for_live_runtime_execution", "phase40j_live_runtime_started", "phase40j_discord_gateway_connected", "phase40j_ready_for_manual_readonly_runtime_launch", "phase40k_planned_command_executed_by_codex", "phase40k_live_runtime_started", "phase40k_discord_gateway_connected", "phase40l_live_capture_observed", "phase40m_discord_api_send_called", "phase40m_discord_message_sent", "phase40n_phase41_reply_runtime_allowed", "phase40n_reply_send_allowed", "phase40n_llm_reply_allowed", "phase40n_rag_reply_allowed", "phase40n_ready_for_phase41_reply_runtime", "phase40o_live_runtime_started", "phase40o_discord_gateway_connected", "phase40o_discord_api_send_called", "phase40o_discord_message_sent", "phase40o_ready_for_manual_readonly_runtime_launch", "phase40p_raw_content_logged", "phase40p_raw_discord_ids_logged", "phase40p_secret_values_logged", "phase40q_capture_review_completed", "phase40q_discord_api_send_called", "phase40q_discord_message_sent", "phase40q_ready_for_phase41_reply_runtime", "phase40r_phase41_reply_runtime_allowed", "phase40r_discord_reply_send_allowed", "phase40r_llm_reply_allowed", "phase40r_rag_reply_allowed", "phase40s_live_runtime_started_by_codex", "phase40s_overnight_external_actions_executed_by_codex", "phase40s_phase41_reply_runtime_allowed", "phase40t_live_runtime_started", "phase40t_discord_gateway_connected", "phase40t_discord_api_send_called", "phase40t_discord_message_sent", "phase40t_send_messages_enabled", "phase40t_private_test_reply_enabled", "phase40t_llm_called", "phase40t_rag_called", "phase40t_embedding_api_called", "phase40t_vector_index_created", "phase40t_external_execution", "phase40t_secret_values_logged", "phase40t_raw_discord_ids_logged", "phase40t_approval_phrase_value_logged", "phase40t_ready_for_phase41_reply_runtime", "phase40t_execute_flag_present", "phase40t_capture_file_contains_raw_content", "phase40t_capture_file_contains_raw_discord_ids", "phase40t_capture_file_contains_secret_values", "phase40t_closeout_started", "phase40t_closeout_gateway_connected", "phase40t_login_failure_gateway_connected", "phase40t_login_failure_discord_api_send_called", "phase40t_login_failure_discord_message_sent", "phase40t_login_failure_retry_attempted", "phase40t_login_failure_traceback_included", "phase40t_login_failure_token_value_logged", "phase40t_missing_env_login_attempted", "phase40u_discord_api_send_called", "phase40u_discord_message_sent", "phase40x_discord_api_send_called", "phase40x_discord_message_sent", "phase41_actual_reply_send_executed", "phase41_discord_api_send_called", "phase41_discord_message_sent", "phase41_public_team_reply_allowed", "phase41_unattended_auto_reply_allowed", "phase41_llm_called", "phase41_rag_called", "phase41_embedding_api_called", "phase41_external_execution", "phase41_raw_content_logged", "phase41_raw_discord_ids_logged", "phase41_secret_values_logged", "phase41_actual_reply_without_one_shot_manual_gate"):
        assert_raises(lambda selected=key: build_forbidden_behavior_sentinel({selected: True}), f"{key} should fail")


def test_forbidden_behavior_sentinel_actual_message_count_fixture() -> None:
    assert_raises(lambda: build_forbidden_behavior_sentinel({"actual_message_sent_count": 1}), "Actual message count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"actual_discord_send_count": 1}), "Actual Discord send count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"additional_message_sent_count_in_phase39c": 1}), "Phase 39C additional count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_actual_discord_send_count_locked": 2}), "Phase 40 count should stay 1")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_additional_discord_send_count": 1}), "Phase 40 additional count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_message_sent_count": 1}), "Phase 40 message count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_synthetic_replay_only": False}), "Phase 40 synthetic replay required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_duplicate_message_id_guard": False}), "Phase 40 duplicate guard required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40j_readonly_preflight_available": False}), "Phase 40J preflight required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40k_manual_launch_only": False}), "Phase 40K manual only required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40k_codex_must_not_launch": False}), "Phase 40K Codex no-launch required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40l_capture_closeout_available": False}), "Phase 40L closeout required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40l_captured_event_count": 1}), "Phase 40L captured count must stay 0")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40m_manual_abort_available": False}), "Phase 40M abort required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40m_abort_on_any_send_attempt": False}), "Phase 40M send abort required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40n_phase41_reply_runtime_entry_gate_available": False}), "Phase 40N gate required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40o_manual_launch_only": False}), "Phase 40O manual launch required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40o_codex_must_not_launch": False}), "Phase 40O no launch required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40p_capture_schema_available": False}), "Phase 40P schema required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40q_message_sent_count": 1}), "Phase 40Q count 0 required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40r_phase41_reply_runtime_entry_available": False}), "Phase 40R matrix required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40s_safe_to_review_next_morning": False}), "Phase 40S safe review required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40s_requires_user_confirmation": False}), "Phase 40S confirmation required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40s_additional_discord_send_count": 1}), "Phase 40S no additional send")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_command_available": False}), "Phase 40T command required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_blocked_by_default": False}), "Phase 40T blocked required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_codex_runtime_launch_forbidden": False}), "Phase 40T codex forbidden required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_message_sent_count": 1}), "Phase 40T count 0 required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_ready_for_manual_readonly_runtime_launch": True, "phase40t_reply_mode_readonly_private_test_only": False}), "Phase 40T ready requires readonly mode")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_execute_flag_required": False}), "Phase 40T execute required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_execution_gate_blocked_by_default": False}), "Phase 40T execution blocked")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_closeout_message_sent_count": 1}), "Phase 40T closeout count 0 required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_live_runtime_started": True, "phase40t_execute_flag_present": False}), "Phase 40T started needs execute")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_login_failure_closeout_available": False}), "Phase 40T login closeout required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_login_failure_message_sent_count": 1}), "Phase 40T login failure no send")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_preflight_snapshot_preserved": False}), "Phase 40T snapshot required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_login_failure_preflight_snapshot_preserved": False}), "Phase 40T failure snapshot required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40t_missing_env_before_login_guard": False}), "Phase 40T missing env guard required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40u_closeout_ready": False}), "Phase 40U closeout required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40u_message_sent_count": 1}), "Phase 40U count 0 required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40x_reply_dry_run_ready": False}), "Phase 40X dry-run required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40x_message_sent_count": 1}), "Phase 40X count 0 required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase41_actual_reply_default_blocked": False}), "Phase 41 default block required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase41_message_sent_count": 1}), "Phase 41 count 0 required")


def test_forbidden_behavior_sentinel_phase41b_45a_negative_fixtures() -> None:
    for key in (
        "phase41b_ready_for_manual_private_test_reply_one_shot",
        "phase41b_actual_runtime_executed",
        "phase41b_actual_reply_send_executed",
        "phase41b_discord_api_send_called",
        "phase41b_discord_message_sent",
        "phase41b_llm_api_called",
        "phase41b_rag_called",
        "phase41b_embedding_api_called",
        "phase41b_external_execution",
        "phase41c_discord_api_send_called_during_phase41c",
        "phase41c_discord_message_sent_during_phase41c",
        "phase41c_ready_for_repeat_send",
        "phase42_actual_runtime_executed",
        "phase42_actual_supervised_session_executed",
        "phase42_manual_gate_open",
        "phase42_ready_for_manual_supervised_session",
        "phase42_ready_for_phase41b_repeat_send",
        "phase42_discord_api_send_called",
        "phase42_llm_called",
        "phase42_rag_called",
        "phase42_external_execution",
        "phase42_discord_message_sent",
        "phase43_phase42_manual_gate_open",
        "phase43_ready_for_phase42_actual_supervised_session",
        "phase44_actual_llm_api_call",
        "phase44_llm_api_call_attempted",
        "phase44_discord_message_sent",
        "phase45_actual_llm_api_call",
        "phase45_actual_llm_api_call_attempted",
        "phase45_actual_llm_api_called",
        "phase45_llm_api_call_attempted",
        "phase45_discord_message_sent",
        "phase46_raw_output_included",
        "phase46_full_content_included",
        "phase46_ready_for_retry",
        "phase46_automatic_retry_allowed",
        "phase46_repeat_phase45_call_allowed",
        "phase46_llm_api_call_attempted",
        "phase46_llm_api_called",
        "phase46_discord_api_send_called",
        "phase46_discord_message_sent",
        "phase46_rag_called",
        "phase46_embedding_api_called",
        "phase46_vector_index_created",
        "phase46_external_execution",
        "phase47_automatic_retry_allowed",
        "phase47_automatic_send_allowed",
        "phase47_raw_output_included",
        "phase47_full_content_included",
        "phase47_retry_execution_available",
        "phase47_retry_gate_implemented",
        "phase47_repeat_phase45_call_allowed",
        "phase47_llm_api_call_attempted",
        "phase47_llm_api_called",
        "phase47_additional_llm_api_call",
        "phase47_discord_api_send_called",
        "phase47_discord_message_sent",
        "phase47_rag_called",
        "phase47_embedding_api_called",
        "phase47_vector_index_created",
        "phase47_external_execution",
        "phase47_ready_for_phase48_retry_manual_gate_design",
        "phase47_ready_for_phase48_discord_send_review_gate_design",
    ):
        assert_raises(lambda selected=key: build_forbidden_behavior_sentinel({selected: True}), f"{key} should fail")
    build_forbidden_behavior_sentinel({"phase45_ready_for_actual_llm_one_shot_manual_gate": True, "phase45_ready_for_actual_llm_one_shot_call": True})
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase45_llm_api_call_count": 1}), "45 LLM count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase45_actual_llm_call_closeout_available": False}), "45 closeout required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase45_actual_llm_call_count": 2}), "45 historical count exactly one")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase45_ready_for_repeat_llm_call": True}), "45 repeat locked")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase45_output_safety_blocked": False}), "45 output blocked required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase45_llm_response_packet_created": True}), "45 packet blocked")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase45_closeout_discord_message_sent": True}), "45 closeout no Discord")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase46_blocked_llm_output_review_available": False}), "46 review required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase46_retry_requires_new_manual_gate": False}), "46 manual gate required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase46_discord_send_remains_disabled": False}), "46 Discord disabled")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_human_review_required": False}), "47 human review required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_phase45_llm_call_count": 2}), "47 historical count exactly one")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_phase45_repeat_llm_call_forbidden": False}), "47 repeat forbidden")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_blocked_output_auto_retry_forbidden": False}), "47 auto retry forbidden")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_blocked_output_auto_discord_send_forbidden": False}), "47 auto send forbidden")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_raw_output_dump_forbidden": False}), "47 raw dump forbidden")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_manual_retry_requires_new_phase": False}), "47 new phase required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_manual_retry_requires_new_approval_phrase": False}), "47 new phrase required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase47_discord_send_remains_disabled": False}), "47 Discord disabled")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase41b_message_sent_count": 1}), "41B count 0")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase41c_message_sent_count": 0}), "41C count 1")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase41c_sent_scope": "none"}), "41C private scope")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase41c_repeat_send_blocked": False}), "41C repeat locked")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase44_fake_output_schema_valid": False}), "44 fake schema valid")


def test_forbidden_behavior_sentinel_post_llm_call_fixtures() -> None:
    ok = build_forbidden_behavior_sentinel({"post_llm_call_sentinel": True})
    assert_true(ok["total_phase36_llm_call_count"] == 1, "Post LLM count")
    assert_true(ok["total_phase36_discord_message_sent_count"] == 0, "Post Discord count")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"post_llm_call_sentinel": True, "total_phase36_llm_call_count": 2}), "LLM count >1 should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"post_llm_call_sentinel": True, "total_phase36_discord_message_sent_count": 1}), "Discord count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"post_llm_call_sentinel": True, "phase36_discord_message_sent": True}), "Discord sent should fail")


def test_forbidden_behavior_sentinel_no_sensitive_values() -> None:
    text = json.dumps(build_forbidden_behavior_sentinel(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_forbidden_behavior_sentinel_markdown() -> None:
    assert_true("Forbidden Behavior Sentinel" in render_forbidden_behavior_sentinel_markdown(build_forbidden_behavior_sentinel()), "Markdown")


def main() -> int:
    tests = [
        test_forbidden_behavior_sentinel_success_fixture,
        test_forbidden_behavior_sentinel_flags_false,
        test_forbidden_behavior_sentinel_negative_fixtures,
        test_forbidden_behavior_sentinel_actual_message_count_fixture,
        test_forbidden_behavior_sentinel_phase41b_45a_negative_fixtures,
        test_forbidden_behavior_sentinel_post_llm_call_fixtures,
        test_forbidden_behavior_sentinel_no_sensitive_values,
        test_forbidden_behavior_sentinel_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All forbidden behavior sentinel tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
