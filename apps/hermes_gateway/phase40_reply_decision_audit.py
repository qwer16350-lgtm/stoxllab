"""Phase 40D reply decision audit, no send."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40_reply_decision_audit_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_reply_decision_audit() -> dict[str, Any]:
    report = {
        "report_type": "phase40_reply_decision_audit",
        "version": VERSION,
        "report_only": True,
        "private_test_human_message_decision": "eligible_for_future_manual_reply",
        "self_message_decision": "skip_self_message",
        "bot_message_decision": "skip_bot_message",
        "duplicate_message_decision": "skip_duplicate_message",
        "public_channel_decision": "block_public_channel",
        "team_channel_decision": "block_team_channel",
        "reply_text_generated": False,
        "llm_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
    }
    assert_phase40_reply_decision_audit_safe(report)
    return report


def assert_phase40_reply_decision_audit_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40D reply decision audit contains sensitive values.")
    expected = {
        "private_test_human_message_decision": "eligible_for_future_manual_reply",
        "self_message_decision": "skip_self_message",
        "bot_message_decision": "skip_bot_message",
        "duplicate_message_decision": "skip_duplicate_message",
        "public_channel_decision": "block_public_channel",
        "team_channel_decision": "block_team_channel",
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise ValueError(f"Phase 40D unexpected decision for {key}.")
    for key in (
        "reply_text_generated",
        "llm_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "discord_api_send_called",
        "discord_message_sent",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40D unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40D message_sent_count must remain 0.")


def render_phase40_reply_decision_audit_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40D Reply Decision Audit",
            "",
            "- Report only: true",
            "- Private-test human message decision: eligible_for_future_manual_reply",
            "- Self message decision: skip_self_message",
            "- Bot message decision: skip_bot_message",
            "- Duplicate message decision: skip_duplicate_message",
            "- Public channel decision: block_public_channel",
            "- Team channel decision: block_team_channel",
            "- Discord message sent: false",
        ]
    ) + "\n"
