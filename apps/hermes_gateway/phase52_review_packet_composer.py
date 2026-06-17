"""Phase52 read-only review packet composer."""

from __future__ import annotations

import json
import re
from typing import Any

from phase51_readonly_event_guard import guard_readonly_event
from phase51_readonly_event_schema import SYNTHETIC_EVENTS, normalize_readonly_event
from phase52_session_context_store import build_session_context


VERSION = "phase52_review_packet_composer_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def route_agent(normalized_event: dict[str, Any]) -> str:
    if normalized_event.get("channel_risk") == "private_test":
        return "operations"
    if normalized_event.get("channel_risk") == "team_low":
        return "dev"
    if normalized_event.get("message_kind") == "operator_command":
        return "operations"
    return "unknown"


def compose_review_packet(
    normalized_event: dict[str, Any] | None = None,
    guard: dict[str, Any] | None = None,
    session_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = normalized_event or normalize_readonly_event(SYNTHETIC_EVENTS[0])
    event_guard = guard or guard_readonly_event(event)
    session = session_context or build_session_context()
    packet = {
        "report_type": "phase52_review_packet",
        "version": VERSION,
        "packet_type": "readonly_review_packet",
        "external_action_taken": False,
        "discord_send_allowed": False,
        "llm_call_allowed": False,
        "rag_call_allowed": False,
        "requires_human_review": True,
        "recommended_next_action": "review_only",
        "agent_route_candidate": route_agent(event),
        "evidence_shell_created": True,
        "evidence_shell": {
            "event_metadata_available": True,
            "session_metadata_available": True,
            "knowledge_lookup_placeholder_only": True,
            "rag_called": False,
            "embedding_api_called": False,
            "raw_content_included": False,
        },
        "event_allowed_for_review_packet": bool(event_guard.get("event_allowed_for_review_packet")),
        "event_allowed_for_reply": False,
        "session_scope": session.get("session_scope", "unknown"),
        "session_message_count": int(session.get("message_count", 0) or 0),
        "raw_content_included": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "actual_discord_runtime_executed": False,
        "actual_llm_api_call_attempted": False,
        "actual_llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase52_review_packet_safe(packet)
    return packet


def build_phase52_review_packet_composer() -> dict[str, Any]:
    packet = compose_review_packet()
    report = {
        "report_type": "phase52_review_packet_composer",
        "version": VERSION,
        "review_packet_base_ready": True,
        "packet": packet,
        **packet,
    }
    assert_phase52_review_packet_safe(report)
    return report


def assert_phase52_review_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase52 review packet contains sensitive values.")
    for key in (
        "external_action_taken",
        "discord_send_allowed",
        "llm_call_allowed",
        "rag_call_allowed",
        "event_allowed_for_reply",
        "raw_content_included",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "actual_discord_runtime_executed",
        "actual_llm_api_call_attempted",
        "actual_llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase52 review packet unsafe flag is true: {key}")
    if report.get("recommended_next_action") != "review_only":
        raise ValueError("Phase52 review packet must remain review-only.")


def render_phase52_review_packet_composer_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase52 Review Packet Base",
            "",
            "- Review packet base ready: true",
            "- Packet type: readonly_review_packet",
            "- Requires human review: true",
            "- Recommended next action: review_only",
            f"- Agent route candidate: {report.get('agent_route_candidate')}",
            "- Evidence shell created: true",
            "- Discord send allowed: false",
            "- LLM call allowed: false",
            "- RAG call allowed: false",
            "- Raw content included: false",
        ]
    ) + "\n"
