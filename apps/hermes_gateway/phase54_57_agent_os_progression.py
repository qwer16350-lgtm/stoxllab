"""Phase54-57 lean Agent OS progression report.

This report closes out the operator-run read-only capture canary as metadata
only and prepares the next manual gates without live runtime, send, LLM, RAG,
or scheduler execution.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase54_57_agent_os_progression_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase54_57_agent_os_progression() -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_type": "phase54_57_agent_os_progression",
        "version": VERSION,
        "metadata_only": True,
        "real_readonly_canary_closed_out": True,
        "actual_readonly_canary_executed_by_operator": True,
        "gateway_connection_verified": True,
        "runtime_scope": "private_test_readonly",
        "timeout_seconds": 120,
        "max_events": 5,
        "exit_reason": "timeout",
        "captured_event_count": 1,
        "captured_private_test_human_message_count": 1,
        "captured_self_message_count": 0,
        "captured_bot_message_count": 0,
        "captured_duplicate_message_count": 0,
        "capture_file_written": True,
        "capture_file_metadata_only": True,
        "capture_file_path_value_logged": False,
        "capture_file_read_attempted": False,
        "capture_file_raw_dumped": False,
        "real_capture_to_review_packet_replay_ready": True,
        "review_packet_count": 1,
        "review_packet_metadata_only": True,
        "requires_human_review": True,
        "recommended_next_action": "manual_approved_reply_preflight",
        "discord_send_allowed": False,
        "llm_allowed": False,
        "rag_allowed": False,
        "manual_approved_reply_preflight_available": True,
        "manual_gate_required": True,
        "approval_phrase_present": True,
        "approval_phrase_value_logged": False,
        "manual_reply_env_gate_separate": True,
        "preflight_closed_fixture_passed": True,
        "preflight_open_fixture_passed": True,
        "ready_for_actual_private_test_manual_reply": False,
        "ready_for_actual_private_test_manual_reply_gate": True,
        "mock_reply_packet_created": True,
        "reply_text_source": "deterministic_template",
        "raw_user_content_included": False,
        "ready_for_manual_reply_send_gate": True,
        "supervised_private_test_auto_reply_prep_ready": True,
        "actual_auto_reply_executed": False,
        "private_test_only": True,
        "max_session_seconds": 300,
        "max_reply_count": 1,
        "max_send_count": 1,
        "cooldown_seconds": 30,
        "duplicate_guard": True,
        "self_loop_guard": True,
        "bot_message_guard": True,
        "kill_switch_required": True,
        "llm_rag_disabled_by_default": True,
        "ready_for_supervised_private_test_auto_reply_manual_gate": True,
        "low_risk_team_auto_ops_policy_defined": True,
        "known_team_channel_only": True,
        "non_public_only": True,
        "legal_financial_secret_sensitive_blocked": True,
        "file_deletion_blocked": True,
        "code_push_blocked": True,
        "max_one_reply_per_event": True,
        "human_override_required": True,
        "team_channel_auto_ops_executed": False,
        "manual_gate_required_for_team_canary": True,
        "scheduler_dry_run_policy_defined": True,
        "scheduler_live_execution": False,
        "cron_started": False,
        "ready_for_scheduler_manual_gate": False,
        "ready_for_team_channel_auto_ops": False,
        "ready_for_production_unattended": False,
        "actual_discord_runtime_executed": False,
        "discord_gateway_live_connection_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "unattended_auto_reply_executed": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "raw_session_ids_logged": False,
        "secret_values_logged": False,
        "blocked_llm_raw_output_dumped": False,
        "env_file_read": False,
        "exports_read": False,
        "logs_read": False,
        "local_mapping_read": False,
    }
    assert_phase54_57_agent_os_progression_safe(report)
    return report


def assert_phase54_57_agent_os_progression_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase54-57 report contains sensitive values.")
    for key in (
        "capture_file_path_value_logged",
        "capture_file_read_attempted",
        "capture_file_raw_dumped",
        "discord_send_allowed",
        "llm_allowed",
        "rag_allowed",
        "ready_for_actual_private_test_manual_reply",
        "actual_auto_reply_executed",
        "team_channel_auto_ops_executed",
        "scheduler_live_execution",
        "cron_started",
        "ready_for_scheduler_manual_gate",
        "ready_for_team_channel_auto_ops",
        "ready_for_production_unattended",
        "actual_discord_runtime_executed",
        "discord_gateway_live_connection_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "unattended_auto_reply_executed",
        "raw_user_content_included",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "blocked_llm_raw_output_dumped",
        "env_file_read",
        "exports_read",
        "logs_read",
        "local_mapping_read",
    ):
        if report.get(key):
            raise ValueError(f"Phase54-57 unsafe flag is true: {key}")
    for key in (
        "real_readonly_canary_closed_out",
        "gateway_connection_verified",
        "capture_file_written",
        "capture_file_metadata_only",
        "real_capture_to_review_packet_replay_ready",
        "requires_human_review",
        "manual_approved_reply_preflight_available",
        "manual_gate_required",
        "approval_phrase_present",
        "mock_reply_packet_created",
        "supervised_private_test_auto_reply_prep_ready",
        "low_risk_team_auto_ops_policy_defined",
        "scheduler_dry_run_policy_defined",
        "ready_for_actual_private_test_manual_reply_gate",
        "ready_for_supervised_private_test_auto_reply_manual_gate",
    ):
        if not report.get(key):
            raise ValueError(f"Phase54-57 required flag is false: {key}")
    if int(report.get("captured_event_count", 0) or 0) != 1:
        raise ValueError("Phase54-57 captured_event_count must be 1.")
    if int(report.get("captured_private_test_human_message_count", 0) or 0) != 1:
        raise ValueError("Phase54-57 human message count must be 1.")
    if int(report.get("review_packet_count", 0) or 0) != 1:
        raise ValueError("Phase54-57 review_packet_count must be 1.")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase54-57 message_sent_count must stay 0.")


def render_phase54_57_agent_os_progression_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase54-57 Agent OS Progression",
            "",
            "- Real read-only canary closed out: true",
            f"- Captured event count: {report.get('captured_event_count')}",
            f"- Captured private-test human message count: {report.get('captured_private_test_human_message_count')}",
            f"- Review packet count: {report.get('review_packet_count')}",
            "- Manual-approved reply preflight available: true",
            "- Mock reply packet created: true",
            "- Supervised private-test auto-reply prep ready: true",
            "- Low-risk team auto-ops policy defined: true",
            "- Scheduler dry-run policy defined: true",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- LLM/RAG/embedding/vector/external: false",
            "- Next actual operation: separate Manual Gate for actual private-test manual-approved reply",
        ]
    ) + "\n"
