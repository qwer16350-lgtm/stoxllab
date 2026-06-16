"""Phase 40M runtime abort / kill-switch packet, report-only."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40m_runtime_abort_kill_switch_packet"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40m_runtime_abort_kill_switch_packet() -> dict[str, Any]:
    report = {
        "report_type": "phase40m_runtime_abort_kill_switch_packet",
        "version": VERSION,
        "report_only": True,
        "manual_abort_available": True,
        "abort_on_any_send_attempt": True,
        "abort_on_public_team_channel_event": True,
        "abort_on_unexpected_reply_mode": True,
        "abort_on_llm_enabled": True,
        "abort_on_rag_enabled": True,
        "abort_on_external_execution_enabled": True,
        "kill_switch_envs": [
            "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED=false",
            "HERMES_DISCORD_SEND_MESSAGES=false",
            "HERMES_DISCORD_PRIVATE_TEST_REPLY=false",
            "HERMES_DISCORD_REPLY_MODE=",
        ],
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "reply_send_allowed": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "secret_values_logged": False,
    }
    assert_phase40m_runtime_abort_kill_switch_packet_safe(report)
    return report


def assert_phase40m_runtime_abort_kill_switch_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40M kill switch contains sensitive values.")
    for key in (
        "manual_abort_available",
        "abort_on_any_send_attempt",
        "abort_on_public_team_channel_event",
        "abort_on_unexpected_reply_mode",
        "abort_on_llm_enabled",
        "abort_on_rag_enabled",
        "abort_on_external_execution_enabled",
    ):
        if not report.get(key):
            raise ValueError(f"Phase 40M required abort guard is false: {key}")
    for key in (
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "reply_send_allowed",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "secret_values_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40M unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40M message_sent_count must remain 0.")


def render_phase40m_runtime_abort_kill_switch_packet_markdown(report: dict[str, Any]) -> str:
    envs = "\n".join(f"- `{item}`" for item in report.get("kill_switch_envs", []))
    return "\n".join(
        [
            "# STOXL Phase 40M Runtime Abort Kill-switch Packet",
            "",
            "- Report only: true",
            "- Manual abort available: true",
            "- Abort on any send attempt: true",
            "- Abort on public/team channel event: true",
            "- Abort on LLM/RAG/external enabled: true",
            "",
            "## Kill-switch Envs",
            envs,
        ]
    ) + "\n"
