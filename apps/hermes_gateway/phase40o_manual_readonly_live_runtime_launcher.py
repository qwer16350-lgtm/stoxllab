"""Phase 40O manual read-only live runtime launcher support."""

from __future__ import annotations

import json
import re
from typing import Any

from phase40k_readonly_runtime_launch_packet import PLANNED_COMMAND


VERSION = "phase40o_manual_readonly_live_runtime_launcher_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40o_manual_readonly_live_runtime_launcher() -> dict[str, Any]:
    report = {
        "report_type": "phase40o_manual_readonly_live_runtime_launcher",
        "version": VERSION,
        "report_only": True,
        "manual_launch_only": True,
        "codex_must_not_launch": True,
        "phase39_actual_send_count_locked": 1,
        "additional_send_count": 0,
        "readonly_runtime_launch_command_available": True,
        "planned_command": PLANNED_COMMAND,
        "planned_command_executed_by_codex": False,
        "required_runtime_envs": [
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
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "ready_for_manual_readonly_runtime_launch": False,
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
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }
    assert_phase40o_manual_readonly_live_runtime_launcher_safe(report)
    return report


def assert_phase40o_manual_readonly_live_runtime_launcher_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).replace(PLANNED_COMMAND, "")
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40O launcher contains sensitive values.")
    for key in ("manual_launch_only", "codex_must_not_launch", "readonly_runtime_launch_command_available"):
        if not report.get(key):
            raise ValueError(f"Phase 40O required guard is false: {key}")
    for key in (
        "planned_command_executed_by_codex",
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "ready_for_manual_readonly_runtime_launch",
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
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40O unsafe flag is true: {key}")
    if report.get("phase39_actual_send_count_locked") != 1 or int(report.get("additional_send_count", 0) or 0) != 0:
        raise ValueError("Phase 40O send counts are invalid.")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40O message_sent_count must remain 0.")


def render_phase40o_manual_readonly_live_runtime_launcher_markdown(report: dict[str, Any]) -> str:
    envs = "\n".join(f"- {item}" for item in report.get("required_runtime_envs", []))
    return "\n".join(
        [
            "# STOXL Phase 40O Manual Read-only Live Runtime Launcher",
            "",
            "- Report only: true",
            "- Manual launch only: true",
            "- Codex must not launch: true",
            "- Phase 39 actual send count locked: 1",
            "- Additional send count: 0",
            f"- Planned command: `{PLANNED_COMMAND}`",
            "- Planned command executed by Codex: false",
            "",
            "## Required Runtime Envs",
            envs,
        ]
    ) + "\n"
