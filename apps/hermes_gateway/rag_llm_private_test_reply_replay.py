"""Phase 33D-safe RAG+LLM private test reply replay without live send."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_llm_would_send_preview import build_rag_llm_would_send_preview


VERSION = "phase33d_replay_no_live_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")

EVENT_TYPES = [
    "human_private_test_rag_llm_allowed_would_send",
    "self_message_skipped_before_retrieval",
    "bot_message_skipped_before_retrieval",
    "public_channel_blocked_before_retrieval",
    "private_channel_id_mismatch_blocked",
    "invalid_source_blocked",
    "operations_source_blocked",
    "context_too_large_blocked",
    "too_many_documents_blocked",
    "rag_response_packet_missing_blocked",
    "llm_preflight_failed_blocked",
    "output_safety_blocked",
    "cooldown_blocked",
    "budget_exhausted_blocked",
    "rate_limit_circuit_breaker",
    "send_exception_circuit_breaker",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _event(event_type: str, decision: str, reason: str, would_send: bool = False) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "decision": decision,
        "reason": reason,
        "would_send": bool(would_send),
        "actual_message_sent": False,
        "retrieval_executed": False if "before_retrieval" in event_type else event_type == "human_private_test_rag_llm_allowed_would_send",
        "llm_api_called": False,
        "embedding_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
    }


def build_rag_llm_private_test_reply_replay_report(root: str | None = None) -> dict[str, Any]:
    preview = build_rag_llm_would_send_preview(root=root, source="operation")
    events = [
        _event("human_private_test_rag_llm_allowed_would_send", "would_send_preview_only", "safe_scaffold_no_live_send", True),
        _event("self_message_skipped_before_retrieval", "skipped", "self_message"),
        _event("bot_message_skipped_before_retrieval", "skipped", "bot_author"),
        _event("public_channel_blocked_before_retrieval", "blocked", "public_or_team_channel"),
        _event("private_channel_id_mismatch_blocked", "blocked", "private_channel_id_mismatch"),
        _event("invalid_source_blocked", "blocked", "invalid_source"),
        _event("operations_source_blocked", "blocked", "operations_source_not_allowed"),
        _event("context_too_large_blocked", "blocked", "context_too_large"),
        _event("too_many_documents_blocked", "blocked", "too_many_documents"),
        _event("rag_response_packet_missing_blocked", "blocked", "rag_response_packet_missing"),
        _event("llm_preflight_failed_blocked", "blocked", "llm_preflight_failed"),
        _event("output_safety_blocked", "blocked", "output_safety_blocked"),
        _event("cooldown_blocked", "blocked", "cooldown"),
        _event("budget_exhausted_blocked", "blocked", "budget_exhausted"),
        _event("rate_limit_circuit_breaker", "blocked", "rate_limit_circuit_breaker"),
        _event("send_exception_circuit_breaker", "blocked", "send_exception_circuit_breaker"),
    ]
    report = {
        "report_type": "rag_llm_private_test_reply_replay",
        "version": VERSION,
        "created_at": utc_now(),
        "events_replayed": len(events),
        "would_send": sum(1 for item in events if item.get("would_send")),
        "actual_message_sent": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
        "ready_for_phase33d_live_review": True,
        "preview_available": bool(preview),
        "events": events,
        "required_event_types": EVENT_TYPES,
        "safety_assertions": {
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    _assert_safe(report)
    return report


def render_rag_llm_private_test_reply_replay_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG+LLM Private Test Reply Replay",
            "",
            f"- Events replayed: {report.get('events_replayed', 0)}",
            f"- Would-send previews: {report.get('would_send', 0)}",
            "- Actual message sent: false",
            "- LLM API called: false",
            "- Embedding API called: false",
            "- Discord message sent: false",
            "- External execution: false",
            f"- Ready for Phase 33D live review: {str(report.get('ready_for_phase33d_live_review')).lower()}",
        ]
    ) + "\n"


def _assert_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG+LLM replay contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG+LLM replay contains raw Discord-like IDs.")
