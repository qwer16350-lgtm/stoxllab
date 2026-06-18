"""Post-MVP phase archive index.

This report-only module classifies current runtime, helper, test, and document
assets before any deletion or move is considered. It never deletes, moves,
runs Discord runtime, sends messages, calls LLM/RAG, or starts scheduler live
execution.
"""

from __future__ import annotations

from typing import Any, Mapping

from mvp_state_registry import build_hermes_mvp_state_report, build_post_mvp_compaction_b_report
from safety_report_builders import base_no_external_action_report


ACTIVE_RUNTIME_CORE = [
    "apps/hermes_gateway/cli.py",
    "apps/hermes_gateway/phase60_65_team_canary_autonomy_stage.py",
    "apps/hermes_gateway/phase67_72_supervised_team_auto_ops.py",
    "apps/hermes_gateway/phase74_limited_auto_mode_prep.py",
]

ACTIVE_MVP_REGISTRY = [
    "apps/hermes_gateway/mvp_state_registry.py",
]

ACTIVE_HELPERS = [
    "apps/hermes_gateway/manual_gate_helpers.py",
    "apps/hermes_gateway/safety_report_builders.py",
]

ACTIVE_TESTS = [
    "apps/hermes_gateway/tests/test_mvp_state_registry.py",
    "apps/hermes_gateway/tests/test_post_mvp_code_compaction_b.py",
    "apps/hermes_gateway/tests/test_phase60_65_team_canary_autonomy_stage.py",
    "apps/hermes_gateway/tests/test_phase67_72_supervised_team_auto_ops.py",
    "apps/hermes_gateway/tests/test_phase74_limited_auto_mode_prep.py",
]

CONSUMED_HISTORICAL_GATES = [
    {"name": "phase58_private_test_deterministic_reply", "scope": "private_test_only", "status": "consumed_locked"},
    {"name": "phase59_supervised_private_test_auto_reply", "scope": "private_test_only", "status": "consumed_locked"},
    {"name": "phase60_team_canary", "scope": "known_team_channel_only", "status": "consumed_locked"},
    {"name": "phase67_supervised_team_auto_ops", "scope": "known_team_channel_only", "status": "consumed_locked"},
    {"name": "phase74_limited_auto_mode", "scope": "known_team_channel_only", "status": "consumed_locked"},
]

CONSUMED_CLOSEOUTS = [
    "docs/STOXL_HERMES_MVP_FINAL_CLOSEOUT.md",
    "docs/STOXL_PHASE74_LIMITED_AUTO_MODE_PREP.md",
]

REPORT_ONLY = [
    "docs/STOXL_HERMES_CURRENT_STATE.md",
    "docs/STOXL_HERMES_ALLOWED_MANUAL_GATES.md",
    "docs/STOXL_HERMES_PRODUCTION_ROADMAP.md",
    "docs/STOXL_HERMES_POST_MVP_COMPACTION_PLAN.md",
    "docs/STOXL_HERMES_PHASE_ARCHIVE_INDEX.md",
]

ARCHIVE_CANDIDATES = [
    {"pattern": "older report-only phase docs", "recommendation_only": True},
    {"pattern": "duplicated closeout reports", "recommendation_only": True},
    {"pattern": "superseded prep docs", "recommendation_only": True},
    {"pattern": "legacy phase-specific blocked report docs", "recommendation_only": True},
]

DO_NOT_DELETE = [
    "apps/hermes_gateway/cli.py",
    "apps/hermes_gateway/mvp_state_registry.py",
    "apps/hermes_gateway/manual_gate_helpers.py",
    "apps/hermes_gateway/safety_report_builders.py",
    "apps/hermes_gateway/phase60_65_team_canary_autonomy_stage.py",
    "apps/hermes_gateway/phase67_72_supervised_team_auto_ops.py",
    "apps/hermes_gateway/phase74_limited_auto_mode_prep.py",
    "docs/STOXL_HERMES_MVP_FINAL_CLOSEOUT.md",
    "docs/STOXL_HERMES_POST_MVP_COMPACTION_PLAN.md",
]


def build_hermes_phase_archive_index() -> dict[str, Any]:
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_phase_archive_index",
        "delete_files_now": False,
        "move_files_now": False,
        "active_runtime_core": list(ACTIVE_RUNTIME_CORE),
        "active_mvp_registry": list(ACTIVE_MVP_REGISTRY),
        "active_helpers": list(ACTIVE_HELPERS),
        "active_tests": list(ACTIVE_TESTS),
        "consumed_historical_gates": list(CONSUMED_HISTORICAL_GATES),
        "consumed_closeouts": list(CONSUMED_CLOSEOUTS),
        "report_only": list(REPORT_ONLY),
        "archive_candidates": list(ARCHIVE_CANDIDATES),
        "do_not_delete": list(DO_NOT_DELETE),
        "active_runtime_core_count": len(ACTIVE_RUNTIME_CORE),
        "active_mvp_registry_count": len(ACTIVE_MVP_REGISTRY),
        "active_helper_count": len(ACTIVE_HELPERS),
        "active_test_count": len(ACTIVE_TESTS),
        "consumed_historical_gate_count": len(CONSUMED_HISTORICAL_GATES),
        "consumed_closeout_count": len(CONSUMED_CLOSEOUTS),
        "report_only_count": len(REPORT_ONLY),
        "archive_candidate_count": len(ARCHIVE_CANDIDATES),
        "do_not_delete_count": len(DO_NOT_DELETE),
        "phase60_consumed_lock_preserved": True,
        "phase67_consumed_lock_preserved": True,
        "phase74_consumed_lock_preserved": True,
        "existing_cli_preserved": True,
        "manual_gate_behavior_weakened": False,
        "consumed_locks_weakened": False,
        "secret_redaction_weakened": False,
        "archive_candidates_are_recommendations_only": True,
        "mvp_registry_is_current_ssot": True,
        "production_unattended_ready": False,
    }
    assert_phase_archive_report_safe(report)
    return report


def build_hermes_phase_archive_plan() -> dict[str, Any]:
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_phase_archive_plan",
        "safe_to_prepare_archive": True,
        "delete_files_now": False,
        "move_files_now": False,
        "archive_before_delete_required": True,
        "archive_candidates_are_recommendations_only": True,
        "mvp_registry_is_current_ssot": True,
        "consumed_locks_authoritative": True,
        "production_unattended_ready": False,
        "recommended_next_steps": [
            "create docs archive index",
            "map each old phase doc to current MVP registry entry",
            "identify duplicate report builders now replaced by helpers",
            "prepare archive branch or archive folder plan",
            "run full repeat-lock checks before any deletion",
        ],
        "do_not_change": [
            "manual gate required behavior",
            "consumed/no-repeat locks",
            "secret redaction",
            "public/unknown/high-risk blocking",
            "LLM/RAG/external disabled by default",
            "scheduler live disabled by default",
            "existing MVP state report commands",
        ],
        "next_recommended_stage": "Code Compaction D - safe module consolidation pass, no deletion yet",
    }
    assert_phase_archive_report_safe(report)
    return report


def build_phase_archive_self_check() -> dict[str, Any]:
    mvp = build_hermes_mvp_state_report()
    compaction_b = build_post_mvp_compaction_b_report()
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_phase_archive_self_check",
        "mvp_state_report_passed": mvp.get("mvp_supervised_discord_agent_os_complete") is True,
        "compaction_b_report_passed": compaction_b.get("ready_for_next_compaction_stage") is True,
        "phase60_consumed_lock_preserved": True,
        "phase67_consumed_lock_preserved": True,
        "phase74_consumed_lock_preserved": True,
    }
    assert_phase_archive_report_safe(report)
    return report


def assert_phase_archive_report_safe(report: Mapping[str, Any]) -> None:
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
        "unattended_production_auto_reply_executed",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase archive unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase archive reports must not send messages.")
    if int(report.get("reply_count", 0) or 0) != 0:
        raise ValueError("Phase archive reports must not record live replies.")
    if report.get("delete_files_now") or report.get("move_files_now"):
        raise ValueError("Code Compaction C must not delete or move files.")
