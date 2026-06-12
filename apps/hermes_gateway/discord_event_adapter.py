"""Local Discord-shaped event normalization. This module never calls Discord APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

RuntimeEvent = dict[str, Any]
NormalizedRequest = dict[str, Any]


ROLE_TO_AGENT = {
    "Marketing Senior": "lucy",
    "Marketing Junior": "marin",
    "Operation Senior": "meiko",
    "Operation Junior": "kasumi",
    "Strategy Office": "reze",
}

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


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(event: RuntimeEvent) -> str:
    return event.get("text") or event.get("message_text") or event.get("content") or ""


def _channel(event: RuntimeEvent) -> str:
    return event.get("channel") or event.get("channel_name") or event.get("source_channel") or ""


def infer_requested_action(text: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    lower = text.lower()
    if any(word in lower for word in ("api key", "apikey", "token", "secret", "password")):
        return None
    if ("지원사업" in text or "공모전" in text) and any(word in text for word in ("제출", "신청", "지원해")):
        return "grant_submit"
    if ("인스타" in text or "sns" in lower) and any(word in text for word in ("게시해", "발행", "업로드해")) and "초안" not in text:
        return "sns_publish"
    if "홈페이지" in text and any(word in text for word in ("반영", "올려", "업로드해")) and "초안" not in text:
        return "homepage_upload"
    if "이메일" in text and any(word in text for word in ("보내", "발송")):
        return "external_email_send"
    if "명령" in text and "레제" in text:
        return "direct_order_to_team"
    return None


def infer_requested_source(text: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    lower = text.lower()
    for source in ("brand", "marketing", "operation", "strategy", "shared"):
        if source in lower:
            return source
    return None


def infer_actor_agent(event: RuntimeEvent, channel: str) -> str | None:
    if event.get("actor_agent"):
        return event.get("actor_agent")
    if event.get("author_is_agent"):
        return ROLE_TO_AGENT.get(event.get("author_role", ""))
    return CHANNEL_AGENT_HINTS.get(channel)


def normalize_event(event: RuntimeEvent) -> NormalizedRequest:
    text = _text(event)
    channel = _channel(event)
    return {
        "text": text,
        "actor_role": event.get("author_role") or event.get("actor_role") or "",
        "actor_agent": infer_actor_agent(event, channel),
        "author_display_name": event.get("author_display_name", ""),
        "source_channel": channel,
        "source_category": event.get("channel_category", ""),
        "mentioned_agents": list(event.get("mentioned_agents", [])),
        "requested_action": infer_requested_action(text, event.get("requested_action")),
        "requested_source": infer_requested_source(text, event.get("requested_source")),
        "current_status": event.get("current_status"),
        "requested_next_status": event.get("requested_next_status"),
        "attachments": [{"redacted": True, "note": "attachment originals are not stored"} for _ in event.get("attachments", [])],
        "timestamp": event.get("timestamp") or _now_iso(),
    }


def event_from_text(text: str, channel: str, author_role: str) -> RuntimeEvent:
    return {
        "event_type": "manual_cli_text",
        "text": text,
        "channel_name": channel,
        "author_role": author_role,
        "author_is_agent": False,
        "mentioned_agents": [],
        "attachments": [],
        "timestamp": _now_iso(),
    }
