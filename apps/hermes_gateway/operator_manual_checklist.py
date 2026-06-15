"""Phase 35E operator manual checklist.

Report-only checklist for a no-live operator rehearsal.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase35e_operator_manual_checklist_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_operator_manual_checklist() -> dict[str, Any]:
    report = {
        "report_type": "operator_manual_checklist",
        "version": VERSION,
        "checklist_available": True,
        "report_only": True,
        "human_review_required": True,
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
        "future_manual_gate_names": [
            "phase36_private_test_one_shot_llm_draft_preflight",
            "phase36_agent_review_packet_to_llm_draft_preview",
        ],
        "checklist_items": [
            {"item": "confirm_agent_review_packet", "required": True, "complete": False},
            {"item": "confirm_manual_approval_packet_preview", "required": True, "complete": False},
            {"item": "confirm_public_team_blocked", "required": True, "complete": True},
            {"item": "confirm_unattended_auto_reply_false", "required": True, "complete": True},
            {"item": "confirm_embedding_external_disabled", "required": True, "complete": True},
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
    assert_operator_manual_checklist_safe(report)
    return report


def assert_operator_manual_checklist_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Operator manual checklist contains sensitive values.")
    for key in (
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
            raise ValueError(f"Operator manual checklist unsafe flag is true: {key}")


def render_operator_manual_checklist_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Operator Manual Checklist",
            "",
            "- Checklist available: true",
            "- Report only: true",
            "- Human review required: true",
            "- Approval phrase generated: false",
            "- Ready for actual approval: false",
            "- Ready for live runtime: false",
            "- Ready for LLM call: false",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
            f"- Future manual gate names: {len(report.get('future_manual_gate_names', []))}",
        ]
    ) + "\n"
