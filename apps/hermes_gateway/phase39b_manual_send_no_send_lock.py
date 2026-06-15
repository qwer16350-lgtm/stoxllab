"""Phase 39B-0 no-send lock before actual private-test send."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase39b_manual_send_no_send_lock_before_actual_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase39b_manual_send_no_send_lock() -> dict[str, Any]:
    report = {
        "report_type": "phase39b_manual_send_no_send_lock",
        "version": VERSION,
        "report_only": True,
        "actual_discord_send_count": 0,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "actual_private_test_send_executed": False,
        "actual_send_executed": False,
        "phase39b_actual_send_not_executed_yet": True,
        "phase39c_closeout_not_available": True,
        "phase39c_closeout_reason": "no_actual_discord_message_sent",
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "unattended_auto_reply_allowed": False,
        "public_team_send_allowed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "secret_values_logged": False,
        "approval_phrase_generated": False,
        "manual_approval_actualized": False,
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "ready_for_phase39b_actual_send_manual_attempt": False,
        "ready_for_phase39c_send_closeout": False,
    }
    assert_phase39b_manual_send_no_send_lock_safe(report)
    return report


def assert_phase39b_manual_send_no_send_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 39B-0 no-send lock contains sensitive values.")
    for key in (
        "discord_api_send_called",
        "discord_message_sent",
        "actual_private_test_send_executed",
        "actual_send_executed",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "unattended_auto_reply_allowed",
        "public_team_send_allowed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "secret_values_logged",
        "approval_phrase_generated",
        "manual_approval_actualized",
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "ready_for_phase39b_actual_send_manual_attempt",
        "ready_for_phase39c_send_closeout",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39B-0 no-send lock unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 39B-0 no-send lock message sent count must be 0.")
    if int(report.get("actual_discord_send_count", 0) or 0) != 0:
        raise ValueError("Phase 39B-0 no-send lock actual send count must be 0.")


def render_phase39b_manual_send_no_send_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 39B Manual Send No-send Lock",
            "",
            "- Report only: true",
            "- Actual Discord send count: 0",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Actual private-test send executed: false",
            "- Phase 39B actual send not executed yet: true",
            "- Phase 39C closeout not available: true",
            "- Ready for Phase 39B actual send manual attempt: false",
            "- Ready for Phase 39C send closeout: false",
        ]
    ) + "\n"
