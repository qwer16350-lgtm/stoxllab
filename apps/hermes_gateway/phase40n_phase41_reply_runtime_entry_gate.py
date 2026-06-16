"""Phase 40N Phase 41 reply runtime entry gate, blocked by default."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40n_phase41_reply_runtime_entry_gate_blocked_by_default"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40n_phase41_reply_runtime_entry_gate() -> dict[str, Any]:
    report = {
        "report_type": "phase40n_phase41_reply_runtime_entry_gate",
        "version": VERSION,
        "report_only": True,
        "phase41_reply_runtime_entry_gate_available": True,
        "phase41_reply_runtime_allowed": False,
        "required_before_phase41": [
            "phase40j manual readonly runtime completed",
            "phase40l live capture closeout completed",
            "no additional send during readonly runtime",
            "captured event audit passed",
            "operator approves one private-test reply runtime",
        ],
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "reply_send_allowed": False,
        "llm_reply_allowed": False,
        "rag_reply_allowed": False,
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
        "secret_values_logged": False,
        "ready_for_phase41_reply_runtime": False,
    }
    assert_phase40n_phase41_reply_runtime_entry_gate_safe(report)
    return report


def assert_phase40n_phase41_reply_runtime_entry_gate_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40N Phase 41 gate contains sensitive values.")
    if not report.get("phase41_reply_runtime_entry_gate_available"):
        raise ValueError("Phase 40N entry gate must be available.")
    for key in (
        "phase41_reply_runtime_allowed",
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "reply_send_allowed",
        "llm_reply_allowed",
        "rag_reply_allowed",
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
        "secret_values_logged",
        "ready_for_phase41_reply_runtime",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40N unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40N message_sent_count must remain 0.")


def render_phase40n_phase41_reply_runtime_entry_gate_markdown(report: dict[str, Any]) -> str:
    required = "\n".join(f"- {item}" for item in report.get("required_before_phase41", []))
    return "\n".join(
        [
            "# STOXL Phase 40N Phase 41 Reply Runtime Entry Gate",
            "",
            "- Report only: true",
            "- Phase 41 reply runtime entry gate available: true",
            "- Phase 41 reply runtime allowed: false",
            "- Reply send allowed: false",
            "- LLM reply allowed: false",
            "- RAG reply allowed: false",
            "- Ready for Phase 41 reply runtime: false",
            "",
            "## Required Before Phase 41",
            required,
        ]
    ) + "\n"
