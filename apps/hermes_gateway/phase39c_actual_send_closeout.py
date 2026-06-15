"""Phase 39C actual send closeout, report-only.

This module records the user-observed Phase 39B private-test one-shot send
result. It never sends a Discord message.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase39c_actual_send_closeout_after_private_test_one_shot_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase39c_actual_send_closeout() -> dict[str, Any]:
    report = {
        "report_type": "phase39c_actual_send_closeout",
        "version": VERSION,
        "report_only": True,
        "phase39b_actual_send_observed": True,
        "phase39b_actual_send_success": True,
        "actual_discord_send_count": 1,
        "discord_api_send_called_in_phase39b": True,
        "discord_message_sent_in_phase39b": True,
        "message_sent_count_in_phase39b": 1,
        "send_scope": "private_test_only",
        "ready_for_phase39c_send_closeout": True,
        "phase39c_closeout_completed": True,
        "additional_discord_send_called_in_phase39c": False,
        "additional_discord_message_sent_in_phase39c": False,
        "additional_message_sent_count_in_phase39c": 0,
        "ready_for_repeat_send": False,
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "manual_retry_allowed": False,
        "unattended_auto_reply_allowed": False,
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
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
    }
    assert_phase39c_actual_send_closeout_safe(report)
    return report


def assert_phase39c_actual_send_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 39C closeout contains sensitive values.")
    if report.get("actual_discord_send_count") != 1 or report.get("message_sent_count_in_phase39b") != 1:
        raise ValueError("Phase 39C closeout must lock the Phase 39B send count to exactly 1.")
    if not report.get("phase39b_actual_send_success") or not report.get("phase39c_closeout_completed"):
        raise ValueError("Phase 39C closeout requires the observed Phase 39B success.")
    for key in (
        "additional_discord_send_called_in_phase39c",
        "additional_discord_message_sent_in_phase39c",
        "ready_for_repeat_send",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "manual_retry_allowed",
        "unattended_auto_reply_allowed",
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
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39C closeout unsafe flag is true: {key}")
    if int(report.get("additional_message_sent_count_in_phase39c", 0) or 0) != 0:
        raise ValueError("Phase 39C must not send an additional message.")


def render_phase39c_actual_send_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 39C Actual Send Closeout",
            "",
            "- Report only: true",
            "- Phase 39B actual send observed: true",
            "- Phase 39B actual send success: true",
            "- Actual Discord send count: 1",
            "- Phase 39C additional send count: 0",
            "- Send scope: private_test_only",
            "- Phase 39C closeout completed: true",
            "- Repeat send allowed: false",
        ]
    ) + "\n"
