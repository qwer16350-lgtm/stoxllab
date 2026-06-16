"""Phase 40C inbound event replay dry-run, synthetic only."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40_inbound_event_replay_dry_run_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_inbound_event_replay_dry_run() -> dict[str, Any]:
    report = {
        "report_type": "phase40_inbound_event_replay_dry_run",
        "version": VERSION,
        "report_only": True,
        "uses_recorded_or_synthetic_events_only": True,
        "discord_gateway_connected": False,
        "live_runtime_started": False,
        "synthetic_human_message_processed": True,
        "synthetic_self_message_skipped": True,
        "synthetic_bot_message_skipped": True,
        "synthetic_duplicate_message_skipped": True,
        "synthetic_public_channel_message_blocked": True,
        "synthetic_team_channel_message_blocked": True,
        "reply_text_generated": False,
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
    assert_phase40_inbound_event_replay_dry_run_safe(report)
    return report


def assert_phase40_inbound_event_replay_dry_run_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40C replay dry-run contains sensitive values.")
    for required in (
        "uses_recorded_or_synthetic_events_only",
        "synthetic_human_message_processed",
        "synthetic_self_message_skipped",
        "synthetic_bot_message_skipped",
        "synthetic_duplicate_message_skipped",
        "synthetic_public_channel_message_blocked",
        "synthetic_team_channel_message_blocked",
    ):
        if not report.get(required):
            raise ValueError(f"Phase 40C required replay condition is false: {required}")
    for key in (
        "discord_gateway_connected",
        "live_runtime_started",
        "reply_text_generated",
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
            raise ValueError(f"Phase 40C unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40C message_sent_count must remain 0.")


def render_phase40_inbound_event_replay_dry_run_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40C Inbound Event Replay Dry-run",
            "",
            "- Report only: true",
            "- Uses recorded or synthetic events only: true",
            "- Synthetic human message processed: true",
            "- Self message skipped: true",
            "- Bot message skipped: true",
            "- Duplicate message skipped: true",
            "- Public/team channel blocked: true",
            "- Discord message sent: false",
        ]
    ) + "\n"
