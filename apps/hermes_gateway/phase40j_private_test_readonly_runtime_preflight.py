"""Phase 40J private-test read-only live runtime preflight, report-only."""

from __future__ import annotations

import json
import re
from typing import Any

from phase51_52_readonly_live_runtime_preflight import build_phase51_52_readonly_live_runtime_preflight
from phase40_safe_overnight_summary import build_phase40_safe_overnight_summary


VERSION = "phase40j_private_test_readonly_runtime_preflight_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40j_private_test_readonly_runtime_preflight() -> dict[str, Any]:
    phase40 = build_phase40_safe_overnight_summary()
    gate = build_phase51_52_readonly_live_runtime_preflight()
    report = {
        "report_type": "phase40j_private_test_readonly_runtime_preflight",
        "version": VERSION,
        "report_only": True,
        "phase39_actual_send_count_locked": int(phase40.get("actual_discord_send_count_locked_from_phase39", 0) or 0),
        "phase40_readiness_completed": bool(phase40.get("phase40_reports_completed")),
        "readonly_runtime_preflight_available": True,
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "required_future_runtime_conditions": [
            "DISCORD_BOT_TOKEN present",
            "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID present",
            "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED=true",
            "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE exact",
            "HERMES_DISCORD_SEND_MESSAGES=false",
            "HERMES_DISCORD_PRIVATE_TEST_REPLY=false",
            "HERMES_DISCORD_REPLY_MODE=readonly_private_test_only",
            "LLM false",
            "RAG false",
            "embedding false",
            "external false",
        ],
        "manual_gate_required": True,
        "manual_approval_present": bool(gate.get("manual_approval_present")),
        "manual_approval_true": bool(gate.get("manual_approval_true")),
        "approval_phrase_present": bool(gate.get("approval_phrase_present")),
        "approval_phrase_exact_match": bool(gate.get("approval_phrase_exact_match")),
        "approval_phrase_value_logged": False,
        "send_messages_disabled": bool(gate.get("send_messages_disabled")),
        "private_test_reply_disabled": bool(gate.get("private_test_reply_disabled")),
        "reply_mode_readonly_private_test_only": bool(gate.get("reply_mode_readonly_private_test_only")),
        "llm_disabled": bool(gate.get("llm_disabled")),
        "rag_disabled": bool(gate.get("rag_disabled")),
        "embedding_vector_disabled": bool(gate.get("embedding_vector_disabled")),
        "external_execution_disabled": bool(gate.get("external_execution_disabled")),
        "ready_for_manual_readonly_runtime_launch": bool(gate.get("ready_for_manual_readonly_runtime_launch")),
        "actual_discord_runtime_executed": False,
        "ready_for_reply_send": False,
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
    assert_phase40j_private_test_readonly_runtime_preflight_safe(report)
    return report


def assert_phase40j_private_test_readonly_runtime_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40J preflight contains sensitive values.")
    if report.get("phase39_actual_send_count_locked") != 1 or not report.get("phase40_readiness_completed"):
        raise ValueError("Phase 40J requires Phase 39 count locked and Phase 40 completed.")
    for key in (
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "actual_discord_runtime_executed",
        "ready_for_reply_send",
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
            raise ValueError(f"Phase 40J unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40J message_sent_count must remain 0.")


def render_phase40j_private_test_readonly_runtime_preflight_markdown(report: dict[str, Any]) -> str:
    conditions = "\n".join(f"- {item}" for item in report.get("required_future_runtime_conditions", []))
    return "\n".join(
        [
            "# STOXL Phase 40J Private-test Read-only Runtime Preflight",
            "",
            "- Report only: true",
            "- Phase 39 actual send count locked: 1",
            "- Phase 40 readiness completed: true",
            "- Live runtime started: false",
            "- Discord Gateway connected: false",
            "- Ready for manual read-only runtime launch: false",
            "",
            "## Required Future Runtime Conditions",
            conditions,
        ]
    ) + "\n"
