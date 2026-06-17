"""Phase52 synthetic session context store for read-only events."""

from __future__ import annotations

import json
import re
from typing import Any

from phase51_readonly_event_guard import guard_readonly_event
from phase51_readonly_event_schema import SYNTHETIC_EVENTS, normalize_readonly_event


VERSION = "phase52_session_context_store_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_session_context(raw_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    selected = raw_events or SYNTHETIC_EVENTS
    normalized = [normalize_readonly_event(event) for event in selected]
    guards = [guard_readonly_event(event) for event in normalized]
    first_scope = normalized[0].get("channel_scope", "unknown") if normalized else "unknown"
    context = {
        "session_id_created": True,
        "session_id_hash": "session_synthetic_readonly",
        "session_scope": first_scope if first_scope in {"private_test", "team", "public", "unknown"} else "unknown",
        "message_count": len(normalized),
        "duplicate_count": sum(1 for event in normalized if event.get("message_kind") == "duplicate"),
        "operator_command_count": sum(1 for event in normalized if event.get("message_kind") == "operator_command"),
        "review_packet_candidate_count": sum(1 for guard in guards if guard.get("event_allowed_for_review_packet")),
        "reply_count": 0,
        "send_count": 0,
        "llm_call_count": 0,
        "rag_call_count": 0,
        "external_execution_count": 0,
        "actual_discord_runtime_executed": False,
        "synthetic_fixture_only": True,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
    }
    assert_phase52_session_context_store_safe(context)
    return context


def build_phase52_session_context_store() -> dict[str, Any]:
    context = build_session_context()
    report = {
        "report_type": "phase52_session_context_store",
        "version": VERSION,
        "session_context_store_available": True,
        **context,
    }
    assert_phase52_session_context_store_safe(report)
    return report


def assert_phase52_session_context_store_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase52 session context contains sensitive values.")
    for key in (
        "reply_count",
        "send_count",
        "llm_call_count",
        "rag_call_count",
        "external_execution_count",
        "actual_discord_runtime_executed",
        "raw_content_logged",
        "raw_discord_ids_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase52 session context unsafe flag/count is non-zero: {key}")


def render_phase52_session_context_store_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase52 Session Context Store",
            "",
            "- Session context store available: true",
            f"- Session scope: {report.get('session_scope')}",
            f"- Synthetic message count: {report.get('message_count')}",
            f"- Duplicate count: {report.get('duplicate_count')}",
            f"- Operator command count: {report.get('operator_command_count')}",
            "- Reply count: 0",
            "- Send count: 0",
            "- LLM call count: 0",
            "- RAG call count: 0",
            "- External execution count: 0",
        ]
    ) + "\n"
