"""Phase59-62 large lean Agent OS autonomy stage report.

This report wires Phase59 readiness into the broader Agent OS roadmap without
running Discord, sending messages, calling LLM/RAG, or starting scheduler work.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase59_62_agent_os_autonomy_stage_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase59_62_agent_os_autonomy_stage() -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_type": "phase59_62_agent_os_autonomy_stage",
        "version": VERSION,
        "metadata_only": True,
        "large_lean_bundle": True,
        "phase58_actual_reply_closeout_complete": True,
        "phase58_message_sent_count_fixed": 1,
        "phase58_repeat_send_locked": True,
        "phase59_supervised_private_test_auto_reply_path_available": True,
        "phase59_sender_adapter_wired": True,
        "phase59_real_sender_adapter_available_for_manual_gate": True,
        "phase59_real_sender_adapter_used_in_this_bundle": False,
        "phase59_fake_sender_exactly_once_test_required": True,
        "phase59_actual_cli_without_allow_expected_blocked": True,
        "phase59_send_adapter_required_block_resolved": True,
        "phase59_ready_for_manual_gate_short_session": True,
        "phase59_ready_for_repeat_session": False,
        "phase59_max_reply_count": 1,
        "phase59_max_send_count": 1,
        "phase59_reply_text_source": "deterministic_template",
        "phase59_runtime_scope": "private_test_only",
        "phase59_sent_scope": "private_test_only",
        "phase60_low_risk_team_canary_policy_synced": True,
        "phase60_team_send_executed": False,
        "phase60_known_team_channel_only": True,
        "phase60_non_public_only": True,
        "phase60_sensitive_topics_blocked": True,
        "phase60_file_deletion_blocked": True,
        "phase60_code_push_blocked": True,
        "phase60_human_override_required": True,
        "phase60_ready_for_team_auto_ops": False,
        "phase61_scheduler_dry_run_control_synced": True,
        "phase61_scheduler_dry_run_only": True,
        "phase61_scheduler_live_execution": False,
        "phase61_cron_started": False,
        "phase61_ready_for_scheduler_live_gate": False,
        "phase62_autonomy_matrix_updated": True,
        "autonomy_matrix": {
            "level_2": "manual_gate_deterministic_reply_verified",
            "level_3": "supervised_private_test_auto_reply_path_nearly_ready_sender_wired",
            "level_4": "team_auto_ops_not_ready",
            "level_5": "production_unattended_not_ready",
        },
        "current_autonomy_level": "level_3_pre_manual_gate",
        "ready_for_level_4": False,
        "ready_for_level_5": False,
        "next_actual_operation": "separate_manual_gate_actual_phase59_supervised_private_test_auto_reply_short_session_exactly_once",
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
        "scheduler_live_execution": False,
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
    assert_phase59_62_agent_os_autonomy_stage_safe(report)
    return report


def assert_phase59_62_agent_os_autonomy_stage_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase59-62 report contains sensitive values.")
    for key in (
        "phase59_real_sender_adapter_used_in_this_bundle",
        "phase59_ready_for_repeat_session",
        "phase60_team_send_executed",
        "phase60_ready_for_team_auto_ops",
        "phase61_scheduler_live_execution",
        "phase61_cron_started",
        "phase61_ready_for_scheduler_live_gate",
        "ready_for_level_4",
        "ready_for_level_5",
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
        "scheduler_live_execution",
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
            raise ValueError(f"Phase59-62 unsafe flag is true: {key}")
    for key in (
        "metadata_only",
        "phase58_actual_reply_closeout_complete",
        "phase58_repeat_send_locked",
        "phase59_supervised_private_test_auto_reply_path_available",
        "phase59_sender_adapter_wired",
        "phase59_send_adapter_required_block_resolved",
        "phase59_ready_for_manual_gate_short_session",
        "phase60_low_risk_team_canary_policy_synced",
        "phase61_scheduler_dry_run_control_synced",
        "phase62_autonomy_matrix_updated",
    ):
        if not report.get(key):
            raise ValueError(f"Phase59-62 required flag is false: {key}")
    if int(report.get("phase58_message_sent_count_fixed", 0) or 0) != 1:
        raise ValueError("Phase59-62 Phase58 fixed message count must be 1.")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase59-62 bundle message_sent_count must stay 0.")
    if report.get("phase59_reply_text_source") != "deterministic_template":
        raise ValueError("Phase59-62 Phase59 reply source must be deterministic_template.")
    if report.get("phase59_runtime_scope") != "private_test_only" or report.get("phase59_sent_scope") != "private_test_only":
        raise ValueError("Phase59-62 Phase59 scope must stay private_test_only.")


def render_phase59_62_agent_os_autonomy_stage_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase59-62 Agent OS Autonomy Stage",
            "",
            "- Metadata only: true",
            "- Phase59 sender adapter wired: true",
            "- Phase59 real sender used in this bundle: false",
            "- Phase60 team canary policy synced: true",
            "- Phase61 scheduler dry-run control synced: true",
            "- Phase62 autonomy matrix updated: true",
            "- Level 2: manual-gate deterministic reply verified",
            "- Level 3: supervised private-test auto-reply path nearly ready, sender wired",
            "- Level 4: team auto-ops not ready",
            "- Level 5: production unattended not ready",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- LLM/RAG/embedding/vector/external: false",
            f"- Next actual operation: {report.get('next_actual_operation')}",
        ]
    ) + "\n"
