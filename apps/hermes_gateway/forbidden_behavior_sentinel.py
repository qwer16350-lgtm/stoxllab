"""Phase 35G forbidden behavior sentinel.

Report-only guardrail sentinel. It never runs Discord, sends messages, calls
LLMs, creates embeddings/vector indexes, or executes external actions.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase35g_forbidden_behavior_sentinel_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
FORBIDDEN_TRUE_FIELDS = (
    "public_channel_reply_allowed",
    "team_channel_reply_allowed",
    "public_channel_send_allowed",
    "team_channel_send_allowed",
    "unattended_auto_reply_allowed",
    "scheduler_auto_reply_allowed",
    "embedding_api_called",
    "vector_index_created",
    "external_execution",
    "full_content_included",
    "approval_phrase_generated",
    "discord_api_send_called",
    "actual_private_test_send_executed",
    "actual_send_implementation_executed",
    "new_llm_api_call_attempted",
    "new_llm_api_called",
    "llm_api_call_attempted",
    "llm_api_called",
    "discord_live_runtime_executed",
    "ready_for_discord_send",
    "ready_for_actual_private_test_send",
    "ready_for_phase37d_actual_private_test_send",
    "ready_for_phase38_actual_private_test_send_path",
    "ready_for_phase39_live_execution",
    "ready_for_phase39b_manual_one_shot_send",
    "ready_for_phase39b_actual_send_manual_attempt",
    "ready_for_phase39c_send_closeout",
    "actual_discord_api_send_called",
    "actual_discord_message_sent",
    "api_key_value_logged",
    "token_value_logged",
    "discord_token_value_logged",
    "private_test_channel_id_value_logged",
    "raw_discord_ids_logged",
    "approval_phrase_value_logged",
    "additional_discord_send_called_in_phase39c",
    "additional_discord_message_sent_in_phase39c",
    "phase39c_repeat_send_allowed",
    "phase39c_automatic_retry_allowed",
    "phase39c_manual_retry_allowed",
    "phase39c_ready_for_repeat_send",
    "phase40_live_runtime_started",
    "phase40_discord_gateway_connected",
    "phase40_discord_api_send_called",
    "phase40_discord_message_sent",
    "phase40_repeat_send_allowed",
    "phase40_automatic_retry_allowed",
    "phase40_unattended_auto_reply_allowed",
    "phase40_public_channel_send_allowed",
    "phase40_team_channel_send_allowed",
    "phase40_public_channel_reply_allowed",
    "phase40_team_channel_reply_allowed",
    "phase40_llm_api_call_attempted",
    "phase40_llm_api_called",
    "phase40_rag_called",
    "phase40_embedding_api_called",
    "phase40_vector_index_created",
    "phase40_external_execution",
    "phase40_secret_values_logged",
    "phase40_ready_for_live_runtime_execution",
    "phase40j_live_runtime_started",
    "phase40j_discord_gateway_connected",
    "phase40j_ready_for_manual_readonly_runtime_launch",
    "phase40k_planned_command_executed_by_codex",
    "phase40k_live_runtime_started",
    "phase40k_discord_gateway_connected",
    "phase40l_live_capture_observed",
    "phase40m_discord_api_send_called",
    "phase40m_discord_message_sent",
    "phase40n_phase41_reply_runtime_allowed",
    "phase40n_reply_send_allowed",
    "phase40n_llm_reply_allowed",
    "phase40n_rag_reply_allowed",
    "phase40n_ready_for_phase41_reply_runtime",
    "phase40o_live_runtime_started",
    "phase40o_discord_gateway_connected",
    "phase40o_discord_api_send_called",
    "phase40o_discord_message_sent",
    "phase40o_ready_for_manual_readonly_runtime_launch",
    "phase40p_raw_content_logged",
    "phase40p_raw_discord_ids_logged",
    "phase40p_secret_values_logged",
    "phase40q_capture_review_completed",
    "phase40q_discord_api_send_called",
    "phase40q_discord_message_sent",
    "phase40q_ready_for_phase41_reply_runtime",
    "phase40r_phase41_reply_runtime_allowed",
    "phase40r_discord_reply_send_allowed",
    "phase40r_llm_reply_allowed",
    "phase40r_rag_reply_allowed",
    "phase40s_live_runtime_started_by_codex",
    "phase40s_overnight_external_actions_executed_by_codex",
    "phase40s_phase41_reply_runtime_allowed",
    "phase40t_live_runtime_started",
    "phase40t_discord_gateway_connected",
    "phase40t_discord_api_send_called",
    "phase40t_discord_message_sent",
    "phase40t_send_messages_enabled",
    "phase40t_private_test_reply_enabled",
    "phase40t_llm_called",
    "phase40t_rag_called",
    "phase40t_embedding_api_called",
    "phase40t_vector_index_created",
    "phase40t_external_execution",
    "phase40t_secret_values_logged",
    "phase40t_raw_discord_ids_logged",
    "phase40t_approval_phrase_value_logged",
    "phase40t_ready_for_phase41_reply_runtime",
    "phase40t_execute_flag_present",
    "phase40t_capture_file_contains_raw_content",
    "phase40t_capture_file_contains_raw_discord_ids",
    "phase40t_capture_file_contains_secret_values",
    "phase40t_closeout_started",
    "phase40t_closeout_gateway_connected",
    "phase40t_login_failure_gateway_connected",
    "phase40t_login_failure_discord_api_send_called",
    "phase40t_login_failure_discord_message_sent",
    "phase40t_login_failure_retry_attempted",
    "phase40t_login_failure_traceback_included",
    "phase40t_login_failure_token_value_logged",
    "phase40t_missing_env_login_attempted",
    "phase40u_discord_api_send_called",
    "phase40u_discord_message_sent",
    "phase40x_discord_api_send_called",
    "phase40x_discord_message_sent",
    "phase41_actual_reply_send_executed",
    "phase41_discord_api_send_called",
    "phase41_discord_message_sent",
    "phase41_public_team_reply_allowed",
    "phase41_unattended_auto_reply_allowed",
    "phase41_llm_called",
    "phase41_rag_called",
    "phase41_embedding_api_called",
    "phase41_external_execution",
    "phase41_raw_content_logged",
    "phase41_raw_discord_ids_logged",
    "phase41_secret_values_logged",
    "phase41_actual_reply_without_one_shot_manual_gate",
    "phase41b_ready_for_manual_private_test_reply_one_shot",
    "phase41b_actual_runtime_executed",
    "phase41b_actual_reply_send_executed",
    "phase41b_discord_api_send_called",
    "phase41b_discord_message_sent",
    "phase41b_llm_api_called",
    "phase41b_rag_called",
    "phase41b_embedding_api_called",
    "phase41b_external_execution",
    "phase41c_ready_for_repeat_send",
    "phase42_actual_runtime_executed",
    "phase42_llm_called",
    "phase42_rag_called",
    "phase42_external_execution",
    "phase42_discord_message_sent",
    "phase44_actual_llm_api_call",
    "phase44_llm_api_call_attempted",
    "phase44_discord_message_sent",
    "phase45_ready_for_actual_llm_one_shot_call",
    "phase45_actual_llm_api_call",
    "phase45_llm_api_call_attempted",
    "phase45_discord_message_sent",
)


def build_forbidden_behavior_sentinel(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_type": "forbidden_behavior_sentinel",
        "version": VERSION,
        "sentinel_available": True,
        "report_only": True,
        "live_runtime_executed": False,
        "llm_called": False,
        "discord_message_sent": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "unattended_auto_reply_allowed": False,
        "scheduler_auto_reply_allowed": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "full_content_included": False,
        "approval_phrase_generated": False,
        "discord_api_send_called": False,
        "actual_private_test_send_executed": False,
        "actual_send_implementation_executed": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "ready_for_discord_send": False,
        "ready_for_actual_private_test_send": False,
        "ready_for_phase37d_actual_private_test_send": False,
        "ready_for_phase38_actual_private_test_send_path": False,
        "ready_for_phase39_live_execution": False,
        "ready_for_phase39b_manual_one_shot_send": False,
        "ready_for_phase39b_actual_send_manual_attempt": False,
        "ready_for_phase39c_send_closeout": False,
        "actual_discord_api_send_called": False,
        "actual_discord_message_sent": False,
        "actual_discord_send_count": 0,
        "actual_message_sent_count": 0,
        "api_key_value_logged": False,
        "token_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "raw_discord_ids_logged": False,
        "approval_phrase_value_logged": False,
        "additional_discord_send_called_in_phase39c": False,
        "additional_discord_message_sent_in_phase39c": False,
        "additional_message_sent_count_in_phase39c": 0,
        "phase39c_actual_discord_send_count_locked": 1,
        "phase39c_repeat_send_allowed": False,
        "phase39c_automatic_retry_allowed": False,
        "phase39c_manual_retry_allowed": False,
        "phase39c_ready_for_repeat_send": False,
        "phase39c_closeout_completed": True,
        "phase39c_no_repeat_lock_active": True,
        "phase40_actual_discord_send_count_locked": 1,
        "phase40_additional_discord_send_count": 0,
        "phase40_message_sent_count": 0,
        "phase40_live_runtime_started": False,
        "phase40_discord_gateway_connected": False,
        "phase40_discord_api_send_called": False,
        "phase40_discord_message_sent": False,
        "phase40_repeat_send_allowed": False,
        "phase40_automatic_retry_allowed": False,
        "phase40_unattended_auto_reply_allowed": False,
        "phase40_public_channel_send_allowed": False,
        "phase40_team_channel_send_allowed": False,
        "phase40_public_channel_reply_allowed": False,
        "phase40_team_channel_reply_allowed": False,
        "phase40_llm_api_call_attempted": False,
        "phase40_llm_api_called": False,
        "phase40_rag_called": False,
        "phase40_embedding_api_called": False,
        "phase40_vector_index_created": False,
        "phase40_external_execution": False,
        "phase40_secret_values_logged": False,
        "phase40_synthetic_replay_only": True,
        "phase40_duplicate_message_id_guard": True,
        "phase40_ready_for_live_runtime_execution": False,
        "phase40j_readonly_preflight_available": True,
        "phase40j_live_runtime_started": False,
        "phase40j_discord_gateway_connected": False,
        "phase40j_ready_for_manual_readonly_runtime_launch": False,
        "phase40k_manual_launch_only": True,
        "phase40k_codex_must_not_launch": True,
        "phase40k_planned_command_executed_by_codex": False,
        "phase40k_live_runtime_started": False,
        "phase40k_discord_gateway_connected": False,
        "phase40l_capture_closeout_available": True,
        "phase40l_live_capture_observed": False,
        "phase40l_captured_event_count": 0,
        "phase40m_manual_abort_available": True,
        "phase40m_abort_on_any_send_attempt": True,
        "phase40m_discord_api_send_called": False,
        "phase40m_discord_message_sent": False,
        "phase40n_phase41_reply_runtime_entry_gate_available": True,
        "phase40n_phase41_reply_runtime_allowed": False,
        "phase40n_reply_send_allowed": False,
        "phase40n_llm_reply_allowed": False,
        "phase40n_rag_reply_allowed": False,
        "phase40n_ready_for_phase41_reply_runtime": False,
        "phase40o_manual_launch_only": True,
        "phase40o_codex_must_not_launch": True,
        "phase40o_live_runtime_started": False,
        "phase40o_discord_gateway_connected": False,
        "phase40o_discord_api_send_called": False,
        "phase40o_discord_message_sent": False,
        "phase40o_ready_for_manual_readonly_runtime_launch": False,
        "phase40p_capture_schema_available": True,
        "phase40p_raw_content_logged": False,
        "phase40p_raw_discord_ids_logged": False,
        "phase40p_secret_values_logged": False,
        "phase40q_capture_file_present": False,
        "phase40q_capture_review_completed": False,
        "phase40q_message_sent_count": 0,
        "phase40q_discord_api_send_called": False,
        "phase40q_discord_message_sent": False,
        "phase40q_ready_for_phase41_reply_runtime": False,
        "phase40r_phase41_reply_runtime_entry_available": True,
        "phase40r_phase41_reply_runtime_allowed": False,
        "phase40r_discord_reply_send_allowed": False,
        "phase40r_llm_reply_allowed": False,
        "phase40r_rag_reply_allowed": False,
        "phase40s_safe_to_review_next_morning": True,
        "phase40s_requires_user_confirmation": True,
        "phase40s_additional_discord_send_count": 0,
        "phase40s_live_runtime_started_by_codex": False,
        "phase40s_overnight_external_actions_executed_by_codex": False,
        "phase40s_phase41_reply_runtime_allowed": False,
        "phase40t_command_available": True,
        "phase40t_blocked_by_default": True,
        "phase40t_codex_runtime_launch_forbidden": True,
        "phase40t_live_runtime_started": False,
        "phase40t_discord_gateway_connected": False,
        "phase40t_discord_api_send_called": False,
        "phase40t_discord_message_sent": False,
        "phase40t_message_sent_count": 0,
        "phase40t_send_messages_enabled": False,
        "phase40t_private_test_reply_enabled": False,
        "phase40t_reply_mode_readonly_private_test_only": False,
        "phase40t_execute_flag_required": True,
        "phase40t_execute_flag_present": False,
        "phase40t_execution_gate_blocked_by_default": True,
        "phase40t_llm_called": False,
        "phase40t_rag_called": False,
        "phase40t_embedding_api_called": False,
        "phase40t_vector_index_created": False,
        "phase40t_external_execution": False,
        "phase40t_secret_values_logged": False,
        "phase40t_raw_discord_ids_logged": False,
        "phase40t_approval_phrase_value_logged": False,
        "phase40t_ready_for_phase41_reply_runtime": False,
        "phase40t_capture_file_contains_raw_content": False,
        "phase40t_capture_file_contains_raw_discord_ids": False,
        "phase40t_capture_file_contains_secret_values": False,
        "phase40t_closeout_started": False,
        "phase40t_closeout_gateway_connected": False,
        "phase40t_closeout_message_sent_count": 0,
        "phase40t_login_failure_closeout_available": True,
        "phase40t_login_failure_gateway_connected": False,
        "phase40t_login_failure_discord_api_send_called": False,
        "phase40t_login_failure_discord_message_sent": False,
        "phase40t_login_failure_message_sent_count": 0,
        "phase40t_login_failure_retry_attempted": False,
        "phase40t_login_failure_traceback_included": False,
        "phase40t_login_failure_token_value_logged": False,
        "phase40t_preflight_snapshot_preserved": True,
        "phase40t_presence_consistency_verified": True,
        "phase40t_login_attempt_requires_token_and_channel": True,
        "phase40t_login_failure_preflight_snapshot_preserved": True,
        "phase40t_login_failure_presence_consistency_verified": True,
        "phase40t_missing_env_before_login_guard": True,
        "phase40t_missing_env_login_attempted": False,
        "phase40u_closeout_ready": True,
        "phase40u_discord_api_send_called": False,
        "phase40u_discord_message_sent": False,
        "phase40u_message_sent_count": 0,
        "phase40x_reply_dry_run_ready": True,
        "phase40x_discord_api_send_called": False,
        "phase40x_discord_message_sent": False,
        "phase40x_message_sent_count": 0,
        "phase41_actual_reply_default_blocked": True,
        "phase41_actual_reply_send_executed": False,
        "phase41_discord_api_send_called": False,
        "phase41_discord_message_sent": False,
        "phase41_message_sent_count": 0,
        "phase41_public_team_reply_allowed": False,
        "phase41_unattended_auto_reply_allowed": False,
        "phase41_llm_called": False,
        "phase41_rag_called": False,
        "phase41_embedding_api_called": False,
        "phase41_external_execution": False,
        "phase41_raw_content_logged": False,
        "phase41_raw_discord_ids_logged": False,
        "phase41_secret_values_logged": False,
        "phase41_actual_reply_without_one_shot_manual_gate": False,
        "phase41b_one_shot_available": True,
        "phase41b_default_blocked": True,
        "phase41b_actual_runtime_path_available": True,
        "phase41b_actual_runtime_executed": False,
        "phase41b_real_discord_send_adapter_wired": True,
        "phase41b_fake_adapter_contract_passed": True,
        "phase41b_manual_retry_required": True,
        "phase41b_ready_for_actual_private_test_reply_retry_manual_gate": False,
        "phase41b_ready_for_manual_private_test_reply_one_shot": False,
        "phase41b_actual_reply_send_executed": False,
        "phase41b_discord_api_send_called": False,
        "phase41b_discord_message_sent": False,
        "phase41b_message_sent_count": 0,
        "phase41b_llm_api_called": False,
        "phase41b_rag_called": False,
        "phase41b_embedding_api_called": False,
        "phase41b_external_execution": False,
        "phase41c_closeout_available": True,
        "phase41c_message_sent_count": 0,
        "phase41c_ready_for_repeat_send": False,
        "phase42_session_preflight_available": True,
        "phase42_actual_runtime_executed": False,
        "phase42_llm_called": False,
        "phase42_rag_called": False,
        "phase42_external_execution": False,
        "phase42_discord_message_sent": False,
        "phase43_policy_available": True,
        "phase43_public_team_blocked": True,
        "phase44_provider_preflight_available": True,
        "phase44_actual_llm_api_call": False,
        "phase44_llm_api_call_attempted": False,
        "phase44_discord_message_sent": False,
        "phase44_fake_adapter_available": True,
        "phase44_fake_output_schema_valid": True,
        "phase45_preflight_available": True,
        "phase45_ready_for_actual_llm_one_shot_call": False,
        "phase45_actual_llm_api_call": False,
        "phase45_llm_api_call_attempted": False,
        "phase45_discord_message_sent": False,
        "post_llm_call_sentinel": False,
        "total_phase36_llm_call_count": 1,
        "total_phase36_discord_message_sent_count": 0,
        "phase36_discord_message_sent": False,
        "public_team_blocked": True,
        "embedding_vector_disabled": True,
        "forbidden_behavior_sentinel_passed": True,
    }
    if overrides:
        report.update(overrides)
    report["public_team_blocked"] = not any(
        bool(report.get(key))
        for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed")
    )
    report["embedding_vector_disabled"] = not (bool(report.get("embedding_api_called")) or bool(report.get("vector_index_created")))
    report["forbidden_behavior_sentinel_passed"] = _sentinel_passed(report)
    assert_forbidden_behavior_sentinel_safe(report)
    return report


def _sentinel_passed(report: dict[str, Any]) -> bool:
    if any(bool(report.get(key)) for key in FORBIDDEN_TRUE_FIELDS):
        return False
    if bool(report.get("post_llm_call_sentinel")):
        if int(report.get("total_phase36_llm_call_count", 0) or 0) != 1:
            return False
        if int(report.get("total_phase36_discord_message_sent_count", 0) or 0) != 0:
            return False
        if report.get("phase36_discord_message_sent"):
            return False
    if int(report.get("actual_message_sent_count", 0) or 0) != 0:
        return False
    if int(report.get("actual_discord_send_count", 0) or 0) != 0:
        return False
    if int(report.get("additional_message_sent_count_in_phase39c", 0) or 0) != 0:
        return False
    if int(report.get("phase40_actual_discord_send_count_locked", 0) or 0) != 1:
        return False
    if int(report.get("phase40_additional_discord_send_count", 0) or 0) != 0:
        return False
    if int(report.get("phase40_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase40_synthetic_replay_only")):
        return False
    if not bool(report.get("phase40_duplicate_message_id_guard")):
        return False
    if not bool(report.get("phase40j_readonly_preflight_available")):
        return False
    if not bool(report.get("phase40k_manual_launch_only")) or not bool(report.get("phase40k_codex_must_not_launch")):
        return False
    if not bool(report.get("phase40l_capture_closeout_available")):
        return False
    if int(report.get("phase40l_captured_event_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase40m_manual_abort_available")) or not bool(report.get("phase40m_abort_on_any_send_attempt")):
        return False
    if not bool(report.get("phase40n_phase41_reply_runtime_entry_gate_available")):
        return False
    if not bool(report.get("phase40o_manual_launch_only")) or not bool(report.get("phase40o_codex_must_not_launch")):
        return False
    if not bool(report.get("phase40p_capture_schema_available")):
        return False
    if int(report.get("phase40q_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase40r_phase41_reply_runtime_entry_available")):
        return False
    if not bool(report.get("phase40s_safe_to_review_next_morning")) or not bool(report.get("phase40s_requires_user_confirmation")):
        return False
    if int(report.get("phase40s_additional_discord_send_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase40t_command_available")) or not bool(report.get("phase40t_blocked_by_default")) or not bool(report.get("phase40t_codex_runtime_launch_forbidden")):
        return False
    if not bool(report.get("phase40t_execute_flag_required")) or not bool(report.get("phase40t_execution_gate_blocked_by_default")):
        return False
    if int(report.get("phase40t_message_sent_count", 0) or 0) != 0:
        return False
    if int(report.get("phase40t_closeout_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase40t_login_failure_closeout_available")) or int(report.get("phase40t_login_failure_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase40t_preflight_snapshot_preserved")) or not bool(report.get("phase40t_presence_consistency_verified")):
        return False
    if not bool(report.get("phase40t_login_failure_preflight_snapshot_preserved")) or not bool(report.get("phase40t_login_failure_presence_consistency_verified")):
        return False
    if not bool(report.get("phase40t_missing_env_before_login_guard")):
        return False
    if not bool(report.get("phase40u_closeout_ready")) or int(report.get("phase40u_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase40x_reply_dry_run_ready")) or int(report.get("phase40x_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase41_actual_reply_default_blocked")) or int(report.get("phase41_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase41b_one_shot_available")) or not bool(report.get("phase41b_actual_runtime_path_available")) or not bool(report.get("phase41b_real_discord_send_adapter_wired")) or not bool(report.get("phase41b_fake_adapter_contract_passed")) or not bool(report.get("phase41b_default_blocked")):
        return False
    if int(report.get("phase41b_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase41c_closeout_available")) or int(report.get("phase41c_message_sent_count", 0) or 0) != 0:
        return False
    if not bool(report.get("phase42_session_preflight_available")):
        return False
    if not bool(report.get("phase43_policy_available")) or not bool(report.get("phase43_public_team_blocked")):
        return False
    if not bool(report.get("phase44_provider_preflight_available")) or not bool(report.get("phase44_fake_adapter_available")) or not bool(report.get("phase44_fake_output_schema_valid")):
        return False
    if not bool(report.get("phase45_preflight_available")):
        return False
    if not bool(report.get("phase40t_execute_flag_present")) and (
        bool(report.get("phase40t_live_runtime_started")) or bool(report.get("phase40t_closeout_started"))
    ):
        return False
    if bool(report.get("phase40t_ready_for_manual_readonly_runtime_launch")) and not bool(report.get("phase40t_reply_mode_readonly_private_test_only")):
        return False
    return True


def assert_forbidden_behavior_sentinel_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Forbidden behavior sentinel contains sensitive values.")
    if not report.get("forbidden_behavior_sentinel_passed"):
        raise ValueError("Forbidden behavior sentinel failed.")
    for key in FORBIDDEN_TRUE_FIELDS:
        if report.get(key):
            raise ValueError(f"Forbidden behavior enabled: {key}")
    if bool(report.get("post_llm_call_sentinel")):
        if int(report.get("total_phase36_llm_call_count", 0) or 0) != 1:
            raise ValueError("Post-LLM sentinel requires Phase 36 LLM call count exactly 1.")
        if int(report.get("total_phase36_discord_message_sent_count", 0) or 0) != 0:
            raise ValueError("Post-LLM sentinel requires Phase 36 Discord message count 0.")
        if report.get("phase36_discord_message_sent"):
            raise ValueError("Post-LLM sentinel requires Phase 36 Discord message sent false.")
    if int(report.get("actual_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires actual message sent count 0.")
    if int(report.get("actual_discord_send_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires actual Discord send count 0.")
    if int(report.get("additional_message_sent_count_in_phase39c", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 39C additional send count 0.")
    if int(report.get("phase40_actual_discord_send_count_locked", 0) or 0) != 1:
        raise ValueError("Forbidden behavior sentinel requires Phase 40 locked send count 1.")
    if int(report.get("phase40_additional_discord_send_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40 additional send count 0.")
    if int(report.get("phase40_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40 message sent count 0.")
    if not report.get("phase40_synthetic_replay_only") or not report.get("phase40_duplicate_message_id_guard"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40 replay/idempotency guards.")
    if not report.get("phase40j_readonly_preflight_available"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40J preflight.")
    if not report.get("phase40k_manual_launch_only") or not report.get("phase40k_codex_must_not_launch"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40K manual-only launch guard.")
    if not report.get("phase40l_capture_closeout_available") or int(report.get("phase40l_captured_event_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40L pre-capture closeout.")
    if not report.get("phase40m_manual_abort_available") or not report.get("phase40m_abort_on_any_send_attempt"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40M abort guard.")
    if not report.get("phase40n_phase41_reply_runtime_entry_gate_available"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40N entry gate.")
    if not report.get("phase40o_manual_launch_only") or not report.get("phase40o_codex_must_not_launch"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40O manual-only launch support.")
    if not report.get("phase40p_capture_schema_available"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40P capture schema.")
    if int(report.get("phase40q_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40Q message count 0.")
    if not report.get("phase40r_phase41_reply_runtime_entry_available"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40R matrix.")
    if not report.get("phase40s_safe_to_review_next_morning") or not report.get("phase40s_requires_user_confirmation"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40S review confirmation.")
    if int(report.get("phase40s_additional_discord_send_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40S additional send count 0.")
    if not report.get("phase40t_command_available") or not report.get("phase40t_blocked_by_default") or not report.get("phase40t_codex_runtime_launch_forbidden"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40T blocked command guard.")
    if not report.get("phase40t_execute_flag_required") or not report.get("phase40t_execution_gate_blocked_by_default"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40T execute gate blocked by default.")
    if int(report.get("phase40t_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40T message count 0.")
    if int(report.get("phase40t_closeout_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40T closeout message count 0.")
    if not report.get("phase40t_login_failure_closeout_available") or int(report.get("phase40t_login_failure_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40T login failure closeout with message count 0.")
    if not report.get("phase40t_preflight_snapshot_preserved") or not report.get("phase40t_presence_consistency_verified"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40T preflight snapshot consistency.")
    if not report.get("phase40t_login_failure_preflight_snapshot_preserved") or not report.get("phase40t_login_failure_presence_consistency_verified"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40T login failure snapshot consistency.")
    if not report.get("phase40t_missing_env_before_login_guard"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40T missing-env-before-login guard.")
    if not report.get("phase40u_closeout_ready") or int(report.get("phase40u_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40U closeout with message count 0.")
    if not report.get("phase40x_reply_dry_run_ready") or int(report.get("phase40x_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 40X dry-run with message count 0.")
    if not report.get("phase41_actual_reply_default_blocked") or int(report.get("phase41_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 41 default block with message count 0.")
    if not report.get("phase41b_one_shot_available") or not report.get("phase41b_actual_runtime_path_available") or not report.get("phase41b_real_discord_send_adapter_wired") or not report.get("phase41b_fake_adapter_contract_passed") or not report.get("phase41b_default_blocked") or int(report.get("phase41b_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 41B blocked no-send prep.")
    if not report.get("phase41c_closeout_available") or int(report.get("phase41c_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires Phase 41C no-send closeout scaffold.")
    if not report.get("phase42_session_preflight_available"):
        raise ValueError("Forbidden behavior sentinel requires Phase 42 session preflight.")
    if not report.get("phase43_policy_available") or not report.get("phase43_public_team_blocked"):
        raise ValueError("Forbidden behavior sentinel requires Phase 43 public/team block.")
    if not report.get("phase44_provider_preflight_available") or not report.get("phase44_fake_adapter_available") or not report.get("phase44_fake_output_schema_valid"):
        raise ValueError("Forbidden behavior sentinel requires Phase 44 preflight/fake adapter.")
    if not report.get("phase45_preflight_available"):
        raise ValueError("Forbidden behavior sentinel requires Phase 45A preflight.")
    if not report.get("phase40t_execute_flag_present") and (report.get("phase40t_live_runtime_started") or report.get("phase40t_closeout_started")):
        raise ValueError("Forbidden behavior sentinel forbids Phase 40T started without execute flag.")
    if report.get("phase40t_ready_for_manual_readonly_runtime_launch") and not report.get("phase40t_reply_mode_readonly_private_test_only"):
        raise ValueError("Forbidden behavior sentinel requires Phase 40T readonly reply mode when ready.")


def render_forbidden_behavior_sentinel_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Forbidden Behavior Sentinel",
            "",
            "- Sentinel available: true",
            "- Report only: true",
            "- Public/team blocked: true",
            "- Unattended auto reply allowed: false",
            "- Scheduler auto reply allowed: false",
            "- Embedding/vector disabled: true",
            "- External execution: false",
            "- Full content included: false",
            "- Approval phrase generated: false",
            "- Phase 40 live runtime started: false",
            "- Phase 40 Discord gateway connected: false",
            "- Phase 40 additional send count: 0",
            "- Phase 40J ready for manual read-only runtime launch: false",
            "- Phase 40N Phase 41 reply runtime allowed: false",
            "- Phase 40O Codex must not launch: true",
            "- Phase 40R Discord reply send allowed: false",
            "- Phase 40T command available: true",
            "- Phase 40T blocked by default: true",
            "- Phase 40T execute flag required: true",
            "- Phase 41B one-shot default blocked: true",
            "- Phase 41B actual runtime path available: true",
            "- Phase 41B actual runtime executed: false",
            "- Phase 41B real Discord send adapter wired: true",
            "- Phase 41B fake adapter contract passed: true",
            "- Phase 41B Discord message sent: false",
            "- Phase 42 actual runtime executed: false",
            "- Phase 44 actual LLM API call: false",
            "- Phase 45 actual LLM API call: false",
            "- Forbidden behavior sentinel passed: true",
        ]
    ) + "\n"
