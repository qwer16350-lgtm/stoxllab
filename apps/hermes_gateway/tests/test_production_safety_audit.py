from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from mvp_state_registry import build_hermes_mvp_state_report
from phase60_65_team_canary_autonomy_stage import build_actual_phase60_team_canary
from phase67_72_supervised_team_auto_ops import build_actual_phase67_team_auto_ops
from phase74_limited_auto_mode_prep import build_actual_phase74_limited_auto_mode
from production_hardening import build_hermes_production_hardening_checklist
from production_safety_audit import (
    AUDIT_CATEGORIES,
    REMAINING_REQUIRED_BEFORE_UNATTENDED,
    build_hermes_launch_readiness_scorecard,
    build_hermes_production_safety_audit,
)
from runtime_facade import build_hermes_runtime_facade_report


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_runtime_send_or_external(report: dict[str, object]) -> None:
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
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_true(report["reply_count"] == 0, "No reply count")


def test_production_safety_audit() -> None:
    report = build_hermes_production_safety_audit()
    assert_true(report["report_type"] == "hermes_production_safety_audit", "Report type")
    assert_true(report["dry_run_audit"] is True, "Dry run")
    assert_true(report["production_safety_audit_available"] is True, "Audit exists")
    assert_true(report["audit_categories"] == AUDIT_CATEGORIES, "Audit categories")
    assert_true(report["mvp_supervised_discord_agent_os_complete"] is True, "MVP")
    assert_true(report["current_verified_level"] == "level4_limited_auto_mode_short_run_verified_once", "Level")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    passed = report["passed_controls"]
    for key in (
        "manual_gate_required_for_real_send",
        "consumed_locks_preserved",
        "secret_redaction_preserved",
        "public_unknown_high_risk_blocked",
        "llm_rag_disabled_by_default",
        "external_execution_disabled_by_default",
        "scheduler_live_disabled_by_default",
        "runtime_live_disabled_by_default",
    ):
        assert_true(passed[key] is True, key)
    blocking = report["blocking_controls"]
    for key in (
        "kill_switch_live_tested",
        "rollback_runbook_tested",
        "rate_limit_live_tested",
        "audit_log_persistence_tested",
        "long_running_runtime_soak_tested",
        "scheduler_live_tested",
        "production_env_reviewed",
        "operator_oncall_defined",
        "cost_guard_tested",
        "incident_stop_procedure_tested",
    ):
        assert_true(blocking[key] is False, key)
    assert_true(report["production_unattended_launch_allowed"] is False, "Launch false")
    assert_true(report["recommended_next_stage"] == "production_hardening_H_read_only_live_soak_plan", "Next")
    assert_no_runtime_send_or_external(report)


def test_launch_readiness_scorecard() -> None:
    report = build_hermes_launch_readiness_scorecard()
    assert_true(report["report_type"] == "hermes_launch_readiness_scorecard", "Report type")
    assert_true(report["dry_run_scorecard"] is True, "Dry run")
    assert_true(report["production_unattended_launch_allowed"] is False, "Launch false")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    assert_true(report["mvp_complete"] is True, "MVP")
    summary = report["score_summary"]
    assert_true(summary["mvp_controls_passed"] is True, "MVP controls")
    assert_true(summary["safety_defaults_passed"] is True, "Safety controls")
    assert_true(summary["live_ops_controls_passed"] is False, "Live ops controls")
    assert_true(summary["operator_controls_passed"] is False, "Operator controls")
    assert_true(summary["overall_ready"] is False, "Overall")
    assert_true(
        report["remaining_required_before_unattended"] == REMAINING_REQUIRED_BEFORE_UNATTENDED,
        "Remaining required",
    )
    assert_true(report["next_safe_action"] == "read_only_live_soak_plan_no_send", "Next action")
    assert_no_runtime_send_or_external(report)


def test_existing_reports_still_pass() -> None:
    assert_true(
        build_hermes_production_hardening_checklist()["production_hardening_checklist_available"] is True,
        "Hardening",
    )
    assert_true(build_hermes_runtime_facade_report()["facade_available"] is True, "Runtime facade")
    assert_true(build_hermes_mvp_state_report()["mvp_supervised_discord_agent_os_complete"] is True, "MVP")


def test_repeat_locks_still_blocked_send_zero() -> None:
    phase60 = build_actual_phase60_team_canary(allow_flag_present=True)
    phase67 = build_actual_phase67_team_auto_ops(allow_flag_present=True)
    phase74 = build_actual_phase74_limited_auto_mode(allow_flag_present=True)
    assert_true(phase60["blocked_reasons"] == ["phase60_team_canary_already_consumed"], "Phase60")
    assert_true(phase67["blocked_reasons"] == ["phase67_team_auto_ops_already_consumed"], "Phase67")
    assert_true(phase74["blocked_reasons"] == ["phase74_limited_auto_mode_already_consumed"], "Phase74")
    for report in (phase60, phase67, phase74):
        assert_true(report["blocked"] is True, "Blocked")
        assert_true(report["discord_api_send_called"] is False, "No API send")
        assert_true(report["discord_message_sent"] is False, "No message")
        assert_true(report["message_sent_count"] == 0, "No send count")


def main() -> int:
    tests = [
        test_production_safety_audit,
        test_launch_readiness_scorecard,
        test_existing_reports_still_pass,
        test_repeat_locks_still_blocked_send_zero,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All production safety audit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
