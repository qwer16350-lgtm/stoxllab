"""Dry-run production safety audit and launch readiness scorecard.

These builders summarize remaining production blockers only. They do not run
Discord runtime, send messages, call LLM/RAG, execute external commands, or
start scheduler live execution.
"""

from __future__ import annotations

from typing import Any, Mapping

from mvp_state_registry import build_hermes_mvp_state_report
from production_hardening import (
    REQUIRED_BEFORE_PRODUCTION_UNATTENDED,
    SAFETY_DEFAULTS,
    build_hermes_production_hardening_checklist,
)
from runtime_facade import build_hermes_runtime_facade_report
from safety_report_builders import base_no_external_action_report


AUDIT_CATEGORIES = [
    "mvp_state",
    "manual_gate_integrity",
    "consumed_lock_integrity",
    "secret_redaction",
    "scope_control",
    "high_risk_blocking",
    "llm_rag_default_disabled",
    "external_execution_disabled",
    "scheduler_live_disabled",
    "runtime_live_disabled",
    "rate_limit_readiness",
    "cooldown_readiness",
    "kill_switch_readiness",
    "rollback_readiness",
    "audit_log_readiness",
    "operator_readiness",
    "cost_guard_readiness",
    "incident_stop_readiness",
]


REMAINING_REQUIRED_BEFORE_UNATTENDED = [
    "kill_switch_live_test",
    "rollback_runbook_test",
    "rate_limit_live_test",
    "audit_log_persistence_test",
    "read_only_live_soak",
    "scheduler_live_test",
    "production_env_review",
    "operator_oncall_assignment",
    "cost_guard_test",
    "incident_stop_drill",
]


def build_hermes_production_safety_audit() -> dict[str, Any]:
    mvp = build_hermes_mvp_state_report()
    runtime_facade = build_hermes_runtime_facade_report()
    hardening = build_hermes_production_hardening_checklist()
    safety_defaults = hardening.get("safety_defaults", SAFETY_DEFAULTS)
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_production_safety_audit",
        "dry_run_audit": True,
        "production_safety_audit_available": True,
        "audit_categories": list(AUDIT_CATEGORIES),
        "mvp_supervised_discord_agent_os_complete": mvp.get("mvp_supervised_discord_agent_os_complete") is True,
        "current_verified_level": mvp.get("current_verified_level"),
        "ready_for_production_unattended": False,
        "production_unattended_ready": False,
        "passed_controls": {
            "manual_gate_required_for_real_send": safety_defaults.get("manual_gate_required_for_real_send") is True,
            "consumed_locks_preserved": runtime_facade.get("consumed_locks_preserved") is True,
            "secret_redaction_preserved": True,
            "public_unknown_high_risk_blocked": safety_defaults.get("public_unknown_high_risk_blocked") is True,
            "llm_rag_disabled_by_default": safety_defaults.get("llm_rag_disabled_by_default") is True,
            "external_execution_disabled_by_default": safety_defaults.get("external_execution_disabled_by_default") is True,
            "scheduler_live_disabled_by_default": safety_defaults.get("scheduler_live_disabled_by_default") is True,
            "runtime_live_disabled_by_default": True,
        },
        "blocking_controls": dict(REQUIRED_BEFORE_PRODUCTION_UNATTENDED),
        "production_unattended_launch_allowed": False,
        "delete_files_now": False,
        "move_files_now": False,
        "recommended_next_stage": "production_hardening_H_read_only_live_soak_plan",
        "next_safe_action": "read_only_live_soak_plan_no_send",
    }
    assert_production_safety_audit_safe(report)
    return report


def build_hermes_launch_readiness_scorecard() -> dict[str, Any]:
    audit = build_hermes_production_safety_audit()
    passed_controls = audit["passed_controls"]
    blocking_controls = audit["blocking_controls"]
    safety_defaults_passed = all(passed_controls.values())
    live_ops_controls_passed = all(blocking_controls.values())
    operator_controls_passed = all(
        blocking_controls[key]
        for key in (
            "production_env_reviewed",
            "operator_oncall_defined",
            "incident_stop_procedure_tested",
        )
    )
    overall_ready = safety_defaults_passed and live_ops_controls_passed and operator_controls_passed
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_launch_readiness_scorecard",
        "dry_run_scorecard": True,
        "production_unattended_launch_allowed": False,
        "ready_for_production_unattended": False,
        "production_unattended_ready": False,
        "mvp_complete": audit.get("mvp_supervised_discord_agent_os_complete") is True,
        "score_summary": {
            "mvp_controls_passed": audit.get("mvp_supervised_discord_agent_os_complete") is True,
            "safety_defaults_passed": safety_defaults_passed,
            "live_ops_controls_passed": live_ops_controls_passed,
            "operator_controls_passed": operator_controls_passed,
            "overall_ready": overall_ready,
        },
        "remaining_required_before_unattended": list(REMAINING_REQUIRED_BEFORE_UNATTENDED),
        "next_safe_action": "read_only_live_soak_plan_no_send",
        "delete_files_now": False,
        "move_files_now": False,
    }
    assert_production_safety_audit_safe(report)
    return report


def assert_production_safety_audit_safe(report: Mapping[str, Any]) -> None:
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
            raise ValueError(f"Production safety audit unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Production safety audit reports must not send messages.")
    if int(report.get("reply_count", 0) or 0) != 0:
        raise ValueError("Production safety audit reports must not record live replies.")
    if report.get("ready_for_production_unattended") or report.get("production_unattended_ready"):
        raise ValueError("Production unattended must remain blocked.")
    if report.get("production_unattended_launch_allowed"):
        raise ValueError("Production unattended launch must remain disallowed.")
    if report.get("delete_files_now") or report.get("move_files_now"):
        raise ValueError("Production safety audit must not delete or move files.")
