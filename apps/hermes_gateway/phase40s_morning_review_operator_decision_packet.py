"""Phase 40S morning review / operator decision packet."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40s_morning_review_operator_decision_packet"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40s_morning_review_operator_decision_packet() -> dict[str, Any]:
    report = {
        "report_type": "phase40s_morning_review_operator_decision_packet",
        "version": VERSION,
        "report_only": True,
        "safe_to_review_next_morning": True,
        "overnight_external_actions_executed_by_codex": False,
        "live_runtime_started_by_codex": False,
        "additional_discord_send_count": 0,
        "phase39_actual_send_count_locked": 1,
        "next_operator_choices": [
            "Run Phase 40O manual read-only runtime",
            "Review capture with Phase 40Q",
            "Proceed to Phase 41 reply rehearsal",
            "Stop before any reply/send",
        ],
        "recommended_next_phase": "Phase 40O manual read-only live runtime launch by user",
        "requires_user_confirmation": True,
        "reply_send_allowed": False,
        "phase41_reply_runtime_allowed": False,
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
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }
    assert_phase40s_morning_review_operator_decision_packet_safe(report)
    return report


def assert_phase40s_morning_review_operator_decision_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40S morning review contains sensitive values.")
    if not report.get("safe_to_review_next_morning") or not report.get("requires_user_confirmation"):
        raise ValueError("Phase 40S requires safe review and user confirmation.")
    if report.get("phase39_actual_send_count_locked") != 1 or int(report.get("additional_discord_send_count", 0) or 0) != 0:
        raise ValueError("Phase 40S send counts are invalid.")
    for key in (
        "overnight_external_actions_executed_by_codex",
        "live_runtime_started_by_codex",
        "reply_send_allowed",
        "phase41_reply_runtime_allowed",
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
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40S unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40S message_sent_count must remain 0.")


def render_phase40s_morning_review_operator_decision_packet_markdown(report: dict[str, Any]) -> str:
    choices = "\n".join(f"- {item}" for item in report.get("next_operator_choices", []))
    return "\n".join(
        [
            "# STOXL Phase 40S Morning Review Operator Decision Packet",
            "",
            "- Report only: true",
            "- Safe to review next morning: true",
            "- Live runtime started by Codex: false",
            "- Additional Discord send count: 0",
            "- Phase 39 actual send count locked: 1",
            "- Requires user confirmation: true",
            f"- Recommended next phase: {report.get('recommended_next_phase')}",
            "",
            "## Next Operator Choices",
            choices,
        ]
    ) + "\n"
