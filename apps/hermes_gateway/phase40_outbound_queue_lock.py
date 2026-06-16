"""Phase 40E outbound queue lock, no send worker."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40_outbound_queue_lock_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_outbound_queue_lock() -> dict[str, Any]:
    report = {
        "report_type": "phase40_outbound_queue_lock",
        "version": VERSION,
        "report_only": True,
        "outbound_queue_enabled": False,
        "queued_message_count": 0,
        "send_worker_enabled": False,
        "send_worker_started": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "manual_retry_requires_new_phase": True,
        "unattended_auto_reply_allowed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase40_outbound_queue_lock_safe(report)
    return report


def assert_phase40_outbound_queue_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40E outbound queue lock contains sensitive values.")
    if not report.get("manual_retry_requires_new_phase"):
        raise ValueError("Phase 40E manual retry must require a new phase.")
    for key in (
        "outbound_queue_enabled",
        "send_worker_enabled",
        "send_worker_started",
        "discord_api_send_called",
        "discord_message_sent",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "unattended_auto_reply_allowed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40E unsafe flag is true: {key}")
    if int(report.get("queued_message_count", 0) or 0) != 0 or int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40E queue and send counts must remain 0.")


def render_phase40_outbound_queue_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40E Outbound Queue Lock",
            "",
            "- Report only: true",
            "- Outbound queue enabled: false",
            "- Queued message count: 0",
            "- Send worker enabled: false",
            "- Send worker started: false",
            "- Repeat send allowed: false",
            "- Automatic retry allowed: false",
            "- Manual retry requires new phase: true",
        ]
    ) + "\n"
