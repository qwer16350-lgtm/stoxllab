"""Local replay summaries for private test reply closeout events."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any


VERSION = "phase31e_replay_closeout"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_MARKERS = ("sk-", "xoxb-", "mfa.", "bearer ", "api_key", "apikey", "token=", "password=")

EVENT_KINDS = [
    "human_allowed_sent",
    "self_message_skipped",
    "duplicate_message_blocked",
    "cooldown_blocked",
    "budget_exhausted_blocked",
    "rate_limit_circuit_breaker",
    "send_exception_circuit_breaker",
    "public_channel_blocked",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _base_event(kind: str) -> dict[str, Any]:
    if kind not in EVENT_KINDS:
        raise ValueError(f"Unknown private test reply replay kind: {kind}")
    return {
        "event_type": "private_test_reply_replay_event",
        "version": VERSION,
        "kind": kind,
        "event_id": f"event_redacted_{EVENT_KINDS.index(kind):04d}",
        "channel_name": "hermes-private-test" if kind != "public_channel_blocked" else "marketing-brief",
        "message_sent": False,
        "historical_message_sent": False,
        "allowed": False,
        "blocked": False,
        "skipped": False,
        "reason": "",
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
    }


def build_private_test_reply_replay_event(kind: str = "sent") -> dict[str, Any]:
    normalized_kind = "human_allowed_sent" if kind == "sent" else kind
    event = _base_event(normalized_kind)
    if normalized_kind == "human_allowed_sent":
        event.update({"allowed": True, "historical_message_sent": True, "reason": "private_test_reply_sent"})
    elif normalized_kind == "self_message_skipped":
        event.update({"skipped": True, "reason": "self_message"})
    elif normalized_kind == "duplicate_message_blocked":
        event.update({"blocked": True, "reason": "duplicate_message"})
    elif normalized_kind == "cooldown_blocked":
        event.update({"blocked": True, "reason": "cooldown_active"})
    elif normalized_kind == "budget_exhausted_blocked":
        event.update({"blocked": True, "reason": "reply_budget_exhausted"})
    elif normalized_kind == "rate_limit_circuit_breaker":
        event.update({"blocked": True, "reason": "rate_limit_seen", "circuit_breaker_opened": True})
    elif normalized_kind == "send_exception_circuit_breaker":
        event.update({"blocked": True, "reason": "send_exception_seen", "circuit_breaker_opened": True})
    elif normalized_kind == "public_channel_blocked":
        event.update({"blocked": True, "reason": "not_private_test_channel"})
    assert_private_test_reply_replay_safe(event)
    return event


def replay_private_test_reply_events(events: list[dict[str, Any]], safety_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    replayed = []
    for item in events:
        kind = item.get("kind", "")
        replayed.append(build_private_test_reply_replay_event(kind))
    result = {
        "replay_type": "private_test_reply_replay",
        "version": VERSION,
        "events_replayed": len(replayed),
        "events": replayed,
        "safety_policy": {key: value for key, value in (safety_policy or {}).items() if not key.startswith("_")},
        "message_sent": False,
        "discord_api_called": False,
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
    }
    assert_private_test_reply_replay_safe(result)
    return result


def summarize_private_test_reply_replay(replay_result: dict[str, Any]) -> dict[str, int]:
    events = replay_result.get("events", [])
    return {
        "allowed": sum(1 for item in events if item.get("allowed")),
        "sent": sum(1 for item in events if item.get("historical_message_sent")),
        "blocked": sum(1 for item in events if item.get("blocked")),
        "skipped": sum(1 for item in events if item.get("skipped")),
        "self_message_skipped": sum(1 for item in events if item.get("reason") == "self_message"),
        "duplicate_blocked": sum(1 for item in events if item.get("reason") == "duplicate_message"),
        "cooldown_blocked": sum(1 for item in events if item.get("reason") == "cooldown_active"),
        "budget_exhausted_blocked": sum(1 for item in events if item.get("reason") == "reply_budget_exhausted"),
        "circuit_breaker_opened": sum(1 for item in events if item.get("circuit_breaker_opened")),
        "public_channel_blocked": sum(1 for item in events if item.get("reason") == "not_private_test_channel"),
    }


def build_private_test_reply_replay_report(root: str | None = None, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    selected_events = events or [build_private_test_reply_replay_event(kind) for kind in EVENT_KINDS]
    replay = replay_private_test_reply_events(selected_events)
    report = {
        "report_type": "private_test_reply_replay_report",
        "version": VERSION,
        "created_at": utc_now(),
        "events_replayed": replay["events_replayed"],
        "summary": summarize_private_test_reply_replay(replay),
        "events": replay["events"],
        "message_sent": False,
        "safety_assertions": {
            "discord_api_called": False,
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
            "env_file_read": False,
            "local_mapping_file_read": False,
            "raw_token_logged": False,
            "raw_discord_ids_logged": False,
        },
    }
    assert_private_test_reply_replay_safe(report)
    return report


def render_private_test_reply_replay_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Private Test Reply Replay Report",
        "",
        f"- Events replayed: {report.get('events_replayed', 0)}",
        f"- Historical sent: {summary.get('sent', 0)}",
        f"- Blocked: {summary.get('blocked', 0)}",
        f"- Skipped: {summary.get('skipped', 0)}",
        f"- Self-message skipped: {summary.get('self_message_skipped', 0)}",
        f"- Duplicate blocked: {summary.get('duplicate_blocked', 0)}",
        f"- Cooldown blocked: {summary.get('cooldown_blocked', 0)}",
        f"- Budget exhausted: {summary.get('budget_exhausted_blocked', 0)}",
        f"- Circuit breaker: {summary.get('circuit_breaker_opened', 0)}",
        f"- Public channel blocked: {summary.get('public_channel_blocked', 0)}",
        "",
        "## Safety",
        "- Discord API called: false",
        "- Message sent during replay: false",
        "- LLM called: false",
        "- RAG called: false",
        "- External execution: false",
    ]
    text = "\n".join(lines) + "\n"
    assert_private_test_reply_replay_safe({"markdown": text})
    return text


def assert_private_test_reply_replay_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if any(marker in text for marker in SECRET_MARKERS):
        raise ValueError("Private test reply replay contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Private test reply replay contains raw Discord-like IDs.")
    if isinstance(report, dict):
        safety = report.get("safety_assertions", {})
        if safety.get("discord_api_called") or safety.get("message_sent") or safety.get("external_execution") or safety.get("llm_called") or safety.get("rag_called"):
            raise ValueError("Private test reply replay safety assertions are unsafe.")
