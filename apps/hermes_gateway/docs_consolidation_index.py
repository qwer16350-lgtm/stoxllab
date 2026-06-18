"""Report-only docs consolidation index for post-MVP Hermes docs."""

from __future__ import annotations

from typing import Any, Mapping

from safety_report_builders import base_no_external_action_report


SSOT_DOCS = [
    "docs/STOXL_HERMES_MVP_FINAL_CLOSEOUT.md",
    "docs/STOXL_HERMES_CURRENT_STATE.md",
    "docs/STOXL_HERMES_ALLOWED_MANUAL_GATES.md",
    "docs/STOXL_HERMES_PRODUCTION_ROADMAP.md",
    "docs/STOXL_HERMES_POST_MVP_COMPACTION_PLAN.md",
    "docs/STOXL_HERMES_PHASE_ARCHIVE_INDEX.md",
    "docs/STOXL_HERMES_DOCS_CONSOLIDATION_INDEX.md",
]

ACTIVE_OPERATOR_DOCS = [
    "docs/STOXL_HERMES_CURRENT_STATE.md",
    "docs/STOXL_HERMES_ALLOWED_MANUAL_GATES.md",
    "docs/STOXL_HERMES_PRODUCTION_ROADMAP.md",
]

MANUAL_GATE_DOCS = [
    "docs/STOXL_HERMES_ALLOWED_MANUAL_GATES.md",
]

HISTORICAL_PHASE_DOCS = [
    "docs/STOXL_PHASE74_LIMITED_AUTO_MODE_PREP.md",
    "docs/STOXL_PHASE67_72_SUPERVISED_TEAM_AUTO_OPS.md",
    "docs/STOXL_PHASE58_MANUAL_APPROVED_PRIVATE_TEST_REPLY.md",
]

ARCHIVE_CANDIDATE_DOCS = [
    {"pattern": "superseded phase-specific closeout docs", "recommendation_only": True},
    {"pattern": "duplicated manual gate notes already covered by SSOT docs", "recommendation_only": True},
    {"pattern": "older report-only prep docs already mapped to MVP registry", "recommendation_only": True},
]

DO_NOT_DELETE_DOCS = list(SSOT_DOCS)

FUTURE_MERGE_CANDIDATES = [
    {"source": "historical phase closeout docs", "target": "STOXL_HERMES_MVP_FINAL_CLOSEOUT.md"},
    {"source": "manual gate phase notes", "target": "STOXL_HERMES_ALLOWED_MANUAL_GATES.md"},
    {"source": "post-MVP compaction notes", "target": "STOXL_HERMES_POST_MVP_COMPACTION_PLAN.md"},
]


def build_hermes_docs_consolidation_index() -> dict[str, Any]:
    report = {
        **base_no_external_action_report(),
        "report_type": "hermes_docs_consolidation_index",
        "docs_consolidation_index_available": True,
        "delete_docs_now": False,
        "move_docs_now": False,
        "delete_files_now": False,
        "move_files_now": False,
        "archive_candidates_are_recommendations_only": True,
        "mvp_registry_is_current_ssot": True,
        "consumed_locks_authoritative": True,
        "production_unattended_ready": False,
        "ssot_docs": list(SSOT_DOCS),
        "active_operator_docs": list(ACTIVE_OPERATOR_DOCS),
        "manual_gate_docs": list(MANUAL_GATE_DOCS),
        "historical_phase_docs": list(HISTORICAL_PHASE_DOCS),
        "archive_candidate_docs": list(ARCHIVE_CANDIDATE_DOCS),
        "do_not_delete_docs": list(DO_NOT_DELETE_DOCS),
        "future_merge_candidates": list(FUTURE_MERGE_CANDIDATES),
        "ssot_docs_count": len(SSOT_DOCS),
        "active_operator_docs_count": len(ACTIVE_OPERATOR_DOCS),
        "manual_gate_docs_count": len(MANUAL_GATE_DOCS),
        "historical_phase_docs_count": len(HISTORICAL_PHASE_DOCS),
        "archive_candidate_docs_count": len(ARCHIVE_CANDIDATE_DOCS),
        "do_not_delete_docs_count": len(DO_NOT_DELETE_DOCS),
        "future_merge_candidates_count": len(FUTURE_MERGE_CANDIDATES),
        "secret_values_documented": False,
        "raw_channel_ids_documented": False,
        "approval_phrase_values_documented": False,
    }
    assert_docs_consolidation_index_safe(report)
    return report


def assert_docs_consolidation_index_safe(report: Mapping[str, Any]) -> None:
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
        "secret_values_documented",
        "raw_channel_ids_documented",
        "approval_phrase_values_documented",
    ):
        if report.get(key):
            raise ValueError(f"Docs consolidation unsafe flag is true: {key}")
    if report.get("delete_docs_now") or report.get("move_docs_now"):
        raise ValueError("Docs consolidation must not delete or move docs.")
    if report.get("delete_files_now") or report.get("move_files_now"):
        raise ValueError("Docs consolidation must not delete or move files.")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Docs consolidation reports must not send messages.")
