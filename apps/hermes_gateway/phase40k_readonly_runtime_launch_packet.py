"""Phase 40K read-only runtime launch packet, manual-only."""

from __future__ import annotations

import json
import re
from typing import Any

from phase40j_private_test_readonly_runtime_preflight import build_phase40j_private_test_readonly_runtime_preflight


VERSION = "phase40k_readonly_runtime_launch_packet_report_only"
PLANNED_COMMAND = r"python apps\hermes_gateway\cli.py --run-discord-private-test-readonly --json"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40k_readonly_runtime_launch_packet() -> dict[str, Any]:
    preflight = build_phase40j_private_test_readonly_runtime_preflight()
    report = {
        "report_type": "phase40k_readonly_runtime_launch_packet",
        "version": VERSION,
        "report_only": True,
        "manual_launch_only": True,
        "codex_must_not_launch": True,
        "runtime_scope": "private_test_readonly",
        "send_messages_required_false": True,
        "private_test_reply_required_false": True,
        "reply_mode": "readonly_private_test_only",
        "planned_command": PLANNED_COMMAND,
        "planned_command_executed_by_codex": False,
        "preflight_available": bool(preflight.get("readonly_runtime_preflight_available")),
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "ready_for_manual_readonly_runtime_launch": False,
        "next_human_confirmation_required": True,
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
    assert_phase40k_readonly_runtime_launch_packet_safe(report)
    return report


def assert_phase40k_readonly_runtime_launch_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).replace(PLANNED_COMMAND, "")
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40K launch packet contains sensitive values.")
    for key in ("manual_launch_only", "codex_must_not_launch", "send_messages_required_false", "private_test_reply_required_false", "next_human_confirmation_required"):
        if not report.get(key):
            raise ValueError(f"Phase 40K required condition is false: {key}")
    if report.get("reply_mode") != "readonly_private_test_only":
        raise ValueError("Phase 40K reply mode must be readonly_private_test_only.")
    for key in (
        "planned_command_executed_by_codex",
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "ready_for_manual_readonly_runtime_launch",
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
            raise ValueError(f"Phase 40K unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40K message_sent_count must remain 0.")


def render_phase40k_readonly_runtime_launch_packet_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40K Read-only Runtime Launch Packet",
            "",
            "- Report only: true",
            "- Manual launch only: true",
            "- Codex must not launch: true",
            "- Runtime scope: private_test_readonly",
            "- Send messages required false: true",
            "- Private-test reply required false: true",
            "- Reply mode: readonly_private_test_only",
            f"- Planned command: `{PLANNED_COMMAND}`",
            "- Planned command executed by Codex: false",
        ]
    ) + "\n"
