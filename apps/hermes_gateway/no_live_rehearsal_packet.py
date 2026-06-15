"""Phase 35E no-live rehearsal packet."""

from __future__ import annotations

import json
import re
from typing import Any

from manual_approval_packet_preview import build_manual_approval_packet_preview
from operator_manual_checklist import build_operator_manual_checklist


VERSION = "phase35e_no_live_rehearsal_packet_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_no_live_rehearsal_packet() -> dict[str, Any]:
    checklist = build_operator_manual_checklist()
    approval = build_manual_approval_packet_preview()
    report = {
        "report_type": "no_live_rehearsal_packet",
        "version": VERSION,
        "rehearsal_available": True,
        "report_only": True,
        "operator_checklist_available": bool(checklist.get("checklist_available")),
        "manual_approval_packet_preview_available": bool(approval.get("approval_packet_preview_available")),
        "live_runtime_executed": False,
        "llm_called": False,
        "discord_message_sent": False,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "manual_approval_activated": False,
        "ready_for_actual_approval": False,
        "ready_for_live_runtime": False,
        "ready_for_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "ready_for_unattended_auto_reply": False,
        "rehearsal_steps": [
            "review_agent_review_packet",
            "review_manual_approval_packet_preview",
            "confirm_forbidden_behavior_sentinel",
            "confirm_phase36_entry_gate_before_any_future_live_work",
        ],
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "approval_phrase_generated": False,
            "live_runtime_executed": False,
            "embedding_called": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
        },
    }
    assert_no_live_rehearsal_packet_safe(report)
    return report


def assert_no_live_rehearsal_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("No-live rehearsal packet contains sensitive values.")
    for key in (
        "live_runtime_executed",
        "llm_called",
        "discord_message_sent",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "manual_approval_activated",
        "ready_for_actual_approval",
        "ready_for_live_runtime",
        "ready_for_llm_call",
        "ready_for_discord_send",
        "ready_for_embedding",
        "ready_for_external_sources",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"No-live rehearsal packet unsafe flag is true: {key}")


def render_no_live_rehearsal_packet_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL No-live Rehearsal Packet",
            "",
            "- Rehearsal available: true",
            "- Report only: true",
            "- Live runtime executed: false",
            "- LLM called: false",
            "- Discord message sent: false",
            "- Approval phrase generated: false",
            "- Ready for actual approval: false",
            "- Ready for live runtime: false",
            "- Ready for LLM call: false",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
        ]
    ) + "\n"
