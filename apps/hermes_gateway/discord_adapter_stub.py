"""Future Discord adapter local stub.

This module accepts Discord-shaped raw event dictionaries, but it never imports
discord.py/discord.js, never connects to a Gateway, and never sends messages.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import load_config
from dispatcher import build_dispatch_plan
from evaluator_bridge import evaluate_request
from message_renderer import (
    build_would_send_payload as render_would_send_payload,
    render_agent_dispatch_message,
    render_approval_required_message,
    render_blocked_message,
    render_review_packet_hint,
)
from registry_loader import load_registry


SECRET_MARKERS = ("api key", "apikey", "token", "secret", "password", "sk-", "bearer")
CHANNEL_AGENT_HINTS = {
    "marin-초안": "marin",
    "sns-콘텐츠": "marin",
    "homepage": "marin",
    "lucy-검토": "lucy",
    "kasumi-리서치": "kasumi",
    "공모전-지원사업": "meiko",
    "일정-마감관리": "meiko",
    "meiko-검토": "meiko",
    "reze-전략기획": "reze",
    "new-business": "reze",
    "product-ideas": "reze",
}


def _redact_text(text: str) -> str:
    lower = text.lower()
    if any(marker in lower for marker in SECRET_MARKERS):
        return "[REDACTED]"
    return text


def _author_role(raw_event: dict[str, Any]) -> str:
    roles = raw_event.get("author", {}).get("roles") or []
    return roles[0] if roles else raw_event.get("author_role", "")


def _mentions(raw_event: dict[str, Any]) -> list[str]:
    mentions = raw_event.get("mentions") or []
    normalized: list[str] = []
    for item in mentions:
        if isinstance(item, str):
            normalized.append(item)
        elif isinstance(item, dict):
            normalized.append(item.get("agent_id") or item.get("name") or item.get("display_name") or "")
    return [item for item in normalized if item]


def _infer_requested_action(text: str, explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    lower = text.lower()
    if any(marker in lower for marker in SECRET_MARKERS):
        return None
    if ("지원사업" in text or "공모전" in text) and any(word in text for word in ("제출", "신청", "지원해")):
        return "grant_submit"
    if ("sns" in lower or "인스타" in text) and any(word in text for word in ("게시", "발행", "업로드")) and "초안" not in text:
        return "sns_publish"
    if "홈페이지" in text and any(word in text for word in ("업로드", "반영", "올려")) and "초안" not in text:
        return "homepage_upload"
    return None


def _infer_requested_source(text: str, explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    lower = text.lower()
    for source in ("brand", "marketing", "operation", "strategy", "shared"):
        if source in lower:
            return source
    return None


def normalize_discord_raw_event(raw_event: dict[str, Any], mapping: dict[str, Any] | None = None) -> dict[str, Any]:
    channel_name = raw_event.get("channel_name") or raw_event.get("channel") or ""
    text = raw_event.get("content") or raw_event.get("message_text") or raw_event.get("text") or ""
    author = raw_event.get("author", {})
    actor_agent = raw_event.get("actor_agent") or CHANNEL_AGENT_HINTS.get(channel_name)
    return {
        "text": text,
        "actor_role": _author_role(raw_event),
        "actor_agent": actor_agent,
        "author_display_name": author.get("display_name") or raw_event.get("author_display_name", ""),
        "source_channel": channel_name,
        "source_category": raw_event.get("category_name") or raw_event.get("channel_category", ""),
        "mentioned_agents": _mentions(raw_event),
        "requested_action": _infer_requested_action(text, raw_event.get("requested_action")),
        "requested_source": _infer_requested_source(text, raw_event.get("requested_source")),
        "current_status": raw_event.get("current_status"),
        "requested_next_status": raw_event.get("requested_next_status"),
        "attachments": [{"redacted": True, "note": "attachment originals are not stored"} for _ in raw_event.get("attachments", [])],
        "timestamp": raw_event.get("timestamp", ""),
    }


def evaluate_discord_raw_event(
    raw_event: dict[str, Any],
    root: str | Path | None = None,
    mapping: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = load_config(Path(root) if root else Path(__file__).resolve())
    registry = load_registry(cfg)
    normalized = normalize_discord_raw_event(raw_event, mapping)
    evaluator_result = evaluate_request(registry, normalized, cfg)
    dispatch_plan = build_dispatch_plan(normalized, evaluator_result)
    return {
        "raw_event_meta": {
            "event_type": raw_event.get("event_type"),
            "guild_id": raw_event.get("guild_id"),
            "channel_id": raw_event.get("channel_id"),
            "expected_blocked": raw_event.get("expected_blocked"),
            "expected_message_kind": raw_event.get("expected_message_kind"),
            "notes": raw_event.get("notes"),
        },
        "normalized_request": normalized,
        "evaluator_result": evaluator_result,
        "dispatch_plan": dispatch_plan,
    }


def build_dispatch_from_evaluation(evaluation_result: dict[str, Any]) -> dict[str, Any]:
    return dict(evaluation_result.get("dispatch_plan", {}))


def _message_kind(dispatch_plan: dict[str, Any], evaluator_result: dict[str, Any]) -> str:
    if dispatch_plan.get("blocked") and dispatch_plan.get("approval_required") is True:
        return "approval_required"
    if dispatch_plan.get("blocked"):
        return "blocked_request"
    return "agent_dispatch"


def build_would_send_payload(dispatch_plan: dict[str, Any], evaluation_result: dict[str, Any]) -> dict[str, Any]:
    evaluator_result = evaluation_result.get("evaluator_result", evaluation_result)
    kind = _message_kind(dispatch_plan, evaluator_result)
    if kind == "blocked_request":
        content = render_blocked_message(evaluator_result)
        target = evaluation_result.get("normalized_request", {}).get("source_channel")
    elif kind == "approval_required":
        content = render_approval_required_message(evaluator_result, dispatch_plan) + " " + render_review_packet_hint(evaluator_result)
        target = dispatch_plan.get("final_report_channel") or "최종-승인요청"
    else:
        content = render_agent_dispatch_message(evaluator_result, dispatch_plan)
        target = dispatch_plan.get("dispatch_channel")
    return render_would_send_payload(
        kind,
        target,
        content,
        metadata={
            "dispatch_to_agent": dispatch_plan.get("dispatch_to_agent"),
            "reviewer_agent": dispatch_plan.get("reviewer_agent"),
            "approval_required": dispatch_plan.get("approval_required"),
            "blocked": dispatch_plan.get("blocked"),
        },
    )


def run_discord_adapter_stub(
    raw_event: dict[str, Any],
    root: str | Path | None = None,
    mapping: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evaluation = evaluate_discord_raw_event(raw_event, root=root, mapping=mapping)
    dispatch_plan = build_dispatch_from_evaluation(evaluation)
    payload = build_would_send_payload(dispatch_plan, evaluation)
    return {
        "adapter_type": "discord_adapter_stub",
        "normalized_request": evaluation["normalized_request"],
        "evaluator_result": evaluation["evaluator_result"],
        "dispatch_plan": dispatch_plan,
        "would_send_payload": payload,
        "safety": {
            "discord_api_called": False,
            "gateway_connected": False,
            "message_sent": False,
            "external_execution": False,
            "human_only_execution": True,
        },
    }


def load_raw_events(path: str | Path) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.get("events", [data] if data.get("event_type") else []))
    raise ValueError("Raw event file must contain an event object, event list, or object with events.")
