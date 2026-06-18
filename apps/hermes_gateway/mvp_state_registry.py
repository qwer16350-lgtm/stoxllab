"""Post-MVP Hermes state registry.

This module freezes the supervised Discord Agent OS MVP state as report-only
data. It does not run Discord runtime, send messages, call LLM/RAG, start
scheduler live execution, or move/delete files.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from safety_report_builders import base_no_external_action_report


VERSION = "post_mvp_compaction_a_state_registry"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


VERIFIED_LEVELS: dict[str, str] = {
    "level_1": "read_only_observation_verified",
    "level_2": "manual_deterministic_reply_verified",
    "level_3": "supervised_private_test_auto_reply_verified",
    "level_4_canary": "low_risk_team_channel_canary_verified_once",
    "level_4_auto_ops": "supervised_team_channel_auto_ops_verified_once",
    "level_4_limited_auto": "limited_auto_mode_short_run_verified_once",
    "level_5": "production_unattended_not_ready",
}

MANUAL_GATES: list[dict[str, str]] = [
    {"name": "phase39_private_test_one_shot_send", "status": "consumed_locked", "scope": "private_test_only"},
    {"name": "phase41_private_test_reply", "status": "consumed_locked", "scope": "private_test_only"},
    {"name": "phase42_supervised_private_test_session", "status": "consumed_locked", "scope": "private_test_only"},
    {"name": "phase45_llm_one_shot", "status": "consumed_locked", "scope": "llm_only_no_discord_send"},
    {"name": "phase58_private_test_reply", "status": "consumed_locked", "scope": "private_test_only"},
    {"name": "phase59_supervised_private_test_auto_reply", "status": "consumed_locked", "scope": "private_test_only"},
    {"name": "phase60_team_canary", "status": "consumed_locked", "scope": "known_team_channel_only"},
    {"name": "phase67_supervised_team_auto_ops", "status": "consumed_locked", "scope": "known_team_channel_only"},
    {"name": "phase74_limited_auto_mode_short_run", "status": "consumed_locked", "scope": "known_team_channel_only"},
]

CONSUMED_LOCKS: dict[str, bool] = {
    "phase58_private_test_reply": True,
    "phase59_supervised_private_test_auto_reply": True,
    "phase60_team_canary": True,
    "phase67_team_auto_ops": True,
    "phase74_limited_auto_mode": True,
}

SAFE_REPORT_COMMANDS = [
    "--hermes-mvp-state-report",
    "--hermes-manual-gate-inventory",
    "--hermes-post-mvp-compaction-plan",
    "--hermes-mvp-final-closeout",
    "--phase74-limited-auto-closeout",
]

ACTUAL_MANUAL_GATE_COMMANDS = [
    "--actual-phase58-manual-approved-private-test-reply",
    "--actual-phase59-supervised-private-test-auto-reply",
    "--actual-phase60-team-canary",
    "--actual-phase67-team-auto-ops",
    "--actual-phase74-limited-auto-mode",
]

CLOSEOUT_COMMANDS = [
    "--phase58-manual-approved-private-test-reply-closeout",
    "--phase60-team-canary-closeout",
    "--phase67-team-auto-ops-closeout",
    "--phase74-limited-auto-closeout",
    "--hermes-mvp-final-closeout",
]

PRODUCTION_BLOCKERS = [
    "production_unattended_not_approved",
    "scheduler_live_not_approved",
    "long_running_runtime_not_approved",
    "llm_rag_live_team_reply_not_approved",
    "public_or_unrestricted_team_auto_reply_not_approved",
    "post_mvp_refactor_and_compaction_not_complete",
]

NEXT_REFACTOR_TARGETS = [
    "consolidate phase report builders into shared state registry",
    "deduplicate manual gate env parsing",
    "deduplicate blocked report builders",
    "deduplicate send result safety assertions",
    "centralize consumed lock policy",
    "centralize allowed scopes and forbidden scopes",
    "archive old docs by index before deleting anything",
]

FORBIDDEN_PATHS = [
    ".env",
    "exports/",
    "logs/",
    "apps/hermes_gateway/local/*",
]

DO_NOT_CHANGE = [
    "manual gate required behavior",
    "consumed/no-repeat locks",
    "secret redaction",
    "public/unknown/high-risk blocking",
    "LLM/RAG/external disabled by default",
    "scheduler live disabled by default",
]


def _safe_runtime_flags() -> dict[str, Any]:
    return {
        "actual_discord_runtime_executed": False,
        "discord_gateway_live_connection_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "reply_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_live_execution": False,
        "cron_started": False,
        "unattended_production_auto_reply_executed": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "raw_session_ids_logged": False,
        "secret_values_logged": False,
        "approval_phrase_value_logged": False,
        "team_channel_id_value_logged": False,
    }


def _base_state() -> dict[str, Any]:
    return {
        "version": VERSION,
        "mvp_supervised_discord_agent_os_complete": True,
        "current_verified_level": "level4_limited_auto_mode_short_run_verified_once",
        "next_target_level": "production_hardening_refactor_compaction",
        "ready_for_production_unattended": False,
        "production_unattended_ready": False,
        "verified_levels": dict(VERIFIED_LEVELS),
        "consumed_locks": dict(CONSUMED_LOCKS),
    }


def build_hermes_mvp_state_report() -> dict[str, Any]:
    report = {
        **_base_state(),
        **_safe_runtime_flags(),
        "report_type": "hermes_mvp_state_report",
        "manual_gates": list(MANUAL_GATES),
        "safe_report_commands": list(SAFE_REPORT_COMMANDS),
        "actual_manual_gate_commands": list(ACTUAL_MANUAL_GATE_COMMANDS),
        "closeout_commands": list(CLOSEOUT_COMMANDS),
        "production_blockers": list(PRODUCTION_BLOCKERS),
        "next_refactor_targets": list(NEXT_REFACTOR_TARGETS),
        "forbidden_paths": list(FORBIDDEN_PATHS),
    }
    assert_mvp_state_report_safe(report)
    return report


def build_hermes_manual_gate_inventory() -> dict[str, Any]:
    report = {
        **_safe_runtime_flags(),
        "version": VERSION,
        "report_type": "hermes_manual_gate_inventory",
        "manual_gates": list(MANUAL_GATES),
        "consumed_locks": dict(CONSUMED_LOCKS),
        "approval_phrase_values_logged": False,
        "token_values_logged": False,
        "channel_id_values_logged": False,
        "team_channel_id_value_logged": False,
    }
    assert_mvp_state_report_safe(report)
    return report


def build_hermes_post_mvp_compaction_plan() -> dict[str, Any]:
    report = {
        **_base_state(),
        **_safe_runtime_flags(),
        "report_type": "hermes_post_mvp_compaction_plan",
        "safe_to_start_compaction": True,
        "delete_files_now": False,
        "move_files_now": False,
        "production_unattended_ready": False,
        "recommended_next_steps": list(NEXT_REFACTOR_TARGETS),
        "do_not_change": list(DO_NOT_CHANGE),
        "forbidden_paths": list(FORBIDDEN_PATHS),
    }
    assert_mvp_state_report_safe(report)
    return report


def build_post_mvp_compaction_b_report() -> dict[str, Any]:
    report = {
        **base_no_external_action_report(),
        "version": VERSION,
        "report_type": "post_mvp_code_compaction_b",
        "manual_gate_helpers_available": True,
        "safety_report_builders_available": True,
        "phase60_helpers_integrated": True,
        "phase67_helpers_integrated": True,
        "phase74_helpers_integrated": True,
        "existing_cli_preserved": True,
        "manual_gate_behavior_weakened": False,
        "consumed_locks_weakened": False,
        "secret_redaction_weakened": False,
        "public_unknown_high_risk_blocking_weakened": False,
        "delete_files_now": False,
        "move_files_now": False,
        "ready_for_next_compaction_stage": True,
        "next_target_level": "code_compaction_c_runtime_doc_index_before_deletion",
        "recommended_next_stage": "Code Compaction C - consolidate old phase docs/runtime index before deletion",
    }
    assert_mvp_state_report_safe(report)
    return report


def build_post_mvp_compaction_d_report() -> dict[str, Any]:
    report = {
        **base_no_external_action_report(),
        "version": VERSION,
        "report_type": "post_mvp_code_compaction_d",
        "phase_policy_builders_available": True,
        "phase60_policy_helpers_integrated": True,
        "phase67_policy_helpers_integrated": True,
        "phase74_policy_helpers_integrated": True,
        "existing_cli_preserved": True,
        "delete_files_now": False,
        "move_files_now": False,
        "manual_gate_behavior_weakened": False,
        "consumed_locks_weakened": False,
        "secret_redaction_weakened": False,
        "public_unknown_high_risk_blocking_weakened": False,
        "ready_for_next_compaction_stage": True,
        "next_target_level": "code_compaction_e_archive_safe_doc_consolidation_or_runtime_facade",
        "recommended_next_stage": "Code Compaction E - small archive-safe doc consolidation or runtime facade, no deletion yet",
    }
    assert_mvp_state_report_safe(report)
    return report


def assert_mvp_state_report_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("MVP state registry report contains sensitive values.")
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
            raise ValueError(f"MVP state registry unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("MVP state registry reports must not send messages.")
    if int(report.get("reply_count", 0) or 0) != 0:
        raise ValueError("MVP state registry reports must not record live replies.")
    if report.get("ready_for_production_unattended") or report.get("production_unattended_ready"):
        raise ValueError("MVP state registry must keep production unattended not ready.")
    if report.get("delete_files_now") or report.get("move_files_now"):
        raise ValueError("Post-MVP compaction A must not delete or move files.")
