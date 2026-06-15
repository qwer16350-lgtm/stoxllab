"""Phase 39A actual private-test send blocked report."""

from __future__ import annotations

import json
import re
from typing import Any

from actual_private_test_send_safety_gate import build_actual_private_test_send_safety_gate


VERSION = "phase39a_actual_private_test_send_blocked_report"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_actual_private_test_send_blocked_report(safety_gate: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_gate = safety_gate or build_actual_private_test_send_safety_gate()
    report = {
        "report_type": "actual_private_test_send_blocked_report",
        "version": VERSION,
        "blocked_report_available": True,
        "report_only": True,
        "source_safety_gate_available": bool(selected_gate.get("safety_gate_available")),
        "blocked": True,
        "blocked_reason_categories": [
            "manual_approval_missing",
            "allow_flag_missing",
            "discord_send_disabled",
            "phase39a_no_execution_policy",
        ],
        "phase39a_no_execution_policy": True,
        "actual_send_executed": False,
        "actual_private_test_send_executed": False,
        "discord_live_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "ready_for_phase39b_manual_one_shot_send": False,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "manual_approval_actualized": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_actual_private_test_send_blocked_report_safe(report)
    return report


def assert_actual_private_test_send_blocked_report_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 39A blocked report contains sensitive values.")
    if not report.get("blocked") or not report.get("phase39a_no_execution_policy"):
        raise ValueError("Phase 39A blocked report must stay blocked by policy.")
    for key in (
        "actual_send_executed",
        "actual_private_test_send_executed",
        "discord_live_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "ready_for_actual_private_test_send",
        "ready_for_discord_send",
        "ready_for_phase39b_manual_one_shot_send",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "manual_approval_actualized",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39A blocked report unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 39A blocked report message sent count must be 0.")


def render_actual_private_test_send_blocked_report_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Actual Private-test Send Blocked Report",
            "",
            "- Blocked report available: true",
            "- Report only: true",
            "- Blocked: true",
            "- Phase 39A no-execution policy: true",
            "- Actual send executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
        ]
    ) + "\n"
