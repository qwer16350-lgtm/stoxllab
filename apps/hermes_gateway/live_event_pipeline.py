"""Audit-only processing for live Discord message events."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from audit_log import build_audit_payload
from discord_adapter_stub import build_dispatch_from_evaluation, build_would_send_payload, evaluate_discord_raw_event
from discord_safety_wrapper import block_outgoing_action
from reply_planner import build_reply_plan


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def redact_discord_id(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    if LONG_ID_RE.fullmatch(text):
        return f"discord_id_redacted:{text[-4:]}"
    return LONG_ID_RE.sub(lambda match: f"discord_id_redacted:{match.group(0)[-4:]}", text)


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _author_dict(message: Any) -> dict[str, Any]:
    author = _value(message, "author", {}) or {}
    return {
        "id": redact_discord_id(_value(author, "id", "")),
        "display_name": _value(author, "display_name", _value(author, "name", "")),
        "bot": bool(_value(author, "bot", False)),
        "roles": _value(author, "roles", []) if isinstance(_value(author, "roles", []), list) else [],
    }


def normalize_live_discord_message_event(message: Any, mapping: dict[str, Any] | None = None) -> dict[str, Any]:
    channel = _value(message, "channel", {}) or {}
    guild = _value(message, "guild", {}) or {}
    raw = {
        "event_type": "live_discord_message_create",
        "event_id": redact_discord_id(_value(message, "id", "")),
        "guild_id": redact_discord_id(_value(guild, "id", _value(message, "guild_id", ""))),
        "channel_id": redact_discord_id(_value(channel, "id", _value(message, "channel_id", ""))),
        "channel_name": _value(channel, "name", _value(message, "channel_name", "")),
        "category_name": _value(message, "category_name", ""),
        "content": _value(message, "content", ""),
        "author": _author_dict(message),
        "author_is_bot": bool(_value(message, "author_is_bot", False)),
        "attachments": _value(message, "attachments", []) or [],
        "mentions": _value(message, "mentions", []) or [],
        "timestamp": str(_value(message, "created_at", _value(message, "timestamp", ""))),
    }
    if isinstance(message, dict):
        for key in ("requested_action", "requested_source", "current_status", "requested_next_status", "actor_agent"):
            if key in message:
                raw[key] = message[key]
    return raw


def _pipeline_safety(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "gateway_connected_by_pipeline": False,
        "discord_api_called_by_pipeline": False,
        "message_sent": False,
        "write_action_blocked": block.get("blocked") is True,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
        "human_only_execution_preserved": True,
    }


def process_live_event_audit_only(raw_event: Any, root: str | Path | None = None) -> dict[str, Any]:
    event = normalize_live_discord_message_event(raw_event)
    block = block_outgoing_action("message_create", "Live event pipeline is audit-only in Phase 29.")
    if event.get("author", {}).get("bot") or event.get("author_is_bot"):
        return {
            "pipeline_mode": "audit_only",
            "status": "ignored_self_or_bot_message",
            "raw_event_summary": {
                "event_type": event.get("event_type"),
                "channel_name": event.get("channel_name"),
                "author_is_bot": True,
                "event_id": event.get("event_id"),
            },
            "would_send_payload": {"will_send": False, "message_sent": False},
            "reply_plan": {"will_send": False, "reply_enabled": False},
            "outgoing_action_guard": block,
            "safety": _pipeline_safety(block),
        }

    evaluation = evaluate_discord_raw_event(event, root=root)
    dispatch_plan = build_dispatch_from_evaluation(evaluation)
    payload = build_would_send_payload(dispatch_plan, evaluation)
    payload["will_send"] = False
    payload["message_sent"] = False
    reply_plan = build_reply_plan(evaluation.get("evaluator_result", {}), payload)
    audit = build_audit_payload(
        event.get("event_type", "live_discord_message_create"),
        evaluation["normalized_request"],
        evaluation["evaluator_result"],
        dispatch_plan,
        event.get("event_id"),
    )
    return {
        "pipeline_mode": "audit_only",
        "status": "processed_audit_only",
        "raw_event_summary": {
            "event_type": event.get("event_type"),
            "channel_name": event.get("channel_name"),
            "author_is_bot": False,
            "event_id": event.get("event_id"),
        },
        "normalized_request": evaluation["normalized_request"],
        "dispatch_plan": dispatch_plan,
        "would_send_payload": payload,
        "reply_plan": reply_plan,
        "audit_log_payload": audit,
        "outgoing_action_guard": block,
        "safety": _pipeline_safety(block),
    }


def build_live_event_pipeline_report(root: str | Path | None = None) -> dict[str, Any]:
    sample = {
        "id": "123456789012345678",
        "guild_id": "234567890123456789",
        "channel_id": "345678901234567890",
        "channel_name": "marin-초안",
        "content": "SNS 초안 후보를 검토해 주세요.",
        "author": {"id": "456789012345678901", "display_name": "local_user", "bot": False, "roles": ["Decision Maker"]},
        "attachments": [],
        "mentions": [],
    }
    result = process_live_event_audit_only(sample, root=root)
    return {
        "report_type": "live_event_pipeline_report",
        "version": "phase29_readonly",
        "pipeline_mode": "audit_only",
        "sample_result": result,
        "safety_assertions": {
            "gateway_connected_by_report": False,
            "discord_api_called_by_report": False,
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
            "raw_long_discord_ids_logged": False,
        },
    }
