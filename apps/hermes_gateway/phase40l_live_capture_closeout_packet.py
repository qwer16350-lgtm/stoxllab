"""Phase 40L live capture closeout packet, before live capture."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40l_live_capture_closeout_packet_before_live_capture"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40l_live_capture_closeout_packet() -> dict[str, Any]:
    report = {
        "report_type": "phase40l_live_capture_closeout_packet",
        "version": VERSION,
        "report_only": True,
        "capture_closeout_available": True,
        "live_capture_observed": False,
        "captured_event_count": 0,
        "captured_private_test_human_message_count": 0,
        "captured_self_message_count": 0,
        "captured_bot_message_count": 0,
        "captured_public_team_message_count": 0,
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
        "ready_for_capture_closeout_after_manual_runtime": False,
    }
    assert_phase40l_live_capture_closeout_packet_safe(report)
    return report


def assert_phase40l_live_capture_closeout_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40L capture closeout contains sensitive values.")
    if not report.get("capture_closeout_available"):
        raise ValueError("Phase 40L closeout packet must be available.")
    for key in (
        "live_capture_observed",
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
        "ready_for_capture_closeout_after_manual_runtime",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40L unsafe flag is true: {key}")
    for key in ("captured_event_count", "captured_private_test_human_message_count", "captured_self_message_count", "captured_bot_message_count", "captured_public_team_message_count", "message_sent_count"):
        if int(report.get(key, 0) or 0) != 0:
            raise ValueError(f"Phase 40L count must remain 0: {key}")


def render_phase40l_live_capture_closeout_packet_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40L Live Capture Closeout Packet",
            "",
            "- Report only: true",
            "- Capture closeout available: true",
            "- Live capture observed: false",
            "- Captured event count: 0",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for capture closeout after manual runtime: false",
        ]
    ) + "\n"
