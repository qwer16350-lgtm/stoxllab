from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from docs_consolidation_index import build_hermes_docs_consolidation_index
from mvp_state_registry import (
    build_hermes_mvp_state_report,
    build_post_mvp_compaction_b_report,
    build_post_mvp_compaction_d_report,
)
from phase60_65_team_canary_autonomy_stage import build_actual_phase60_team_canary
from phase67_72_supervised_team_auto_ops import build_actual_phase67_team_auto_ops
from phase74_limited_auto_mode_prep import build_actual_phase74_limited_auto_mode
from phase_archive_index import build_hermes_phase_archive_index, build_hermes_phase_archive_plan
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
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
    ):
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "No send count")


def test_runtime_facade_report() -> None:
    report = build_hermes_runtime_facade_report()
    assert_true(report["report_type"] == "hermes_runtime_facade_report", "Report type")
    assert_true(report["facade_available"] is True, "Facade")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["existing_cli_preserved"] is True, "CLI preserved")
    assert_true(report["mvp_supervised_discord_agent_os_complete"] is True, "MVP")
    assert_true(report["current_verified_level"] == "level4_limited_auto_mode_short_run_verified_once", "Level")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    for group in (
        "mvp_state",
        "manual_gate_inventory",
        "compaction_plan",
        "phase_archive_index",
        "phase_archive_plan",
        "compaction_b_report",
        "compaction_d_report",
        "phase60_report",
        "phase67_report",
        "phase74_report",
        "repeat_lock_status",
        "production_readiness",
    ):
        assert_true(group in report["available_report_groups"], group)
    assert_true(report["consumed_locks_preserved"] is True, "Locks")
    assert_true(report["delete_files_now"] is False, "No delete")
    assert_true(report["move_files_now"] is False, "No move")
    assert_no_runtime_send_or_external(report)


def test_docs_consolidation_index() -> None:
    report = build_hermes_docs_consolidation_index()
    assert_true(report["report_type"] == "hermes_docs_consolidation_index", "Report type")
    assert_true(report["docs_consolidation_index_available"] is True, "Docs index")
    assert_true(report["delete_docs_now"] is False, "No docs delete")
    assert_true(report["move_docs_now"] is False, "No docs move")
    assert_true(report["archive_candidates_are_recommendations_only"] is True, "Recommendations only")
    assert_true(report["ssot_docs_count"] == len(report["ssot_docs"]), "SSOT count")
    assert_true(report["do_not_delete_docs_count"] == len(report["do_not_delete_docs"]), "Do not delete count")
    assert_true("docs/STOXL_HERMES_MVP_FINAL_CLOSEOUT.md" in report["do_not_delete_docs"], "MVP final doc")
    assert_true("docs/STOXL_HERMES_DOCS_CONSOLIDATION_INDEX.md" in report["ssot_docs"], "Docs index doc")
    assert_true(report["secret_values_documented"] is False, "No secret values")
    assert_true(report["raw_channel_ids_documented"] is False, "No channel values")
    assert_true(report["approval_phrase_values_documented"] is False, "No approval values")
    assert_no_runtime_send_or_external(report)


def test_existing_reports_and_repeat_locks() -> None:
    assert_true(build_hermes_mvp_state_report()["mvp_supervised_discord_agent_os_complete"] is True, "MVP")
    assert_true(build_post_mvp_compaction_b_report()["ready_for_next_compaction_stage"] is True, "B")
    assert_true(build_post_mvp_compaction_d_report()["ready_for_next_compaction_stage"] is True, "D")
    assert_true(build_hermes_phase_archive_index()["delete_files_now"] is False, "Archive index")
    assert_true(build_hermes_phase_archive_plan()["move_files_now"] is False, "Archive plan")
    phase60 = build_actual_phase60_team_canary(allow_flag_present=True)
    phase67 = build_actual_phase67_team_auto_ops(allow_flag_present=True)
    phase74 = build_actual_phase74_limited_auto_mode(allow_flag_present=True)
    assert_true(phase60["blocked_reasons"] == ["phase60_team_canary_already_consumed"], "Phase60")
    assert_true(phase67["blocked_reasons"] == ["phase67_team_auto_ops_already_consumed"], "Phase67")
    assert_true(phase74["blocked_reasons"] == ["phase74_limited_auto_mode_already_consumed"], "Phase74")
    for report in (phase60, phase67, phase74):
        assert_true(report["blocked"] is True, "Blocked")
        assert_true(report["discord_message_sent"] is False, "No send")
        assert_true(report["message_sent_count"] == 0, "No send count")


def main() -> int:
    tests = [
        test_runtime_facade_report,
        test_docs_consolidation_index,
        test_existing_reports_and_repeat_locks,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Post-MVP Code Compaction E tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
