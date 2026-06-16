"""Phase 40H live runtime entry gate, blocked by default."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40_live_runtime_entry_gate_blocked_by_default"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_live_runtime_entry_gate() -> dict[str, Any]:
    report = {
        "report_type": "phase40_live_runtime_entry_gate",
        "version": VERSION,
        "report_only": True,
        "live_runtime_entry_gate_available": True,
        "live_runtime_start_allowed": False,
        "required_future_flags": [
            "HERMES_PHASE40_PRIVATE_TEST_LIVE_RUNTIME_APPROVED=true",
            "HERMES_PHASE40_PRIVATE_TEST_LIVE_RUNTIME_APPROVAL_PHRASE exact",
            "HERMES_DISCORD_SEND_MESSAGES=false for read-only runtime",
            "HERMES_DISCORD_PRIVATE_TEST_REPLY=false until reply phase",
        ],
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
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "ready_for_live_runtime_execution": False,
    }
    assert_phase40_live_runtime_entry_gate_safe(report)
    return report


def assert_phase40_live_runtime_entry_gate_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    scrubbed = text.replace("HERMES_PHASE40_PRIVATE_TEST_LIVE_RUNTIME_APPROVAL_PHRASE exact", "")
    if SECRET_RE.search(scrubbed.lower()) or LONG_ID_RE.search(scrubbed) or APPROVAL_RE.search(scrubbed):
        raise ValueError("Phase 40H live runtime entry gate contains sensitive values.")
    if not report.get("live_runtime_entry_gate_available"):
        raise ValueError("Phase 40H live runtime entry gate must be available.")
    for key in (
        "live_runtime_start_allowed",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
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
        "ready_for_live_runtime_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40H unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40H message_sent_count must remain 0.")


def render_phase40_live_runtime_entry_gate_markdown(report: dict[str, Any]) -> str:
    flags = "\n".join(f"- {item}" for item in report.get("required_future_flags", []))
    return "\n".join(
        [
            "# STOXL Phase 40H Live Runtime Entry Gate",
            "",
            "- Report only: true",
            "- Live runtime entry gate available: true",
            "- Live runtime start allowed: false",
            "- Discord gateway connected: false",
            "- Discord message sent: false",
            "",
            "## Required Future Flags",
            flags,
        ]
    ) + "\n"
