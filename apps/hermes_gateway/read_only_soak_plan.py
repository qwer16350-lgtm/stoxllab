"""Report-only read-only live soak plan and preflight.

This module prepares the next Manual Gate for observation-only live soak. It
does not connect to Discord Gateway, send messages, call LLM/RAG, execute
external commands, or start scheduler live execution.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

from production_safety_audit import build_hermes_production_safety_audit
from safety_report_builders import base_no_external_action_report, build_blocked_report


SOAK_PLAN_CATEGORIES = [
    "goal",
    "scope",
    "duration",
    "max_events",
    "capture_policy",
    "redaction_policy",
    "send_disabled",
    "llm_disabled",
    "rag_disabled",
    "external_disabled",
    "scheduler_disabled",
    "stop_conditions",
    "success_criteria",
    "operator_checklist",
    "post_soak_review",
]


STOP_CONDITIONS = [
    "any send attempted",
    "any reply attempted",
    "LLM or RAG call attempted",
    "external execution attempted",
    "scheduler live starts",
    "secret value logged",
    "raw Discord ID logged",
    "raw user content dumped",
    "event count exceeds configured max",
    "operator kill switch triggered",
]


SUCCESS_CRITERIA = [
    "gateway connects",
    "events captured as metadata only",
    "no send/reply",
    "no LLM/RAG/external/scheduler",
    "no raw/secrets/channel values",
    "operator can stop session",
    "post-soak review packet generated",
]


OPERATOR_CHECKLIST = [
    "confirm Manual Gate approval before actual soak",
    "confirm Discord send remains disabled",
    "confirm reply path remains disabled",
    "confirm LLM/RAG/external/scheduler remain disabled",
    "confirm metadata-only capture policy",
    "confirm operator stop procedure",
]


def build_hermes_read_only_soak_plan() -> dict[str, Any]:
    audit = build_hermes_production_safety_audit()
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_read_only_soak_plan",
        "read_only_soak_plan_available": True,
        "live_runtime_executed": False,
        "discord_gateway_live_connection_executed": False,
        "production_unattended_launch_allowed": False,
        "ready_for_production_unattended": False,
        "production_unattended_ready": False,
        "next_live_action_requires_manual_gate": True,
        "soak_plan_categories": list(SOAK_PLAN_CATEGORIES),
        "soak_scope": "read_only_observation_only",
        "send_messages_allowed": False,
        "reply_allowed": False,
        "llm_allowed": False,
        "rag_allowed": False,
        "external_execution_allowed": False,
        "scheduler_live_allowed": False,
        "recommended_duration_seconds": 300,
        "recommended_max_events": 25,
        "stop_conditions": list(STOP_CONDITIONS),
        "success_criteria": list(SUCCESS_CRITERIA),
        "operator_checklist": list(OPERATOR_CHECKLIST),
        "post_soak_review_required": True,
        "production_safety_audit_available": audit.get("production_safety_audit_available") is True,
        "passed_controls_preserved": all(audit.get("passed_controls", {}).values()),
        "delete_files_now": False,
        "move_files_now": False,
        "recommended_next_stage": "Manual Gate - actual read-only live soak, no send",
    }
    assert_read_only_soak_safe(report)
    return report


def build_hermes_read_only_soak_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env_map = os.environ if env is None else env
    token_present = bool(env_map.get("DISCORD_TOKEN") or env_map.get("HERMES_DISCORD_TOKEN"))
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_read_only_soak_preflight",
        "manual_gate_required": True,
        "ready_for_read_only_soak_manual_gate": True,
        "discord_token_present": token_present,
        "discord_token_value_logged": False,
        "send_messages_allowed": False,
        "reply_allowed": False,
        "llm_allowed": False,
        "rag_allowed": False,
        "external_execution_allowed": False,
        "scheduler_live_allowed": False,
        "recommended_command": "manual_gate_read_only_soak_only",
        "actual_discord_runtime_executed": False,
        "discord_gateway_live_connection_executed": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "delete_files_now": False,
        "move_files_now": False,
    }
    assert_read_only_soak_safe(report)
    return report


def build_actual_read_only_live_soak_blocked(allow_flag_present: bool = False) -> dict[str, Any]:
    report = build_blocked_report(
        "read_only_live_soak_blocked",
        ["actual_read_only_live_soak_requires_separate_manual_gate"],
        {
            "allow_flag_present": bool(allow_flag_present),
            "actual_read_only_soak_executed": False,
            "discord_gateway_live_connection_executed": False,
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
            "ready_for_read_only_soak_manual_gate": False,
            "send_messages_allowed": False,
            "reply_allowed": False,
            "llm_allowed": False,
            "rag_allowed": False,
            "external_execution_allowed": False,
            "scheduler_live_allowed": False,
            "delete_files_now": False,
            "move_files_now": False,
        },
    )
    assert_read_only_soak_safe(report)
    return report


def assert_read_only_soak_safe(report: Mapping[str, Any]) -> None:
    for key in (
        "actual_discord_runtime_executed",
        "live_runtime_executed",
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
        "cron_started",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
    ):
        if report.get(key):
            raise ValueError(f"Read-only soak unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Read-only soak reports must not send messages.")
    if int(report.get("reply_count", 0) or 0) != 0:
        raise ValueError("Read-only soak reports must not record live replies.")
    if report.get("ready_for_production_unattended") or report.get("production_unattended_ready"):
        raise ValueError("Production unattended must remain blocked.")
    if report.get("production_unattended_launch_allowed"):
        raise ValueError("Production unattended launch must remain disallowed.")
    if report.get("delete_files_now") or report.get("move_files_now"):
        raise ValueError("Read-only soak plan must not delete or move files.")
