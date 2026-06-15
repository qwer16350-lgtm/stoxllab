"""Phase 39C no-repeat send lock, report-only."""

from __future__ import annotations

import json
import re
from typing import Any

from phase39c_actual_send_closeout import build_phase39c_actual_send_closeout


VERSION = "phase39c_no_repeat_send_lock_after_actual_private_test_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase39c_no_repeat_send_lock(closeout: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_closeout = closeout or build_phase39c_actual_send_closeout()
    report = {
        "report_type": "phase39c_no_repeat_send_lock",
        "version": VERSION,
        "report_only": True,
        "phase39c_closeout_completed": bool(selected_closeout.get("phase39c_closeout_completed")),
        "actual_discord_send_count_locked": int(selected_closeout.get("actual_discord_send_count", 0) or 0),
        "max_allowed_actual_send_count": 1,
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "manual_retry_allowed": False,
        "unattended_auto_reply_allowed": False,
        "send_gate_must_remain_off": True,
        "real_execution_env_must_remain_off": True,
        "approval_gate_must_remain_off": True,
        "discord_api_send_called_in_phase39c": False,
        "discord_message_sent_in_phase39c": False,
        "message_sent_count_in_phase39c": 0,
        "ready_for_phase40_private_test_runtime_planning": True,
        "ready_for_repeat_send": False,
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
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
    }
    assert_phase39c_no_repeat_send_lock_safe(report)
    return report


def assert_phase39c_no_repeat_send_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 39C no-repeat lock contains sensitive values.")
    if report.get("actual_discord_send_count_locked") != 1:
        raise ValueError("Phase 39C no-repeat lock requires exactly one locked send.")
    for key in (
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "manual_retry_allowed",
        "unattended_auto_reply_allowed",
        "discord_api_send_called_in_phase39c",
        "discord_message_sent_in_phase39c",
        "ready_for_repeat_send",
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
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39C no-repeat unsafe flag is true: {key}")
    if int(report.get("message_sent_count_in_phase39c", 0) or 0) != 0:
        raise ValueError("Phase 39C no-repeat lock must not record a new message.")


def render_phase39c_no_repeat_send_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 39C No-repeat Send Lock",
            "",
            "- Report only: true",
            "- Actual Discord send count locked: 1",
            "- Max allowed actual send count: 1",
            "- Repeat send allowed: false",
            "- Automatic retry allowed: false",
            "- Manual retry allowed: false",
            "- Unattended auto reply allowed: false",
            "- Ready for repeat send: false",
        ]
    ) + "\n"
