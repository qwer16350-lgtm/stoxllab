"""Phase 38D private-test send operator final checklist, no send."""

from __future__ import annotations

import json
import re
from typing import Any

from private_test_send_rollback_gate import build_private_test_send_rollback_gate


VERSION = "phase38d_private_test_send_operator_checklist_no_send"
REQUIRED_MANUAL_CHECKS = [
    "working_tree_clean",
    "validator_errors_zero",
    "relevant_tests_passed",
    "discord_token_presence_boolean_checked",
    "private_test_channel_presence_boolean_checked",
    "approval_false_by_default",
    "public_team_forbidden",
    "unattended_auto_reply_false",
    "payload_preview_human_reviewed",
    "final_send_command_not_run",
]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_private_test_send_operator_checklist(rollback_gate: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_gate = rollback_gate or build_private_test_send_rollback_gate()
    report = {
        "report_type": "private_test_send_operator_checklist",
        "version": VERSION,
        "operator_checklist_available": True,
        "report_only": True,
        "source_phase38c_rollback_gate_available": bool(selected_gate.get("rollback_gate_available")),
        "operator_checklist_ready": True,
        "required_manual_checks": REQUIRED_MANUAL_CHECKS,
        "approval_false_by_default": True,
        "final_send_command_not_run": True,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "manual_approval_actualized": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "actual_send_implementation_executed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_phase38e_live_send_entry_gate": True,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
    }
    assert_private_test_send_operator_checklist_safe(report)
    return report


def assert_private_test_send_operator_checklist_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 38D operator checklist contains sensitive values.")
    if not report.get("source_phase38c_rollback_gate_available"):
        raise ValueError("Phase 38D requires Phase 38C rollback gate.")
    if report.get("required_manual_checks") != REQUIRED_MANUAL_CHECKS:
        raise ValueError("Phase 38D manual checks changed.")
    for key in (
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "manual_approval_actualized",
        "discord_api_send_called",
        "discord_message_sent",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_live_runtime_executed",
        "actual_send_implementation_executed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_actual_private_test_send",
        "ready_for_discord_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 38D unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 38D message sent count must be 0.")


def render_private_test_send_operator_checklist_markdown(report: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{item}`" for item in report.get("required_manual_checks", []))
    return "\n".join(
        [
            "# STOXL Private-test Send Operator Checklist",
            "",
            "- Operator checklist available: true",
            "- Report only: true",
            "- Operator checklist ready: true",
            "",
            "## Required Manual Checks",
            checks,
            "",
            "- Manual approval actualized: false",
            "- Approval phrase generated: false",
            "- Final send command not run: true",
            "- Ready for Phase 38E live send entry gate: true",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
        ]
    ) + "\n"
