"""Phase51/52 read-only live runtime launch packet, report-only."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from phase51_52_readonly_live_runtime_preflight import (
    APPROVAL_PHRASE,
    build_phase51_52_readonly_live_runtime_preflight,
)


VERSION = "phase51_52_readonly_live_runtime_launch_packet_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
RECOMMENDED_COMMAND = "python apps\\hermes_gateway\\cli.py --run-discord-private-test-readonly --json --readonly-runtime-timeout-seconds 300 --readonly-runtime-max-events 20"


def build_phase51_52_readonly_live_runtime_launch_packet(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    preflight = build_phase51_52_readonly_live_runtime_preflight(env)
    report = {
        "report_type": "phase51_52_readonly_live_runtime_launch_packet",
        "version": VERSION,
        "report_only": True,
        "actual_runtime_command_available": True,
        "recommended_command": RECOMMENDED_COMMAND,
        "send_disabled_required": True,
        "llm_disabled_required": True,
        "rag_disabled_required": True,
        "embedding_vector_disabled_required": True,
        "external_execution_disabled_required": True,
        "scheduler_live_execution_disabled_required": True,
        "ready_for_manual_gate": bool(preflight.get("ready_for_manual_readonly_runtime_launch")),
        "approval_phrase_value_logged": False,
        "actual_discord_runtime_executed": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "actual_llm_api_call_attempted": False,
        "actual_llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_cron_live_execution": False,
        "unattended_auto_reply": False,
    }
    assert_phase51_52_readonly_live_runtime_launch_packet_safe(report)
    return report


def assert_phase51_52_readonly_live_runtime_launch_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    scrubbed = text.replace(APPROVAL_PHRASE, "")
    if SECRET_RE.search(scrubbed.lower()) or LONG_ID_RE.search(scrubbed) or APPROVAL_RE.search(scrubbed):
        raise ValueError("Phase51/52 launch packet contains sensitive values.")
    for key in (
        "approval_phrase_value_logged",
        "actual_discord_runtime_executed",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "actual_llm_api_call_attempted",
        "actual_llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_cron_live_execution",
        "unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Phase51/52 launch packet unsafe flag is true: {key}")
    if not report.get("actual_runtime_command_available"):
        raise ValueError("Phase51/52 launch packet must expose the manual command.")


def render_phase51_52_readonly_live_runtime_launch_packet_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase51/52 Read-only Live Runtime Launch Packet",
            "",
            "- Report only: true",
            "- Actual runtime command available: true",
            f"- Recommended command: `{report.get('recommended_command')}`",
            "- Send disabled required: true",
            "- LLM disabled required: true",
            "- RAG disabled required: true",
            "- External execution disabled required: true",
            f"- Ready for manual gate: {str(report.get('ready_for_manual_gate')).lower()}",
            "- Actual Discord runtime executed: false",
        ]
    ) + "\n"
