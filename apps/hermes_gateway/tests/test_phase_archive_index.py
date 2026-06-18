from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from mvp_state_registry import build_hermes_mvp_state_report, build_post_mvp_compaction_b_report
from phase60_65_team_canary_autonomy_stage import build_actual_phase60_team_canary
from phase67_72_supervised_team_auto_ops import build_actual_phase67_team_auto_ops
from phase74_limited_auto_mode_prep import build_actual_phase74_limited_auto_mode
from phase_archive_index import build_hermes_phase_archive_index, build_hermes_phase_archive_plan


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
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
    ):
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "No send count")


def test_phase_archive_index_exists_and_classifies() -> None:
    report = build_hermes_phase_archive_index()
    assert_true(report["report_type"] == "hermes_phase_archive_index", "Report type")
    assert_true(report["delete_files_now"] is False, "No delete")
    assert_true(report["move_files_now"] is False, "No move")
    for required in (
        "apps/hermes_gateway/cli.py",
        "apps/hermes_gateway/mvp_state_registry.py",
        "apps/hermes_gateway/manual_gate_helpers.py",
        "apps/hermes_gateway/safety_report_builders.py",
        "apps/hermes_gateway/phase60_65_team_canary_autonomy_stage.py",
        "apps/hermes_gateway/phase67_72_supervised_team_auto_ops.py",
        "apps/hermes_gateway/phase74_limited_auto_mode_prep.py",
    ):
        assert_true(required in report["do_not_delete"], required)
    assert_true(report["active_runtime_core_count"] == len(report["active_runtime_core"]), "Runtime count")
    assert_true(report["active_helper_count"] == len(report["active_helpers"]), "Helper count")
    assert_true(report["archive_candidate_count"] == len(report["archive_candidates"]), "Candidate count")
    assert_true(report["archive_candidates_are_recommendations_only"] is True, "Recommendation only")
    assert_true(report["manual_gate_behavior_weakened"] is False, "Manual gate not weakened")
    assert_true(report["consumed_locks_weakened"] is False, "Locks not weakened")
    assert_true(report["secret_redaction_weakened"] is False, "Redaction not weakened")
    assert_no_runtime_send_or_external(report)


def test_phase_archive_plan() -> None:
    report = build_hermes_phase_archive_plan()
    assert_true(report["report_type"] == "hermes_phase_archive_plan", "Report type")
    assert_true(report["safe_to_prepare_archive"] is True, "Safe to prepare")
    assert_true(report["delete_files_now"] is False, "No delete")
    assert_true(report["move_files_now"] is False, "No move")
    assert_true(report["archive_before_delete_required"] is True, "Archive before delete")
    assert_true("run full repeat-lock checks before any deletion" in report["recommended_next_steps"], "Repeat checks")
    assert_true("existing MVP state report commands" in report["do_not_change"], "CLI preserved")
    assert_no_runtime_send_or_external(report)


def test_repeat_locks_still_blocked() -> None:
    phase60 = build_actual_phase60_team_canary(allow_flag_present=True)
    phase67 = build_actual_phase67_team_auto_ops(allow_flag_present=True)
    phase74 = build_actual_phase74_limited_auto_mode(allow_flag_present=True)
    assert_true(phase60["blocked"] is True, "Phase60 blocked")
    assert_true(phase60["blocked_reasons"] == ["phase60_team_canary_already_consumed"], "Phase60 consumed")
    assert_true(phase67["blocked"] is True, "Phase67 blocked")
    assert_true(phase67["blocked_reasons"] == ["phase67_team_auto_ops_already_consumed"], "Phase67 consumed")
    assert_true(phase74["blocked"] is True, "Phase74 blocked")
    assert_true(phase74["blocked_reasons"] == ["phase74_limited_auto_mode_already_consumed"], "Phase74 consumed")
    for report in (phase60, phase67, phase74):
        assert_true(report["discord_api_send_called"] is False, "No API")
        assert_true(report["discord_message_sent"] is False, "No message")
        assert_true(report["message_sent_count"] == 0, "No send count")


def test_mvp_and_compaction_b_reports_still_pass() -> None:
    mvp = build_hermes_mvp_state_report()
    compaction_b = build_post_mvp_compaction_b_report()
    assert_true(mvp["mvp_supervised_discord_agent_os_complete"] is True, "MVP complete")
    assert_true(mvp["ready_for_production_unattended"] is False, "Production false")
    assert_true(compaction_b["manual_gate_helpers_available"] is True, "Manual helpers")
    assert_true(compaction_b["safety_report_builders_available"] is True, "Safety builders")
    assert_true(compaction_b["ready_for_next_compaction_stage"] is True, "Next ready")
    assert_no_runtime_send_or_external(compaction_b)


def main() -> int:
    tests = [
        test_phase_archive_index_exists_and_classifies,
        test_phase_archive_plan,
        test_repeat_locks_still_blocked,
        test_mvp_and_compaction_b_reports_still_pass,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All phase archive index tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
