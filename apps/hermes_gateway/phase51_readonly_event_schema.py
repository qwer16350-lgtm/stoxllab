"""Phase51 read-only event schema for synthetic Discord-like events."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


VERSION = "phase51_readonly_event_schema_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


SYNTHETIC_EVENTS: list[dict[str, Any]] = [
    {
        "event_ref": "evt_private_human_normal",
        "source": "discord",
        "channel_scope": "private_test",
        "author_kind": "human",
        "content": "Please review the latest operations packet.",
    },
    {
        "event_ref": "evt_self_message",
        "source": "discord",
        "channel_scope": "private_test",
        "author_kind": "self",
        "content": "Synthetic self echo.",
    },
    {
        "event_ref": "evt_bot_message",
        "source": "discord",
        "channel_scope": "team",
        "author_kind": "bot",
        "content": "Synthetic bot status.",
    },
    {
        "event_ref": "evt_duplicate_message",
        "source": "discord",
        "channel_scope": "private_test",
        "author_kind": "human",
        "content": "Please review the latest operations packet.",
        "duplicate_of": "evt_private_human_normal",
    },
    {
        "event_ref": "evt_operator_command",
        "source": "discord",
        "channel_scope": "private_test",
        "author_kind": "human",
        "content": "/stoxl status",
    },
    {
        "event_ref": "evt_team_low_risk",
        "source": "discord",
        "channel_scope": "team",
        "author_kind": "human",
        "content": "Please summarize this non-sensitive handoff note.",
        "risk_hint": "low",
    },
    {
        "event_ref": "evt_public_high_risk",
        "source": "discord",
        "channel_scope": "public",
        "author_kind": "human",
        "content": "Public channel request should remain review-only.",
    },
]


def _safe_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _channel_risk(scope: str, risk_hint: str = "") -> str:
    if scope == "private_test":
        return "private_test"
    if scope == "team" and risk_hint == "low":
        return "team_low"
    if scope == "team":
        return "team_high"
    if scope == "public":
        return "public_high"
    return "unknown"


def _message_kind(raw_event: dict[str, Any]) -> str:
    content = str(raw_event.get("content", ""))
    if raw_event.get("duplicate_of"):
        return "duplicate"
    if content.strip().startswith("/"):
        return "operator_command"
    if raw_event.get("system"):
        return "system"
    return "normal"


def normalize_readonly_event(raw_event: dict[str, Any]) -> dict[str, Any]:
    content = str(raw_event.get("content", ""))
    event_ref = str(raw_event.get("event_ref", ""))
    scope = str(raw_event.get("channel_scope", "unknown"))
    author_kind = str(raw_event.get("author_kind", "unknown"))
    normalized = {
        "event_id_present": bool(event_ref),
        "event_ref_hash": _safe_hash(event_ref) if event_ref else "",
        "source": "discord" if raw_event.get("source") == "discord" else "unknown",
        "channel_scope": scope if scope in {"private_test", "team", "public", "unknown"} else "unknown",
        "channel_risk": _channel_risk(scope, str(raw_event.get("risk_hint", ""))),
        "author_kind": author_kind if author_kind in {"human", "bot", "self", "unknown"} else "unknown",
        "message_kind": _message_kind(raw_event),
        "content_present": bool(content),
        "content_length": len(content),
        "content_hash": _safe_hash(content) if content else "",
        "duplicate_of_hash": _safe_hash(str(raw_event.get("duplicate_of", ""))) if raw_event.get("duplicate_of") else "",
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "discord_send_allowed": False,
        "llm_call_allowed": False,
        "rag_call_allowed": False,
        "external_action_taken": False,
    }
    assert_phase51_readonly_event_schema_safe(normalized)
    return normalized


def build_phase51_readonly_event_schema(raw_event: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = raw_event or SYNTHETIC_EVENTS[0]
    normalized = normalize_readonly_event(selected)
    report = {
        "report_type": "phase51_readonly_event_schema",
        "version": VERSION,
        "schema_available": True,
        "synthetic_fixture_only": True,
        "actual_discord_runtime_executed": False,
        "discord_gateway_live_connection": False,
        "normalized_event": normalized,
        **normalized,
    }
    assert_phase51_readonly_event_schema_safe(report)
    return report


def assert_phase51_readonly_event_schema_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase51 readonly event schema contains sensitive values.")
    for key in (
        "raw_content_logged",
        "raw_discord_ids_logged",
        "discord_send_allowed",
        "llm_call_allowed",
        "rag_call_allowed",
        "external_action_taken",
        "actual_discord_runtime_executed",
        "discord_gateway_live_connection",
    ):
        if report.get(key):
            raise ValueError(f"Phase51 readonly event schema unsafe flag is true: {key}")


def render_phase51_readonly_event_schema_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase51 Read-only Event Schema",
            "",
            "- Schema available: true",
            "- Synthetic fixture only: true",
            f"- Source: {report.get('source')}",
            f"- Channel scope: {report.get('channel_scope')}",
            f"- Channel risk: {report.get('channel_risk')}",
            f"- Author kind: {report.get('author_kind')}",
            f"- Message kind: {report.get('message_kind')}",
            "- Raw content logged: false",
            "- Raw Discord IDs logged: false",
            "- Discord send allowed: false",
            "- LLM call allowed: false",
            "- RAG call allowed: false",
        ]
    ) + "\n"
