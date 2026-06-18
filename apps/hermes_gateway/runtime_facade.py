"""Report-only runtime facade for the post-MVP Hermes state.

The facade summarizes existing registry and phase reports. It does not run
Discord runtime, send messages, call LLM/RAG, execute external commands, or
start scheduler live execution.
"""

from __future__ import annotations

from typing import Any, Mapping

from mvp_state_registry import (
    build_hermes_mvp_state_report,
    build_post_mvp_compaction_b_report,
    build_post_mvp_compaction_d_report,
)
from phase60_65_team_canary_autonomy_stage import build_actual_phase60_team_canary
from phase67_72_supervised_team_auto_ops import build_actual_phase67_team_auto_ops
from phase74_limited_auto_mode_prep import build_actual_phase74_limited_auto_mode
from phase_archive_index import build_hermes_phase_archive_index, build_hermes_phase_archive_plan
from safety_report_builders import base_no_external_action_report


AVAILABLE_REPORT_GROUPS = [
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
]


def build_hermes_runtime_facade_report() -> dict[str, Any]:
    mvp = build_hermes_mvp_state_report()
    archive_index = build_hermes_phase_archive_index()
    archive_plan = build_hermes_phase_archive_plan()
    compaction_b = build_post_mvp_compaction_b_report()
    compaction_d = build_post_mvp_compaction_d_report()
    phase60 = build_actual_phase60_team_canary(allow_flag_present=True)
    phase67 = build_actual_phase67_team_auto_ops(allow_flag_present=True)
    phase74 = build_actual_phase74_limited_auto_mode(allow_flag_present=True)
    repeat_locked = all(
        report.get("blocked") is True and int(report.get("message_sent_count", 0) or 0) == 0
        for report in (phase60, phase67, phase74)
    )
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_runtime_facade_report",
        "facade_available": True,
        "report_only": True,
        "existing_cli_preserved": True,
        "mvp_supervised_discord_agent_os_complete": mvp.get("mvp_supervised_discord_agent_os_complete") is True,
        "current_verified_level": mvp.get("current_verified_level"),
        "ready_for_production_unattended": False,
        "production_unattended_ready": False,
        "available_report_groups": list(AVAILABLE_REPORT_GROUPS),
        "consumed_locks_preserved": repeat_locked,
        "manual_gate_behavior_weakened": False,
        "secret_redaction_weakened": False,
        "public_unknown_high_risk_blocking_weakened": False,
        "delete_files_now": False,
        "move_files_now": False,
        "phase_archive_index_available": archive_index.get("report_type") == "hermes_phase_archive_index",
        "phase_archive_plan_available": archive_plan.get("report_type") == "hermes_phase_archive_plan",
        "compaction_b_report_available": compaction_b.get("report_type") == "post_mvp_code_compaction_b",
        "compaction_d_report_available": compaction_d.get("report_type") == "post_mvp_code_compaction_d",
        "repeat_lock_status": {
            "phase60_team_canary": phase60.get("blocked_reasons") == ["phase60_team_canary_already_consumed"],
            "phase67_team_auto_ops": phase67.get("blocked_reasons") == ["phase67_team_auto_ops_already_consumed"],
            "phase74_limited_auto_mode": phase74.get("blocked_reasons") == ["phase74_limited_auto_mode_already_consumed"],
        },
    }
    assert_runtime_facade_safe(report)
    return report


def assert_runtime_facade_safe(report: Mapping[str, Any]) -> None:
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
            raise ValueError(f"Runtime facade unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Runtime facade reports must not send messages.")
    if int(report.get("reply_count", 0) or 0) != 0:
        raise ValueError("Runtime facade reports must not record live replies.")
    if report.get("delete_files_now") or report.get("move_files_now"):
        raise ValueError("Runtime facade must not delete or move files.")
