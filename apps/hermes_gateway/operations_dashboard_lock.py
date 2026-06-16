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
        ]
    ) + "\n"
