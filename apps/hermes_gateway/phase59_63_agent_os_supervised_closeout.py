"""Phase59-63 supervised Agent OS closeout report.

This aggregate report records the operator-run Phase59 supervised private-test
auto-reply success as metadata only, locks repeat sessions, and prepares the
next team/scheduler/autonomy gates without external action.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase59_63_agent_os_supervised_closeout_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase59_63_agent_os_supervised_closeout() -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_type": "phase59_63_agent_os_supervised_closeout",
        "version": VERSION,
        "metadata_only": True,
        "large_lean_bundle": True,
        "phase59_supervised_auto_reply_closed_out": True,
        "phase59_actual_session_sent": True,
        "sent_scope": "private_test_only",
        "reply_text_source": "deterministic_template",
        "historical_message_sent_count": 1,
        "phase59_repeat_session_locked": True,
        "phase59_repeat_block_reason": "phase59_supervised_auto_reply_session_already_consumed",
        "ready_for_repeat_session": False,
        "phase60_low_risk_team_canary_path_available": True,
        "phase60_known_team_channel_only": True,
        "phase60_non_public_only": True,
        "phase60_low_risk_intent_only": True,
        "phase60_deterministic_template_only": True,
        "phase60_max_one_reply_per_event": True,
        "phase60_human_override_required": True,
        "phase60_kill_switch_required": True,
        "phase60_llm_rag_disabled_by_default": True,
        "phase60_external_execution_disabled": True,
        "phase60_scheduler_live_disabled": True,
        "team_channel_auto_ops_executed": False,
        "team_channel_discord_send_called": False,
        "public_channel_send_allowed": False,
        "ready_for_phase60_team_canary_manual_gate": False,
        "phase61_scheduler_gate_available": True,
        "scheduler_dry_run_control_available": True,
        "scheduler_preview_tasks_allowed": [
            "daily_summary_preview",
            "read_only_digest_preview",
            "review_packet_queue_summary",
            "manual_gate_reminder_preview",
        ],
        "scheduler_live_tasks_blocked": [
            "auto_reply",
            "auto_send",
            "live_cron_start",
            "external_execution",
            "llm_call_without_manual_gate",
            "rag_call_without_manual_gate",
        ],
        "scheduler_live_execution": False,
        "cron_started": False,
        "ready_for_scheduler_manual_gate": False,
        "phase62_autonomy_matrix_updated": True,
        "phase63_release_blockers_updated": True,
        "autonomy_matrix": {
            "level_1": "read_only_observation_verified",
            "level_2": "manual_gate_deterministic_reply_verified",
            "level_3": "supervised_private_test_auto_reply_verified",
            "level_4": "low_risk_team_auto_ops_path_prepared_not_executed",
            "level_5": "production_unattended_not_ready",
        },
        "release_blockers": [
            "team_canary_not_executed",
            "scheduler_live_not_approved",
            "rag_llm_live_reply_not_approved",
            "production_kill_switch_not_live_tested",
            "git_index_lock_unresolved",
            "refactor_compaction_pending",
        ],
        "current_verified_level": "level3_supervised_private_test_auto_reply_verified",
        "next_target_level": "level4_low_risk_team_channel_canary",
        "ready_for_production_unattended": False,
        "next_actual_operation": "separate_manual_gate_prep_for_phase60_low_risk_team_channel_canary",
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
        "approval_phrase_value_logged": False,
        "capture_file_path_value_logged": False,
        "capture_file_raw_dumped": False,
        "env_file_read": False,
        "exports_read": False,
        "logs_read": False,
        "local_mapping_read": False,
    }
    assert_phase59_63_agent_os_supervised_closeout_safe(report)
    return report


def assert_phase59_63_agent_os_supervised_closeout_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase59-63 closeout contains sensitive values.")
    for key in (
        "ready_for_repeat_session",
        "team_channel_auto_ops_executed",
        "team_channel_discord_send_called",
        "public_channel_send_allowed",
        "ready_for_phase60_team_canary_manual_gate",
        "scheduler_live_execution",
        "cron_started",
        "ready_for_scheduler_manual_gate",
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
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "capture_file_path_value_logged",
        "capture_file_raw_dumped",
        "env_file_read",
        "exports_read",
        "logs_read",
        "local_mapping_read",
    ):
        if report.get(key):
            raise ValueError(f"Phase59-63 unsafe flag is true: {key}")
    for key in (
        "metadata_only",
        "phase59_supervised_auto_reply_closed_out",
        "phase59_actual_session_sent",
        "phase59_repeat_session_locked",
        "phase60_low_risk_team_canary_path_available",
        "phase61_scheduler_gate_available",
        "scheduler_dry_run_control_available",
        "phase62_autonomy_matrix_updated",
        "phase63_release_blockers_updated",
    ):
        if not report.get(key):
            raise ValueError(f"Phase59-63 required flag is false: {key}")
    if int(report.get("historical_message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase59 historical message count must be 1.")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase59-63 closeout must not send new messages.")
    if report.get("phase59_repeat_block_reason") != "phase59_supervised_auto_reply_session_already_consumed":
        raise ValueError("Phase59 repeat block reason mismatch.")
    if report.get("sent_scope") != "private_test_only":
        raise ValueError("Phase59 sent scope must be private_test_only.")
    if report.get("reply_text_source") != "deterministic_template":
        raise ValueError("Phase59 reply text source must be deterministic_template.")


def render_phase59_63_agent_os_supervised_closeout_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase59-63 Agent OS Supervised Closeout",
            "",
            "- Metadata only: true",
            "- Phase59 supervised auto-reply closed out: true",
            f"- Historical message sent count: {report.get('historical_message_sent_count')}",
            "- Phase59 repeat session locked: true",
            "- Phase60 low-risk team canary path available: true",
            "- Phase61 scheduler dry-run control available: true",
            "- Phase62 autonomy matrix updated: true",
            f"- Current verified level: {report.get('current_verified_level')}",
            f"- Next target level: {report.get('next_target_level')}",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- LLM/RAG/embedding/vector/external: false",
            f"- Next actual operation: {report.get('next_actual_operation')}",
        ]
    ) + "\n"
