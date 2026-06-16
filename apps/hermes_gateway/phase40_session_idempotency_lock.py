"""Phase 40F session/idempotency lock, report-only."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40_session_idempotency_lock_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_session_idempotency_lock() -> dict[str, Any]:
    report = {
        "report_type": "phase40_session_idempotency_lock",
        "version": VERSION,
        "report_only": True,
        "dedupe_key_strategy": "message_id",
        "one_reply_per_human_message": True,
        "duplicate_message_id_guard": True,
        "self_message_guard": True,
        "bot_message_guard": True,
        "duplicate_send_prevented": True,
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "manual_retry_allowed": False,
        "unattended_auto_reply_allowed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase40_session_idempotency_lock_safe(report)
    return report


def assert_phase40_session_idempotency_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40F idempotency lock contains sensitive values.")
    for key in (
        "one_reply_per_human_message",
        "duplicate_message_id_guard",
        "self_message_guard",
        "bot_message_guard",
        "duplicate_send_prevented",
    ):
        if not report.get(key):
            raise ValueError(f"Phase 40F required guard is false: {key}")
    for key in (
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "manual_retry_allowed",
        "unattended_auto_reply_allowed",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40F unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40F message_sent_count must remain 0.")


def render_phase40_session_idempotency_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40F Session Idempotency Lock",
            "",
            "- Report only: true",
            "- Dedupe key strategy: message_id",
            "- One reply per human message: true",
            "- Duplicate message id guard: true",
            "- Self message guard: true",
            "- Bot message guard: true",
            "- Repeat send allowed: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
