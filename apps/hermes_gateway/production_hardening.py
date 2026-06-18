"""Report-only production hardening checklist and safe launch runbook.

These builders document what remains required before production unattended
mode. They do not run Discord runtime, send messages, call LLM/RAG, execute
external commands, or start scheduler live execution.
"""

from __future__ import annotations

from typing import Any, Mapping

from docs_consolidation_index import build_hermes_docs_consolidation_index
from mvp_state_registry import build_hermes_mvp_state_report
from runtime_facade import build_hermes_runtime_facade_report
from safety_report_builders import base_no_external_action_report


CHECKLIST_CATEGORIES = [
    "kill_switch",
    "rollback",
    "rate_limit",
    "cooldown",
    "max_session",
    "max_send_count",
    "max_reply_count",
    "audit_log",
    "secret_redaction",
    "channel_scope",
    "public_unknown_block",
    "high_risk_block",
    "llm_rag_disabled_by_default",
    "external_execution_disabled",
    "scheduler_live_disabled",
    "manual_gate_required",
    "operator_override",
    "repeat_lock_integrity",
    "env_presence_boolean_only",
    "dry_run_required_before_live",
]


REQUIRED_BEFORE_PRODUCTION_UNATTENDED = {
    "kill_switch_live_tested": False,
    "rollback_runbook_tested": False,
    "rate_limit_live_tested": False,
    "audit_log_persistence_tested": False,
    "long_running_runtime_soak_tested": False,
    "scheduler_live_tested": False,
    "production_env_reviewed": False,
    "operator_oncall_defined": False,
    "cost_guard_tested": False,
    "incident_stop_procedure_tested": False,
}


SAFETY_DEFAULTS = {
    "manual_gate_required_for_real_send": True,
    "llm_rag_disabled_by_default": True,
    "external_execution_disabled_by_default": True,
    "scheduler_live_disabled_by_default": True,
    "public_unknown_high_risk_blocked": True,
    "secret_values_logged": False,
    "channel_id_values_logged": False,
}


RECOMMENDED_LAUNCH_SEQUENCE = [
    "confirm MVP state report",
    "confirm runtime facade report",
    "confirm consumed lock inventory",
    "confirm production hardening checklist",
    "run dry-run safety audit",
    "run read-only live observation",
    "run supervised manual-gate short session",
    "review audit logs",
    "only then consider limited production unattended proposal",
]


STOP_CONDITIONS = [
    "secret value logged",
    "raw Discord ID logged",
    "public or unknown channel send attempted",
    "high-risk intent auto reply attempted",
    "message_sent_count exceeds configured max",
    "LLM/RAG call attempted without explicit manual gate",
    "external execution attempted",
    "scheduler live starts without manual gate",
    "kill switch not ready",
]


def build_hermes_production_hardening_checklist() -> dict[str, Any]:
    mvp = build_hermes_mvp_state_report()
    runtime_facade = build_hermes_runtime_facade_report()
    docs_index = build_hermes_docs_consolidation_index()
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_production_hardening_checklist",
        "production_hardening_checklist_available": True,
        "ready_for_production_unattended": False,
        "production_unattended_ready": False,
        "mvp_supervised_discord_agent_os_complete": mvp.get("mvp_supervised_discord_agent_os_complete") is True,
        "current_verified_level": mvp.get("current_verified_level"),
        "next_target_level": "production_hardening_dry_run_safety_audit",
        "checklist_categories": list(CHECKLIST_CATEGORIES),
        "required_before_production_unattended": dict(REQUIRED_BEFORE_PRODUCTION_UNATTENDED),
        "safety_defaults": dict(SAFETY_DEFAULTS),
        "runtime_facade_is_ssot": runtime_facade.get("facade_available") is True,
        "docs_consolidation_index_is_ssot": docs_index.get("docs_consolidation_index_available") is True,
        "mvp_registry_is_ssot": True,
        "consumed_locks_preserved": runtime_facade.get("consumed_locks_preserved") is True,
        "manual_gate_behavior_weakened": False,
        "consumed_locks_weakened": False,
        "secret_redaction_weakened": False,
        "public_unknown_high_risk_blocking_weakened": False,
        "delete_files_now": False,
        "move_files_now": False,
        "recommended_next_stage": "Production Hardening G - dry-run safety audit, no live action",
    }
    assert_production_hardening_safe(report)
    return report


def build_hermes_safe_launch_runbook() -> dict[str, Any]:
    checklist = build_hermes_production_hardening_checklist()
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_safe_launch_runbook",
        "safe_launch_runbook_available": True,
        "production_unattended_launch_allowed": False,
        "launch_mode": "not_production_unattended",
        "recommended_launch_sequence": list(RECOMMENDED_LAUNCH_SEQUENCE),
        "stop_conditions": list(STOP_CONDITIONS),
        "manual_gate_required_for_next_live_action": True,
        "ready_for_production_unattended": False,
        "production_unattended_ready": False,
        "required_before_production_unattended": dict(checklist["required_before_production_unattended"]),
        "safety_defaults": dict(checklist["safety_defaults"]),
        "delete_files_now": False,
        "move_files_now": False,
        "recommended_next_stage": "Production Hardening G - dry-run safety audit, no live action",
    }
    assert_production_hardening_safe(report)
    return report


def assert_production_hardening_safe(report: Mapping[str, Any]) -> None:
    for key in (
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
        "cron_started",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
    ):
        if report.get(key):
            raise ValueError(f"Production hardening unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Production hardening reports must not send messages.")
    if int(report.get("reply_count", 0) or 0) != 0:
        raise ValueError("Production hardening reports must not record live replies.")
    if report.get("ready_for_production_unattended") or report.get("production_unattended_ready"):
        raise ValueError("Production unattended must remain blocked.")
    if report.get("delete_files_now") or report.get("move_files_now"):
        raise ValueError("Production hardening must not delete or move files.")
