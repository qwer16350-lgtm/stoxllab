"""Phase 40R Phase 41 reply runtime preflight matrix."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40r_phase41_reply_preflight_matrix_blocked_by_default"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40r_phase41_reply_preflight_matrix() -> dict[str, Any]:
    report = {
        "report_type": "phase40r_phase41_reply_preflight_matrix",
        "version": VERSION,
        "report_only": True,
        "phase41_reply_runtime_entry_available": True,
        "phase41_reply_runtime_allowed": False,
        "required_before_phase41_reply": [
            "Phase 40O manual read-only runtime launched by user",
            "Phase 40Q capture review closeout completed",
            "No send occurred during read-only runtime",
            "At least one private-test human event reviewed",
            "Operator approves one reply-mode rehearsal",
            "Reply send remains blocked until separate Phase 41 send gate",
        ],
        "reply_text_generation_allowed": False,
        "llm_reply_allowed": False,
        "rag_reply_allowed": False,
        "discord_reply_send_allowed": False,
        "reply_send_allowed": False,
        "unattended_auto_reply_allowed": False,
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_phase41_reply_runtime": False,
    }
    assert_phase40r_phase41_reply_preflight_matrix_safe(report)
    return report


def assert_phase40r_phase41_reply_preflight_matrix_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40R matrix contains sensitive values.")
    if not report.get("phase41_reply_runtime_entry_available"):
        raise ValueError("Phase 40R entry must be available.")
    for key in (
        "phase41_reply_runtime_allowed",
        "reply_text_generation_allowed",
        "llm_reply_allowed",
        "rag_reply_allowed",
        "discord_reply_send_allowed",
        "reply_send_allowed",
        "unattended_auto_reply_allowed",
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_phase41_reply_runtime",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40R unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40R message_sent_count must remain 0.")


def render_phase40r_phase41_reply_preflight_matrix_markdown(report: dict[str, Any]) -> str:
    required = "\n".join(f"- {item}" for item in report.get("required_before_phase41_reply", []))
    return "\n".join(
        [
            "# STOXL Phase 40R Phase 41 Reply Preflight Matrix",
            "",
            "- Report only: true",
            "- Phase 41 reply runtime entry available: true",
            "- Phase 41 reply runtime allowed: false",
            "- Discord reply send allowed: false",
            "- LLM reply allowed: false",
            "- RAG reply allowed: false",
            "",
            "## Required Before Phase 41 Reply",
            required,
        ]
    ) + "\n"
