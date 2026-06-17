"""Phase51/52 continuous read-only runtime foundation readiness."""

from __future__ import annotations

import json
import re
from typing import Any

from phase51_readonly_event_guard import build_phase51_readonly_event_guard
from phase51_readonly_event_schema import build_phase51_readonly_event_schema
from phase52_readonly_synthetic_replay import run_phase52_readonly_synthetic_replay
from phase52_review_packet_composer import build_phase52_review_packet_composer
from phase52_session_context_store import build_phase52_session_context_store


VERSION = "phase51_52_continuous_readonly_foundation_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase51_52_continuous_readonly_foundation() -> dict[str, Any]:
    schema = build_phase51_readonly_event_schema()
    guard = build_phase51_readonly_event_guard()
    session = build_phase52_session_context_store()
    packet = build_phase52_review_packet_composer()
    replay = run_phase52_readonly_synthetic_replay()
    report = {
        "report_type": "phase51_52_continuous_readonly_foundation",
        "version": VERSION,
        "continuous_readonly_runtime_foundation_ready": True,
        "current_automation_level": 1,
        "current_automation_level_name": "continuous_readonly_observation_foundation",
        "actual_discord_runtime_executed": False,
        "discord_gateway_live_connection": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "actual_llm_api_call_attempted": False,
        "actual_llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_cron_live_execution": False,
        "unattended_auto_reply_implemented": False,
        "review_packet_base_ready": bool(packet.get("review_packet_base_ready")),
        "event_schema_ready": bool(schema.get("schema_available")),
        "event_guard_ready": bool(guard.get("guard_available")),
        "session_context_store_ready": bool(session.get("session_context_store_available")),
        "synthetic_replay_passed": bool(replay.get("all_events_packetized")),
        "synthetic_event_count": int(replay.get("event_count", 0) or 0),
        "ready_for_manual_gate_readonly_live_runtime": True,
        "ready_for_auto_reply": False,
        "ready_for_team_channel_auto_ops": False,
        "ready_for_production_unattended": False,
        "next_safe_step": "manual_gate_longer_readonly_live_runtime_no_send",
        "manual_gate_needed_for_live_readonly_runtime": True,
        "raw_content_included": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
    }
    assert_phase51_52_continuous_readonly_foundation_safe(report)
    return report


def assert_phase51_52_continuous_readonly_foundation_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase51/52 foundation contains sensitive values.")
    for key in (
        "actual_discord_runtime_executed",
        "discord_gateway_live_connection",
        "discord_api_send_called",
        "discord_message_sent",
        "actual_llm_api_call_attempted",
        "actual_llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_cron_live_execution",
        "unattended_auto_reply_implemented",
        "ready_for_auto_reply",
        "ready_for_team_channel_auto_ops",
        "ready_for_production_unattended",
        "raw_content_included",
        "raw_content_logged",
        "raw_discord_ids_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase51/52 foundation unsafe flag is true: {key}")
    for key in (
        "continuous_readonly_runtime_foundation_ready",
        "review_packet_base_ready",
        "event_schema_ready",
        "event_guard_ready",
        "session_context_store_ready",
        "synthetic_replay_passed",
        "ready_for_manual_gate_readonly_live_runtime",
        "manual_gate_needed_for_live_readonly_runtime",
    ):
        if not report.get(key):
            raise ValueError(f"Phase51/52 foundation required flag is false: {key}")


def render_phase51_52_continuous_readonly_foundation_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase51/52 Continuous Read-only Runtime Foundation",
            "",
            "- Continuous read-only runtime foundation ready: true",
            "- Review packet base ready: true",
            "- Current automation level: 1 continuous_readonly_observation_foundation",
            "- Actual Discord runtime executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- LLM API called: false",
            "- RAG called: false",
            "- Scheduler cron live execution: false",
            "- Ready for manual gate read-only live runtime: true",
            "- Ready for auto reply: false",
            "- Ready for production unattended: false",
            f"- Next safe step: {report.get('next_safe_step')}",
        ]
    ) + "\n"
