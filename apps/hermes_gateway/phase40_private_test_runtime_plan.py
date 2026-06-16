"""Phase 40B private-test runtime plan, no live execution."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40_private_test_runtime_plan_no_live_execution"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_private_test_runtime_plan() -> dict[str, Any]:
    report = {
        "report_type": "phase40_private_test_runtime_plan",
        "version": VERSION,
        "report_only": True,
        "runtime_scope": "private_test_only",
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "planned_runtime_guards": [
            "private_test_channel_id_only",
            "self_message_guard",
            "bot_message_guard",
            "duplicate_message_id_guard",
            "one_reply_per_human_message",
            "manual_operator_abort",
            "no_public_team_send",
            "no_unattended_auto_reply",
            "no_llm_by_default",
            "no_rag_by_default",
        ],
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "unattended_auto_reply_allowed": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_runtime_dry_replay": True,
        "ready_for_live_runtime_execution": False,
    }
    assert_phase40_private_test_runtime_plan_safe(report)
    return report


def assert_phase40_private_test_runtime_plan_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40B runtime plan contains sensitive values.")
    for key in (
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "unattended_auto_reply_allowed",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_live_runtime_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40B unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40B must not send messages.")


def render_phase40_private_test_runtime_plan_markdown(report: dict[str, Any]) -> str:
    guards = "\n".join(f"- {guard}" for guard in report.get("planned_runtime_guards", []))
    return "\n".join(
        [
            "# STOXL Phase 40B Private-test Runtime Plan",
            "",
            "- Report only: true",
            "- Runtime scope: private_test_only",
            "- Live runtime started: false",
            "- Discord gateway connected: false",
            "- Discord message sent: false",
            "",
            "## Planned Guards",
            guards,
        ]
    ) + "\n"
