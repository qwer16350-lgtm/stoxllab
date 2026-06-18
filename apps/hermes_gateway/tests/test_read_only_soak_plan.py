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
from production_safety_audit import build_hermes_production_safety_audit
from read_only_soak_plan import (
    SOAK_PLAN_CATEGORIES,
    STOP_CONDITIONS,
    SUCCESS_CRITERIA,
    build_actual_read_only_live_soak_blocked,
    build_hermes_read_only_soak_plan,
    build_hermes_read_only_soak_preflight,
)


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


def test_read_only_soak_plan() -> None:
    report = build_hermes_read_only_soak_plan()
    assert_true(report["report_type"] == "hermes_read_only_soak_plan", "Report type")
    assert_true(report["read_only_soak_plan_available"] is True, "Plan exists")
    assert_true(report["live_runtime_executed"] is False, "No live runtime")
    assert_true(report["discord_gateway_live_connection_executed"] is False, "No gateway")
    assert_true(report["production_unattended_launch_allowed"] is False, "No production")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    assert_true(report["next_live_action_requires_manual_gate"] is True, "Manual Gate")
    assert_true(report["soak_plan_categories"] == SOAK_PLAN_CATEGORIES, "Categories")
    assert_true(report["soak_scope"] == "read_only_observation_only", "Scope")
    for key in (
        "send_messages_allowed",
        "reply_allowed",
        "llm_allowed",
        "rag_allowed",
        "external_execution_allowed",
        "scheduler_live_allowed",
    ):
        assert_true(report[key] is False, key)
    assert_true(report["recommended_duration_seconds"] == 300, "Duration")
    assert_true(report["recommended_max_events"] == 25, "Max events")
    assert_true(report["stop_conditions"] == STOP_CONDITIONS, "Stop conditions")
    stop_blob = "\n".join(report["stop_conditions"])
    for expected in (
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
    ):
        assert_true(expected in stop_blob, expected)
    assert_true(report["success_criteria"] == SUCCESS_CRITERIA, "Success criteria")
    success_blob = "\n".join(report["success_criteria"])
    for expected in (
        "gateway connects",
        "events captured as metadata only",
        "no send/reply",
        "no LLM/RAG/external/scheduler",
        "no raw/secrets/channel values",
        "operator can stop session",
        "post-soak review packet generated",
    ):
        assert_true(expected in success_blob, expected)
    assert_no_runtime_send_or_external(report)


def test_read_only_soak_preflight() -> None:
    report = build_hermes_read_only_soak_preflight(env={"HERMES_DISCORD_TOKEN": "present"})
    assert_true(report["report_type"] == "hermes_read_only_soak_preflight", "Report type")
    assert_true(report["manual_gate_required"] is True, "Manual Gate")
    assert_true(report["ready_for_read_only_soak_manual_gate"] is True, "Ready")
    assert_true(report["discord_token_present"] is True, "Token presence boolean")
    assert_true(report["discord_token_value_logged"] is False, "Token value hidden")
    for key in (
        "send_messages_allowed",
        "reply_allowed",
        "llm_allowed",
        "rag_allowed",
        "external_execution_allowed",
        "scheduler_live_allowed",
    ):
        assert_true(report[key] is False, key)
    assert_true(report["recommended_command"] == "manual_gate_read_only_soak_only", "Recommended command")
    assert_no_runtime_send_or_external(report)


def test_actual_read_only_soak_default_blocked() -> None:
    report = build_actual_read_only_live_soak_blocked(allow_flag_present=True)
    assert_true(report["report_type"] == "read_only_live_soak_blocked", "Report type")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["allow_flag_present"] is True, "Allow flag recorded")
    assert_true(report["actual_read_only_soak_executed"] is False, "No actual soak")
    assert_true(report["discord_gateway_live_connection_executed"] is False, "No gateway")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_no_runtime_send_or_external(report)


def test_existing_reports_still_pass() -> None:
    assert_true(
        build_hermes_production_safety_audit()["production_safety_audit_available"] is True,
        "Safety audit",
    )
    assert_true(
        build_hermes_production_hardening_checklist()["production_hardening_checklist_available"] is True,
        "Hardening",
    )
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
        test_read_only_soak_plan,
        test_read_only_soak_preflight,
        test_actual_read_only_soak_default_blocked,
        test_existing_reports_still_pass,
        test_repeat_locks_still_blocked_send_zero,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All read-only soak plan tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
