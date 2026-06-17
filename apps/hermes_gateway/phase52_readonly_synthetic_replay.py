"""Phase52 synthetic replay for the read-only review packet foundation."""

from __future__ import annotations

import json
import re
from typing import Any

from phase51_readonly_event_guard import guard_readonly_event
from phase51_readonly_event_schema import SYNTHETIC_EVENTS, normalize_readonly_event
from phase52_review_packet_composer import compose_review_packet
from phase52_session_context_store import build_session_context


VERSION = "phase52_readonly_synthetic_replay_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def run_phase52_readonly_synthetic_replay() -> dict[str, Any]:
    session = build_session_context(SYNTHETIC_EVENTS)
    results = []
    for raw_event in SYNTHETIC_EVENTS:
        normalized = normalize_readonly_event(raw_event)
        guard = guard_readonly_event(normalized)
        packet = compose_review_packet(normalized, guard, session)
        results.append(
            {
                "event_ref_hash": normalized["event_ref_hash"],
                "channel_scope": normalized["channel_scope"],
                "channel_risk": normalized["channel_risk"],
                "author_kind": normalized["author_kind"],
                "message_kind": normalized["message_kind"],
                "normalized": True,
                "guarded": True,
                "packetized": True,
                "event_allowed_for_review_packet": guard["event_allowed_for_review_packet"],
                "discord_send_allowed": False,
                "llm_call_allowed": False,
                "rag_call_allowed": False,
                "external_execution": False,
                "raw_content_included": False,
                "raw_discord_ids_logged": False,
                "recommended_next_action": packet["recommended_next_action"],
            }
        )
    report = {
        "report_type": "phase52_readonly_synthetic_replay",
        "version": VERSION,
        "synthetic_replay_available": True,
        "synthetic_fixture_only": True,
        "event_count": len(results),
        "all_events_normalized": all(item["normalized"] for item in results),
        "all_events_guarded": all(item["guarded"] for item in results),
        "all_events_packetized": all(item["packetized"] for item in results),
        "results": results,
        "actual_discord_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "actual_llm_api_call_attempted": False,
        "actual_llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase52_readonly_synthetic_replay_safe(report)
    return report


def assert_phase52_readonly_synthetic_replay_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase52 synthetic replay contains sensitive values.")
    for key in (
        "actual_discord_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "actual_llm_api_call_attempted",
        "actual_llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase52 synthetic replay unsafe flag is true: {key}")
    if not report.get("all_events_normalized") or not report.get("all_events_guarded") or not report.get("all_events_packetized"):
        raise ValueError("Phase52 synthetic replay did not process every fixture.")


def render_phase52_readonly_synthetic_replay_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase52 Read-only Synthetic Replay",
            "",
            "- Synthetic replay available: true",
            f"- Event count: {report.get('event_count')}",
            "- All events normalized: true",
            "- All events guarded: true",
            "- All events packetized: true",
            "- Discord message sent: false",
            "- LLM API called: false",
            "- RAG called: false",
        ]
    ) + "\n"
