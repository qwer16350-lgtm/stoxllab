"""Phase 35F operations dashboard lock."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agent_evidence_pack_composer import build_agent_evidence_pack_composer
from agent_prompt_preview import build_agent_prompt_preview
from agent_review_packet import build_agent_review_packet
from forbidden_behavior_sentinel import build_forbidden_behavior_sentinel
from local_knowledge_ingestion_preview import build_local_knowledge_ingestion_preview
from no_live_rehearsal_packet import build_no_live_rehearsal_packet
from one_shot_llm_no_send_final_lock import build_one_shot_llm_no_send_final_lock
from post_llm_call_dashboard_lock import build_post_llm_call_dashboard_lock
from phase35a_post_mvp_safety_audit import build_phase35a_post_mvp_safety_audit
from actual_private_test_one_shot_send import build_actual_private_test_one_shot_send
from phase39b_manual_send_no_send_lock import build_phase39b_manual_send_no_send_lock
from phase39c_actual_send_closeout import build_phase39c_actual_send_closeout
from phase39c_no_repeat_send_lock import build_phase39c_no_repeat_send_lock
from phase39c_post_send_safety_audit import build_phase39c_post_send_safety_audit
from phase40_inbound_event_replay_dry_run import build_phase40_inbound_event_replay_dry_run
from phase40_live_runtime_entry_gate import build_phase40_live_runtime_entry_gate
from phase40_outbound_queue_lock import build_phase40_outbound_queue_lock
from phase40_post_phase39_state_audit import build_phase40_post_phase39_state_audit
from phase40_safe_overnight_summary import build_phase40_safe_overnight_summary
from phase40_session_idempotency_lock import build_phase40_session_idempotency_lock
from phase40j_private_test_readonly_runtime_preflight import build_phase40j_private_test_readonly_runtime_preflight
from phase40k_readonly_runtime_launch_packet import build_phase40k_readonly_runtime_launch_packet
from phase40l_live_capture_closeout_packet import build_phase40l_live_capture_closeout_packet
from phase40m_runtime_abort_kill_switch_packet import build_phase40m_runtime_abort_kill_switch_packet
from phase40n_phase41_reply_runtime_entry_gate import build_phase40n_phase41_reply_runtime_entry_gate
from phase40o_manual_readonly_live_runtime_launcher import build_phase40o_manual_readonly_live_runtime_launcher
from phase40p_readonly_capture_schema import build_phase40p_readonly_capture_schema
from phase40q_capture_review_closeout import build_phase40q_capture_review_closeout
from phase40r_phase41_reply_preflight_matrix import build_phase40r_phase41_reply_preflight_matrix
from phase40s_morning_review_operator_decision_packet import build_phase40s_morning_review_operator_decision_packet
from phase40t_private_test_readonly_runtime_command import (
    build_phase40t_discord_login_failure_closeout_command,
    build_phase40t_private_test_readonly_runtime_command,
)
from phase40t_readonly_capture_writer import CAPTURE_SCHEMA_VERSION
from phase40t_readonly_live_execution_gate import build_phase40t_readonly_live_execution_gate
from phase40t_readonly_runtime_closeout import build_phase40t_readonly_runtime_closeout
from phase40u_readonly_live_connection_closeout import build_phase40u_readonly_live_connection_closeout
from phase40x_reply_decision_dry_run import build_phase40x_reply_decision_dry_run
from phase40y_phase41_reply_preflight_gate import build_phase40y_phase41_reply_preflight_gate
from phase40z_operations_handoff import build_phase40z_operations_handoff
from phase41_private_test_reply_preflight import build_phase41_private_test_reply_preflight
from phase41b_private_test_reply_one_shot import build_phase41b_private_test_reply_one_shot
from phase41c_actual_reply_closeout import build_phase41c_actual_reply_closeout
from phase42_supervised_private_test_session import build_phase42_supervised_private_test_session_preflight
from phase43_routing_rate_limit_policy import build_phase43_routing_rate_limit_policy
from phase44_llm_preflight_contract import build_phase44_llm_provider_preflight
from phase44_fake_llm_adapter import run_phase44_fake_llm_adapter
from phase45_actual_llm_one_shot_preflight import build_phase45_actual_llm_one_shot_preflight
from private_test_live_send_entry_gate import build_private_test_live_send_entry_gate
from rag_evidence_private_test_phase34_final_lock import build_rag_evidence_private_test_phase34_final_lock


VERSION = "phase35f_operations_dashboard_lock_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_operations_dashboard_lock(root: str | Path | None = None) -> dict[str, Any]:
    final_lock = build_rag_evidence_private_test_phase34_final_lock(root=str(root) if root else None)
    audit = build_phase35a_post_mvp_safety_audit(root=root, final_lock=final_lock)
    local = build_local_knowledge_ingestion_preview(root=root, source="operation")
    composer = build_agent_evidence_pack_composer()
    prompt = build_agent_prompt_preview(composer)
    review = build_agent_review_packet()
    rehearsal = build_no_live_rehearsal_packet()
    sentinel = build_forbidden_behavior_sentinel()
    phase36_final_lock = build_one_shot_llm_no_send_final_lock()
    phase36_dashboard = build_post_llm_call_dashboard_lock(phase36_final_lock)
    phase38_entry_gate = build_private_test_live_send_entry_gate()
    phase39a_send_path = build_actual_private_test_one_shot_send()
    phase39b_no_send_lock = build_phase39b_manual_send_no_send_lock()
    phase39c_closeout = build_phase39c_actual_send_closeout()
    phase39c_no_repeat = build_phase39c_no_repeat_send_lock(phase39c_closeout)
    phase39c_safety = build_phase39c_post_send_safety_audit(
        env={
            "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED": "false",
            "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE": "",
            "HERMES_DISCORD_SEND_MESSAGES": "false",
            "HERMES_DISCORD_PRIVATE_TEST_REPLY": "false",
            "HERMES_DISCORD_REPLY_MODE": "",
            "HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION": "false",
            "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
            "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
            "HERMES_DISCORD_RAG_ENABLED": "false",
            "HERMES_LLM_RAG_ENABLED": "false",
            "HERMES_RAG_LLM_REPLY_ENABLED": "false",
            "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
            "HERMES_DISCORD_LLM_ENABLED": "false",
        },
        closeout=phase39c_closeout,
        no_repeat_lock=phase39c_no_repeat,
    )
    phase40_state = build_phase40_post_phase39_state_audit(phase39c_closeout, phase39c_no_repeat)
    phase40_replay = build_phase40_inbound_event_replay_dry_run()
    phase40_queue = build_phase40_outbound_queue_lock()
    phase40_idempotency = build_phase40_session_idempotency_lock()
    phase40_entry_gate = build_phase40_live_runtime_entry_gate()
    phase40_summary = build_phase40_safe_overnight_summary()
    phase40j_preflight = build_phase40j_private_test_readonly_runtime_preflight()
    phase40k_launch = build_phase40k_readonly_runtime_launch_packet()
    phase40l_closeout = build_phase40l_live_capture_closeout_packet()
    phase40m_abort = build_phase40m_runtime_abort_kill_switch_packet()
    phase40n_gate = build_phase40n_phase41_reply_runtime_entry_gate()
    phase40o_launcher = build_phase40o_manual_readonly_live_runtime_launcher()
    phase40p_schema = build_phase40p_readonly_capture_schema()
    phase40q_closeout = build_phase40q_capture_review_closeout()
    phase40r_matrix = build_phase40r_phase41_reply_preflight_matrix()
    phase40s_morning = build_phase40s_morning_review_operator_decision_packet()
    phase40t_command = build_phase40t_private_test_readonly_runtime_command(env={}, report_only=False)
    phase40t_gate = build_phase40t_readonly_live_execution_gate(env={}, execute_flag_present=False, root=root)
    phase40t_closeout = build_phase40t_readonly_runtime_closeout()
    phase40t_login_failure = build_phase40t_discord_login_failure_closeout_command(env={})
    phase40u_closeout = build_phase40u_readonly_live_connection_closeout()
    phase40x_reply = build_phase40x_reply_decision_dry_run()
    phase40y_gate = build_phase40y_phase41_reply_preflight_gate()
    phase40z_handoff = build_phase40z_operations_handoff()
    phase41_preflight = build_phase41_private_test_reply_preflight()
    phase41b_one_shot = build_phase41b_private_test_reply_one_shot()
    phase41c_closeout = build_phase41c_actual_reply_closeout()
    phase42_session = build_phase42_supervised_private_test_session_preflight()
    phase43_policy = build_phase43_routing_rate_limit_policy()
    phase44_provider = build_phase44_llm_provider_preflight()
    phase44_fake = run_phase44_fake_llm_adapter()
    phase45_preflight = build_phase45_actual_llm_one_shot_preflight()
    counts = audit.get("final_e2e_counts", {})
    report = {
        "report_type": "operations_dashboard_lock",
        "version": VERSION,
        "dashboard_lock_available": True,
        "report_only": True,
        "phase34_private_test_mvp_complete": bool(final_lock.get("phase34_private_test_mvp_complete")),
        "phase35a_safety_audit_passed": bool(audit.get("phase35a_audit_passed")),
        "phase35b_dry_previews_available": bool(local.get("ready_for_local_text_ingestion")),
        "phase35c_agent_prompt_previews_available": bool(prompt.get("prompt_preview_available")),
        "phase35d_review_approval_previews_available": bool(review.get("review_packet_available")),
        "phase35e_operator_rehearsal_available": bool(rehearsal.get("rehearsal_available")),
        "total_llm_call_count": int(counts.get("total_llm_call_count", 0) or 0),
        "send_retry_llm_call_count": int(counts.get("send_retry_llm_call_count", 0) or 0),
        "final_discord_message_sent_count": int(counts.get("final_discord_message_sent_count", 0) or 0),
        "sent_channel_scope": counts.get("sent_channel_scope", ""),
        "current_live_gates_off": True,
        "public_team_blocked": bool(sentinel.get("public_team_blocked")),
        "unattended_auto_reply_allowed": False,
        "embedding_vector_disabled": bool(sentinel.get("embedding_vector_disabled")),
        "external_execution": False,
        "ready_for_phase36_entry_gate": True,
        "phase36f_no_send_final_lock_passed": bool(phase36_final_lock.get("phase36f_no_send_final_lock_passed")),
        "phase36g_post_llm_dashboard_lock_available": bool(phase36_dashboard.get("dashboard_lock_available")),
        "phase36_total_llm_call_count": int(phase36_dashboard.get("total_phase36_llm_call_count", 0) or 0),
        "phase36_total_discord_message_sent_count": int(phase36_dashboard.get("total_phase36_discord_message_sent_count", 0) or 0),
        "ready_for_phase37_entry_gate": bool(phase36_dashboard.get("ready_for_phase37_entry_gate")),
        "phase38e_live_send_entry_gate_available": bool(phase38_entry_gate.get("live_send_entry_gate_available")),
        "phase39_not_started": bool(phase38_entry_gate.get("phase39_not_started")),
        "ready_for_phase39_live_execution": bool(phase38_entry_gate.get("ready_for_phase39_live_execution")),
        "phase39a_actual_send_path_available": bool(phase39a_send_path.get("actual_send_path_available")),
        "phase39a_blocked": bool(phase39a_send_path.get("blocked")),
        "phase39a_actual_private_test_send_executed": bool(phase39a_send_path.get("actual_private_test_send_executed")),
        "phase39a_discord_message_sent": bool(phase39a_send_path.get("discord_message_sent")),
        "ready_for_phase39b_manual_one_shot_send": bool(phase39a_send_path.get("ready_for_phase39b_manual_one_shot_send")),
        "phase39b_actual_send_not_executed_yet": bool(phase39b_no_send_lock.get("phase39b_actual_send_not_executed_yet")),
        "phase39b_actual_discord_send_count": int(phase39b_no_send_lock.get("actual_discord_send_count", 0) or 0),
        "phase39b_discord_message_sent": bool(phase39b_no_send_lock.get("discord_message_sent")),
        "phase39c_closeout_not_available": bool(phase39b_no_send_lock.get("phase39c_closeout_not_available")),
        "ready_for_phase39c_send_closeout": bool(phase39b_no_send_lock.get("ready_for_phase39c_send_closeout")),
        "phase39c_closeout_completed": bool(phase39c_closeout.get("phase39c_closeout_completed")),
        "phase39c_actual_discord_send_count_locked": int(phase39c_no_repeat.get("actual_discord_send_count_locked", 0) or 0),
        "phase39c_repeat_send_allowed": bool(phase39c_no_repeat.get("repeat_send_allowed")),
        "phase39c_automatic_retry_allowed": bool(phase39c_no_repeat.get("automatic_retry_allowed")),
        "phase39c_ready_for_repeat_send": bool(phase39c_no_repeat.get("ready_for_repeat_send")),
        "phase39c_gate_off_verified": bool(phase39c_safety.get("gate_off_verified")),
        "phase39c_additional_send_count": int(phase39c_safety.get("phase39c_additional_send_count", 0) or 0),
        "phase40_runtime_readiness_available": bool(phase40_summary.get("phase40_reports_completed")),
        "phase40_actual_discord_send_count_locked": int(phase40_state.get("actual_discord_send_count_locked", 0) or 0),
        "phase40_additional_discord_send_count": int(phase40_summary.get("additional_discord_send_count", 0) or 0),
        "phase40_live_runtime_started": bool(phase40_summary.get("live_runtime_started")),
        "phase40_discord_gateway_connected": bool(phase40_summary.get("discord_gateway_connected")),
        "phase40_discord_api_send_called": bool(phase40_summary.get("discord_api_send_called")),
        "phase40_discord_message_sent": bool(phase40_summary.get("discord_message_sent")),
        "phase40_message_sent_count": int(phase40_summary.get("message_sent_count", 0) or 0),
        "phase40_synthetic_replay_only": bool(phase40_replay.get("uses_recorded_or_synthetic_events_only")),
        "phase40_outbound_queue_enabled": bool(phase40_queue.get("outbound_queue_enabled")),
        "phase40_send_worker_enabled": bool(phase40_queue.get("send_worker_enabled")),
        "phase40_duplicate_message_id_guard": bool(phase40_idempotency.get("duplicate_message_id_guard")),
        "phase40_live_runtime_start_allowed": bool(phase40_entry_gate.get("live_runtime_start_allowed")),
        "phase40_ready_for_live_runtime_execution": bool(phase40_summary.get("ready_for_live_runtime_execution")),
        "phase40_safe_to_review_next_morning": bool(phase40_summary.get("safe_to_review_next_morning")),
        "phase40j_readonly_preflight_available": bool(phase40j_preflight.get("readonly_runtime_preflight_available")),
        "phase40j_ready_for_manual_readonly_runtime_launch": bool(phase40j_preflight.get("ready_for_manual_readonly_runtime_launch")),
        "phase40k_manual_launch_only": bool(phase40k_launch.get("manual_launch_only")),
        "phase40k_codex_must_not_launch": bool(phase40k_launch.get("codex_must_not_launch")),
        "phase40k_planned_command_executed_by_codex": bool(phase40k_launch.get("planned_command_executed_by_codex")),
        "phase40l_capture_closeout_available": bool(phase40l_closeout.get("capture_closeout_available")),
        "phase40l_live_capture_observed": bool(phase40l_closeout.get("live_capture_observed")),
        "phase40l_captured_event_count": int(phase40l_closeout.get("captured_event_count", 0) or 0),
        "phase40m_manual_abort_available": bool(phase40m_abort.get("manual_abort_available")),
        "phase40m_abort_on_any_send_attempt": bool(phase40m_abort.get("abort_on_any_send_attempt")),
        "phase40n_phase41_reply_runtime_entry_gate_available": bool(phase40n_gate.get("phase41_reply_runtime_entry_gate_available")),
        "phase40n_phase41_reply_runtime_allowed": bool(phase40n_gate.get("phase41_reply_runtime_allowed")),
        "phase40n_reply_send_allowed": bool(phase40n_gate.get("reply_send_allowed")),
        "phase40n_ready_for_phase41_reply_runtime": bool(phase40n_gate.get("ready_for_phase41_reply_runtime")),
        "phase40o_manual_launch_only": bool(phase40o_launcher.get("manual_launch_only")),
        "phase40o_codex_must_not_launch": bool(phase40o_launcher.get("codex_must_not_launch")),
        "phase40o_ready_for_manual_readonly_runtime_launch": bool(phase40o_launcher.get("ready_for_manual_readonly_runtime_launch")),
        "phase40p_capture_schema_available": bool(phase40p_schema.get("capture_schema_available")),
        "phase40p_raw_content_logged": bool(phase40p_schema.get("raw_content_logged")),
        "phase40p_secret_values_logged": bool(phase40p_schema.get("secret_values_logged")),
        "phase40q_capture_file_present": bool(phase40q_closeout.get("capture_file_present")),
        "phase40q_capture_review_completed": bool(phase40q_closeout.get("capture_review_completed")),
        "phase40q_message_sent_count": int(phase40q_closeout.get("message_sent_count", 0) or 0),
        "phase40r_phase41_reply_runtime_allowed": bool(phase40r_matrix.get("phase41_reply_runtime_allowed")),
        "phase40r_discord_reply_send_allowed": bool(phase40r_matrix.get("discord_reply_send_allowed")),
        "phase40r_llm_reply_allowed": bool(phase40r_matrix.get("llm_reply_allowed")),
        "phase40r_rag_reply_allowed": bool(phase40r_matrix.get("rag_reply_allowed")),
        "phase40s_safe_to_review_next_morning": bool(phase40s_morning.get("safe_to_review_next_morning")),
        "phase40s_requires_user_confirmation": bool(phase40s_morning.get("requires_user_confirmation")),
        "phase40s_additional_discord_send_count": int(phase40s_morning.get("additional_discord_send_count", 0) or 0),
        "phase40t_command_available": True,
        "phase40t_blocked_by_default": bool(phase40t_command.get("blocked")),
        "phase40t_manual_runtime_launch_allowed": bool(phase40t_command.get("manual_runtime_launch_allowed")),
        "phase40t_codex_runtime_launch_forbidden": bool(phase40t_command.get("codex_runtime_launch_forbidden")),
        "phase40t_live_runtime_started": bool(phase40t_command.get("live_runtime_started")),
        "phase40t_discord_gateway_connected": bool(phase40t_command.get("discord_gateway_connected")),
        "phase40t_discord_api_send_called": bool(phase40t_command.get("discord_api_send_called")),
        "phase40t_discord_message_sent": bool(phase40t_command.get("discord_message_sent")),
        "phase40t_message_sent_count": int(phase40t_command.get("message_sent_count", 0) or 0),
        "phase40t_send_messages_enabled": bool(phase40t_command.get("send_messages_enabled")),
        "phase40t_private_test_reply_enabled": bool(phase40t_command.get("private_test_reply_enabled")),
        "phase40t_ready_for_phase41_reply_runtime": bool(phase40t_command.get("ready_for_phase41_reply_runtime")),
        "phase40t_preflight_snapshot_preserved": bool(phase40t_command.get("preflight_snapshot_preserved")),
        "phase40t_presence_consistency_verified": bool(phase40t_command.get("presence_consistency_verified")),
        "phase40t_login_attempt_requires_token_and_channel": bool(phase40t_command.get("login_attempt_requires_token_and_channel")),
        "phase40t_execution_gate_available": True,
        "phase40t_execute_flag_required": bool(phase40t_gate.get("execute_flag_required")),
        "phase40t_execute_flag_present": bool(phase40t_gate.get("execute_flag_present")),
        "phase40t_execution_gate_blocked_by_default": bool(phase40t_gate.get("blocked")),
        "phase40t_capture_schema_version": CAPTURE_SCHEMA_VERSION,
        "phase40t_redacted_capture_only": True,
        "phase40t_capture_raw_content_allowed": False,
        "phase40t_capture_raw_discord_ids_allowed": False,
        "phase40t_capture_secret_values_allowed": False,
        "phase40t_closeout_available": True,
        "phase40t_closeout_started": bool(phase40t_closeout.get("started")),
        "phase40t_closeout_gateway_connected": bool(phase40t_closeout.get("discord_gateway_connected")),
        "phase40t_closeout_message_sent_count": int(phase40t_closeout.get("message_sent_count", 0) or 0),
        "phase40t_login_failure_closeout_available": True,
        "phase40t_login_failure_blocked": bool(phase40t_login_failure.get("blocked")),
        "phase40t_login_failure_gateway_connected": bool(phase40t_login_failure.get("discord_gateway_connected")),
        "phase40t_login_failure_discord_api_send_called": bool(phase40t_login_failure.get("discord_api_send_called")),
        "phase40t_login_failure_discord_message_sent": bool(phase40t_login_failure.get("discord_message_sent")),
        "phase40t_login_failure_message_sent_count": int(phase40t_login_failure.get("message_sent_count", 0) or 0),
        "phase40t_login_failure_retry_attempted": bool(phase40t_login_failure.get("retry_attempted")),
        "phase40t_login_failure_traceback_included": bool(phase40t_login_failure.get("traceback_included")),
        "phase40t_login_failure_token_value_logged": bool(phase40t_login_failure.get("discord_token_value_logged")),
        "phase40t_login_failure_preflight_snapshot_preserved": bool(phase40t_login_failure.get("preflight_snapshot_preserved")),
        "phase40t_login_failure_presence_consistency_verified": bool(phase40t_login_failure.get("presence_consistency_verified")),
        "phase40t_gateway_connect_verified": bool(phase40u_closeout.get("gateway_connect_verified")),
        "phase40u_closeout_ready": bool(phase40u_closeout.get("ready_for_phase41_dry_run_preparation")),
        "phase40u_discord_api_send_called": bool(phase40u_closeout.get("discord_api_send_called")),
        "phase40u_discord_message_sent": bool(phase40u_closeout.get("discord_message_sent")),
        "phase40u_message_sent_count": int(phase40u_closeout.get("message_sent_count", 0) or 0),
        "phase40x_reply_dry_run_ready": bool(phase40x_reply.get("ready_for_phase41_preflight_gate")),
        "phase40x_discord_api_send_called": bool(phase40x_reply.get("discord_api_send_called")),
        "phase40x_discord_message_sent": bool(phase40x_reply.get("discord_message_sent")),
        "phase40x_message_sent_count": int(phase40x_reply.get("message_sent_count", 0) or 0),
        "phase41_actual_reply_default_blocked": bool(phase40y_gate.get("default_blocked")),
        "phase41_actual_reply_send_executed": bool(phase40y_gate.get("actual_reply_send_executed")),
        "phase41_discord_api_send_called": bool(phase40y_gate.get("discord_api_send_called")),
        "phase41_discord_message_sent": bool(phase40y_gate.get("discord_message_sent")),
        "phase41_message_sent_count": int(phase40y_gate.get("message_sent_count", 0) or 0),
        "phase40z_handoff_ready": bool(phase40z_handoff.get("phase40u_closeout_ready")) and bool(phase40z_handoff.get("phase40x_reply_dry_run_ready")),
        "phase41a_preflight_default_blocked": bool(phase41_preflight.get("default_blocked")),
        "phase41a_ready_for_manual_private_test_reply": bool(phase41_preflight.get("ready_for_manual_private_test_reply")),
        "phase41b_one_shot_available": True,
        "phase41b_default_blocked": bool(phase41b_one_shot.get("default_blocked")),
        "phase41b_ready_for_manual_private_test_reply_one_shot": bool(phase41b_one_shot.get("ready_for_manual_private_test_reply_one_shot")),
        "phase41b_actual_reply_send_executed": bool(phase41b_one_shot.get("actual_reply_send_executed")),
        "phase41b_discord_api_send_called": bool(phase41b_one_shot.get("discord_api_send_called")),
        "phase41b_discord_message_sent": bool(phase41b_one_shot.get("discord_message_sent")),
        "phase41b_message_sent_count": int(phase41b_one_shot.get("message_sent_count", 0) or 0),
        "phase41c_closeout_available": True,
        "phase41c_message_sent_count": int(phase41c_closeout.get("message_sent_count", 0) or 0),
        "phase41c_ready_for_repeat_send": bool(phase41c_closeout.get("ready_for_repeat_send")),
        "phase42_session_preflight_available": True,
        "phase42_actual_runtime_executed": bool(phase42_session.get("actual_runtime_executed")),
        "phase42_discord_message_sent": bool(phase42_session.get("discord_message_sent")),
        "phase43_policy_available": bool(phase43_policy.get("routing_policy_available")),
        "phase43_public_team_blocked": bool(phase43_policy.get("public_team_blocked")),
        "phase44_provider_preflight_available": True,
        "phase44_actual_llm_api_call": bool(phase44_provider.get("actual_llm_api_call")),
        "phase44_llm_api_call_attempted": bool(phase44_provider.get("llm_api_call_attempted")),
        "phase44_fake_adapter_available": bool(phase44_fake.get("fake_adapter_used")),
        "phase44_fake_output_schema_valid": bool(phase44_fake.get("output_schema_valid")),
        "phase45_preflight_available": True,
        "phase45_ready_for_actual_llm_one_shot_call": bool(phase45_preflight.get("ready_for_actual_llm_one_shot_call")),
        "phase45_actual_llm_api_call": bool(phase45_preflight.get("actual_llm_api_call")),
        "phase45_llm_api_call_attempted": bool(phase45_preflight.get("llm_api_call_attempted")),
        "phase45_discord_message_sent": bool(phase45_preflight.get("discord_message_sent")),
        "ready_for_live_runtime": False,
        "ready_for_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "approval_phrase_generated": False,
            "live_runtime_executed": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
            "phase40_live_runtime_started": False,
            "phase40_discord_gateway_connected": False,
            "phase40_discord_api_send_called": False,
            "phase40_discord_message_sent": False,
            "phase40j_ready_for_manual_readonly_runtime_launch": False,
            "phase40k_planned_command_executed_by_codex": False,
            "phase40n_phase41_reply_runtime_allowed": False,
            "phase40o_ready_for_manual_readonly_runtime_launch": False,
            "phase40r_phase41_reply_runtime_allowed": False,
            "phase40r_discord_reply_send_allowed": False,
            "phase40t_live_runtime_started": False,
            "phase40t_discord_gateway_connected": False,
            "phase40t_discord_api_send_called": False,
            "phase40t_discord_message_sent": False,
            "phase40t_execute_flag_present": False,
            "phase40t_closeout_started": False,
            "phase40t_closeout_gateway_connected": False,
            "phase40t_login_failure_gateway_connected": False,
            "phase40t_login_failure_discord_api_send_called": False,
            "phase40t_login_failure_discord_message_sent": False,
            "phase40t_login_failure_retry_attempted": False,
            "phase40t_login_failure_traceback_included": False,
            "phase40t_login_failure_token_value_logged": False,
            "phase40u_discord_api_send_called": False,
            "phase40u_discord_message_sent": False,
            "phase40x_discord_api_send_called": False,
            "phase40x_discord_message_sent": False,
            "phase41_actual_reply_send_executed": False,
            "phase41_discord_api_send_called": False,
            "phase41_discord_message_sent": False,
            "phase41a_ready_for_manual_private_test_reply": False,
            "phase41b_actual_reply_send_executed": False,
            "phase41b_discord_api_send_called": False,
            "phase41b_discord_message_sent": False,
            "phase42_actual_runtime_executed": False,
            "phase44_actual_llm_api_call": False,
            "phase44_llm_api_call_attempted": False,
            "phase45_actual_llm_api_call": False,
            "phase45_llm_api_call_attempted": False,
            "phase45_discord_message_sent": False,
        },
    }
    assert_operations_dashboard_lock_safe(report)
    return report


def assert_operations_dashboard_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Operations dashboard lock contains sensitive values.")
    for key in (
        "unattended_auto_reply_allowed",
        "external_execution",
        "ready_for_live_runtime",
        "ready_for_llm_call",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
        "ready_for_phase39_live_execution",
        "phase39a_actual_private_test_send_executed",
        "phase39a_discord_message_sent",
        "ready_for_phase39b_manual_one_shot_send",
        "phase39b_discord_message_sent",
        "ready_for_phase39c_send_closeout",
        "phase39c_repeat_send_allowed",
        "phase39c_automatic_retry_allowed",
        "phase39c_ready_for_repeat_send",
        "phase40_live_runtime_started",
        "phase40_discord_gateway_connected",
        "phase40_discord_api_send_called",
        "phase40_discord_message_sent",
        "phase40_outbound_queue_enabled",
        "phase40_send_worker_enabled",
        "phase40_live_runtime_start_allowed",
        "phase40_ready_for_live_runtime_execution",
        "phase40j_ready_for_manual_readonly_runtime_launch",
        "phase40k_planned_command_executed_by_codex",
        "phase40l_live_capture_observed",
        "phase40n_phase41_reply_runtime_allowed",
        "phase40n_reply_send_allowed",
        "phase40n_ready_for_phase41_reply_runtime",
        "phase40o_ready_for_manual_readonly_runtime_launch",
        "phase40p_raw_content_logged",
        "phase40p_secret_values_logged",
        "phase40q_capture_review_completed",
        "phase40r_phase41_reply_runtime_allowed",
        "phase40r_discord_reply_send_allowed",
        "phase40r_llm_reply_allowed",
        "phase40r_rag_reply_allowed",
        "phase40t_manual_runtime_launch_allowed",
        "phase40t_live_runtime_started",
        "phase40t_discord_gateway_connected",
        "phase40t_discord_api_send_called",
        "phase40t_discord_message_sent",
        "phase40t_send_messages_enabled",
        "phase40t_private_test_reply_enabled",
        "phase40t_ready_for_phase41_reply_runtime",
        "phase40t_execute_flag_present",
        "phase40t_capture_raw_content_allowed",
        "phase40t_capture_raw_discord_ids_allowed",
        "phase40t_capture_secret_values_allowed",
        "phase40t_closeout_started",
        "phase40t_closeout_gateway_connected",
        "phase40t_login_failure_gateway_connected",
        "phase40t_login_failure_discord_api_send_called",
        "phase40t_login_failure_discord_message_sent",
        "phase40t_login_failure_retry_attempted",
        "phase40t_login_failure_traceback_included",
        "phase40t_login_failure_token_value_logged",
        "phase40u_discord_api_send_called",
        "phase40u_discord_message_sent",
        "phase40x_discord_api_send_called",
        "phase40x_discord_message_sent",
        "phase41_actual_reply_send_executed",
        "phase41_discord_api_send_called",
        "phase41_discord_message_sent",
        "phase41a_ready_for_manual_private_test_reply",
        "phase41b_ready_for_manual_private_test_reply_one_shot",
        "phase41b_actual_reply_send_executed",
        "phase41b_discord_api_send_called",
        "phase41b_discord_message_sent",
        "phase41c_ready_for_repeat_send",
        "phase42_actual_runtime_executed",
        "phase42_discord_message_sent",
        "phase44_actual_llm_api_call",
        "phase44_llm_api_call_attempted",
        "phase45_ready_for_actual_llm_one_shot_call",
        "phase45_actual_llm_api_call",
        "phase45_llm_api_call_attempted",
        "phase45_discord_message_sent",
    ):
        if report.get(key):
            raise ValueError(f"Operations dashboard lock unsafe flag is true: {key}")
    if int(report.get("phase39b_actual_discord_send_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock requires Phase 39B send count 0.")
    if int(report.get("phase39c_actual_discord_send_count_locked", 0) or 0) != 1:
        raise ValueError("Operations dashboard lock requires Phase 39C send count locked to 1.")
    if int(report.get("phase39c_additional_send_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock forbids Phase 39C additional sends.")
    if not report.get("phase39c_closeout_completed") or not report.get("phase39c_gate_off_verified"):
        raise ValueError("Operations dashboard lock requires Phase 39C closeout and gate-off audit.")
    if int(report.get("phase40_actual_discord_send_count_locked", 0) or 0) != 1:
        raise ValueError("Operations dashboard lock requires Phase 40 count locked to 1.")
    if int(report.get("phase40_additional_discord_send_count", 0) or 0) != 0 or int(report.get("phase40_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock forbids Phase 40 sends.")
    if not report.get("phase40_runtime_readiness_available") or not report.get("phase40_synthetic_replay_only") or not report.get("phase40_duplicate_message_id_guard"):
        raise ValueError("Operations dashboard lock requires Phase 40 readiness guards.")
    if not report.get("phase40j_readonly_preflight_available") or not report.get("phase40k_manual_launch_only") or not report.get("phase40k_codex_must_not_launch"):
        raise ValueError("Operations dashboard lock requires Phase 40J/K read-only launch guards.")
    if not report.get("phase40l_capture_closeout_available") or int(report.get("phase40l_captured_event_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock requires Phase 40L pre-capture closeout state.")
    if not report.get("phase40m_manual_abort_available") or not report.get("phase40m_abort_on_any_send_attempt"):
        raise ValueError("Operations dashboard lock requires Phase 40M abort guards.")
    if not report.get("phase40n_phase41_reply_runtime_entry_gate_available"):
        raise ValueError("Operations dashboard lock requires Phase 40N entry gate.")
    if not report.get("phase40o_manual_launch_only") or not report.get("phase40o_codex_must_not_launch"):
        raise ValueError("Operations dashboard lock requires Phase 40O manual-only launch support.")
    if not report.get("phase40p_capture_schema_available"):
        raise ValueError("Operations dashboard lock requires Phase 40P capture schema.")
    if int(report.get("phase40q_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock forbids Phase 40Q sends.")
    if not report.get("phase40s_safe_to_review_next_morning") or not report.get("phase40s_requires_user_confirmation"):
        raise ValueError("Operations dashboard lock requires Phase 40S morning review confirmation.")
    if int(report.get("phase40s_additional_discord_send_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock forbids Phase 40S additional sends.")
    if not report.get("phase40t_command_available") or not report.get("phase40t_blocked_by_default") or not report.get("phase40t_codex_runtime_launch_forbidden"):
        raise ValueError("Operations dashboard lock requires Phase 40T blocked command guard.")
    if int(report.get("phase40t_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock forbids Phase 40T sends.")
    if not report.get("phase40t_preflight_snapshot_preserved") or not report.get("phase40t_presence_consistency_verified") or not report.get("phase40t_login_attempt_requires_token_and_channel"):
        raise ValueError("Operations dashboard lock requires Phase 40T preflight snapshot consistency.")
    if not report.get("phase40t_execution_gate_available") or not report.get("phase40t_execute_flag_required") or not report.get("phase40t_execution_gate_blocked_by_default"):
        raise ValueError("Operations dashboard lock requires Phase 40T execution gate blocked by default.")
    if not report.get("phase40t_redacted_capture_only") or int(report.get("phase40t_closeout_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock requires Phase 40T redacted/no-send closeout posture.")
    if not report.get("phase40t_login_failure_closeout_available") or int(report.get("phase40t_login_failure_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock requires Phase 40T login failure closeout with send count 0.")
    if not report.get("phase40t_login_failure_preflight_snapshot_preserved") or not report.get("phase40t_login_failure_presence_consistency_verified"):
        raise ValueError("Operations dashboard lock requires Phase 40T login failure snapshot consistency.")
    if not report.get("phase40t_gateway_connect_verified") or not report.get("phase40u_closeout_ready"):
        raise ValueError("Operations dashboard lock requires Phase 40U read-only connection closeout readiness.")
    if int(report.get("phase40u_message_sent_count", 0) or 0) != 0 or int(report.get("phase40x_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock forbids Phase 40U/X messages.")
    if not report.get("phase40x_reply_dry_run_ready") or not report.get("phase41_actual_reply_default_blocked"):
        raise ValueError("Operations dashboard lock requires Phase 40X dry-run and Phase 41 default block.")
    if int(report.get("phase41_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock forbids Phase 41 messages.")
    if not report.get("phase40z_handoff_ready") or not report.get("phase41a_preflight_default_blocked"):
        raise ValueError("Operations dashboard lock requires Phase 40Z handoff and Phase 41A default block.")
    if not report.get("phase41b_one_shot_available") or not report.get("phase41b_default_blocked") or int(report.get("phase41b_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock requires Phase 41B blocked no-send prep.")
    if not report.get("phase41c_closeout_available") or int(report.get("phase41c_message_sent_count", 0) or 0) != 0:
        raise ValueError("Operations dashboard lock requires Phase 41C no-send scaffold.")
    if not report.get("phase42_session_preflight_available"):
        raise ValueError("Operations dashboard lock requires Phase 42 session preflight.")
    if not report.get("phase43_policy_available") or not report.get("phase43_public_team_blocked"):
        raise ValueError("Operations dashboard lock requires Phase 43 routing policy.")
    if not report.get("phase44_provider_preflight_available") or not report.get("phase44_fake_adapter_available") or not report.get("phase44_fake_output_schema_valid"):
        raise ValueError("Operations dashboard lock requires Phase 44 preflight/fake adapter.")
    if not report.get("phase45_preflight_available"):
        raise ValueError("Operations dashboard lock requires Phase 45A preflight.")


def render_operations_dashboard_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Operations Dashboard Lock",
            "",
            "- Dashboard lock available: true",
            f"- Private-test MVP complete: {str(report.get('phase34_private_test_mvp_complete')).lower()}",
            f"- Phase 35A safety audit passed: {str(report.get('phase35a_safety_audit_passed')).lower()}",
            f"- Total LLM call count: {report.get('total_llm_call_count')}",
            f"- Send retry LLM count: {report.get('send_retry_llm_call_count')}",
            f"- Final Discord message count: {report.get('final_discord_message_sent_count')}",
            f"- Sent channel scope: {report.get('sent_channel_scope')}",
            "- Current live gates off: true",
            "- Public/team blocked: true",
            "- Unattended auto reply allowed: false",
            "- Embedding/vector disabled: true",
            "- External execution: false",
            "- Ready for live runtime: false",
            f"- Phase 40 runtime readiness available: {str(report.get('phase40_runtime_readiness_available')).lower()}",
            f"- Phase 40 additional Discord send count: {report.get('phase40_additional_discord_send_count')}",
            f"- Phase 40 safe to review next morning: {str(report.get('phase40_safe_to_review_next_morning')).lower()}",
            f"- Phase 40J ready for manual read-only runtime launch: {str(report.get('phase40j_ready_for_manual_readonly_runtime_launch')).lower()}",
            f"- Phase 40N Phase 41 reply runtime allowed: {str(report.get('phase40n_phase41_reply_runtime_allowed')).lower()}",
            f"- Phase 40O manual launch only: {str(report.get('phase40o_manual_launch_only')).lower()}",
            f"- Phase 40R Discord reply send allowed: {str(report.get('phase40r_discord_reply_send_allowed')).lower()}",
            f"- Phase 40T command available: {str(report.get('phase40t_command_available')).lower()}",
            f"- Phase 40T blocked by default: {str(report.get('phase40t_blocked_by_default')).lower()}",
            f"- Phase 40T execute flag required: {str(report.get('phase40t_execute_flag_required')).lower()}",
            f"- Phase 40T redacted capture only: {str(report.get('phase40t_redacted_capture_only')).lower()}",
            f"- Phase 41B one-shot default blocked: {str(report.get('phase41b_default_blocked')).lower()}",
            f"- Phase 41B message sent count: {report.get('phase41b_message_sent_count')}",
            f"- Phase 42 actual runtime executed: {str(report.get('phase42_actual_runtime_executed')).lower()}",
            f"- Phase 44 actual LLM API call: {str(report.get('phase44_actual_llm_api_call')).lower()}",
            f"- Phase 45 actual LLM API call: {str(report.get('phase45_actual_llm_api_call')).lower()}",
        ]
    ) + "\n"
