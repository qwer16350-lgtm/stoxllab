from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from docs_consolidation_index import build_hermes_docs_consolidation_index
from mvp_state_registry import build_hermes_mvp_state_report
from phase60_65_team_canary_autonomy_stage import build_actual_phase60_team_canary
from phase67_72_supervised_team_auto_ops import build_actual_phase67_team_auto_ops
from phase74_limited_auto_mode_prep import build_actual_phase74_limited_auto_mode
from production_hardening import (
    CHECKLIST_CATEGORIES,
    REQUIRED_BEFORE_PRODUCTION_UNATTENDED,
    STOP_CONDITIONS,
    build_hermes_production_hardening_checklist,
    build_hermes_safe_launch_runbook,
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


def test_production_hardening_checklist() -> None:
    report = build_hermes_production_hardening_checklist()
    assert_true(report["report_type"] == "hermes_production_hardening_checklist", "Report type")
    assert_true(report["production_hardening_checklist_available"] is True, "Checklist exists")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    assert_true(report["mvp_supervised_discord_agent_os_complete"] is True, "MVP")
    assert_true(report["current_verified_level"] == "level4_limited_auto_mode_short_run_verified_once", "Level")
    assert_true(report["next_target_level"] == "production_hardening_dry_run_safety_audit", "Next")
    assert_true(report["checklist_categories"] == CHECKLIST_CATEGORIES, "Checklist categories")
    assert_true(
        set(report["required_before_production_unattended"].keys())
        == set(REQUIRED_BEFORE_PRODUCTION_UNATTENDED.keys()),
        "Required blockers present",
    )
    assert_true(
        all(value is False for value in report["required_before_production_unattended"].values()),
        "Required blockers false",
    )
    defaults = report["safety_defaults"]
    assert_true(defaults["manual_gate_required_for_real_send"] is True, "Manual Gate")
    assert_true(defaults["llm_rag_disabled_by_default"] is True, "LLM/RAG default")
    assert_true(defaults["external_execution_disabled_by_default"] is True, "External default")
    assert_true(defaults["scheduler_live_disabled_by_default"] is True, "Scheduler default")
    assert_true(defaults["public_unknown_high_risk_blocked"] is True, "Scope block")
    assert_true(defaults["secret_values_logged"] is False, "No secrets")
    assert_true(defaults["channel_id_values_logged"] is False, "No channel values")
    assert_true(report["runtime_facade_is_ssot"] is True, "Runtime facade SSOT")
    assert_true(report["docs_consolidation_index_is_ssot"] is True, "Docs index SSOT")
    assert_true(report["mvp_registry_is_ssot"] is True, "MVP registry SSOT")
    assert_true(report["consumed_locks_preserved"] is True, "Locks")
    assert_no_runtime_send_or_external(report)


def test_safe_launch_runbook() -> None:
    report = build_hermes_safe_launch_runbook()
    assert_true(report["report_type"] == "hermes_safe_launch_runbook", "Report type")
    assert_true(report["safe_launch_runbook_available"] is True, "Runbook exists")
    assert_true(report["production_unattended_launch_allowed"] is False, "Launch disallowed")
    assert_true(report["launch_mode"] == "not_production_unattended", "Launch mode")
    assert_true(report["manual_gate_required_for_next_live_action"] is True, "Manual Gate")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    assert_true(report["stop_conditions"] == STOP_CONDITIONS, "Stop conditions")
    stop_blob = "\n".join(report["stop_conditions"])
    for expected in (
        "secret value logged",
        "public or unknown channel send attempted",
        "high-risk intent auto reply attempted",
        "message_sent_count exceeds configured max",
        "LLM/RAG call attempted without explicit manual gate",
        "external execution attempted",
        "scheduler live starts without manual gate",
        "kill switch not ready",
    ):
        assert_true(expected in stop_blob, expected)
    assert_no_runtime_send_or_external(report)


def test_existing_reports_still_pass() -> None:
    assert_true(build_hermes_mvp_state_report()["mvp_supervised_discord_agent_os_complete"] is True, "MVP")
    assert_true(build_hermes_runtime_facade_report()["facade_available"] is True, "Runtime facade")
    assert_true(
        build_hermes_docs_consolidation_index()["docs_consolidation_index_available"] is True,
        "Docs index",
    )


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
        test_production_hardening_checklist,
        test_safe_launch_runbook,
        test_existing_reports_still_pass,
        test_repeat_locks_still_blocked_send_zero,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All production hardening tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
