"""Phase 40G operator handoff packet, before live runtime."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40_operator_handoff_packet_before_live_runtime"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_operator_handoff_packet() -> dict[str, Any]:
    report = {
        "report_type": "phase40_operator_handoff_packet",
        "version": VERSION,
        "report_only": True,
        "operator_must_confirm_before_live_runtime": True,
        "operator_must_confirm_before_any_reply_send": True,
        "required_future_confirmations": [
            "start_private_test_live_runtime",
            "allow_one_private_test_reply",
            "enable_llm_for_private_test_reply",
            "enable_rag_for_private_test_reply",
        ],
        "safe_current_state": True,
        "ready_for_phase40_live_runtime_entry_gate": True,
        "ready_for_live_runtime_execution": False,
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
    }
    assert_phase40_operator_handoff_packet_safe(report)
    return report


def assert_phase40_operator_handoff_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40G handoff packet contains sensitive values.")
    for key in (
        "operator_must_confirm_before_live_runtime",
        "operator_must_confirm_before_any_reply_send",
        "safe_current_state",
        "ready_for_phase40_live_runtime_entry_gate",
    ):
        if not report.get(key):
            raise ValueError(f"Phase 40G required handoff condition is false: {key}")
    for key in (
        "ready_for_live_runtime_execution",
        "discord_gateway_connected",
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
            raise ValueError(f"Phase 40G unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40G message_sent_count must remain 0.")


def render_phase40_operator_handoff_packet_markdown(report: dict[str, Any]) -> str:
    confirmations = "\n".join(f"- {item}" for item in report.get("required_future_confirmations", []))
    return "\n".join(
        [
            "# STOXL Phase 40G Operator Handoff Packet",
            "",
            "- Report only: true",
            "- Operator must confirm before live runtime: true",
            "- Operator must confirm before any reply send: true",
            "- Safe current state: true",
            "- Ready for live runtime execution: false",
            "",
            "## Required Future Confirmations",
            confirmations,
        ]
    ) + "\n"
