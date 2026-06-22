"""In-memory handoff context for STOXL company agents."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from company_agent_registry import get_agent
from company_persistent_memory import load_recent_records
from llm_client import redact_text


CONTEXT_REFERENCE_TERMS = (
    "방금",
    "아까",
    "이거",
    "이 문구",
    "이 초안",
    "이 지원사업",
    "이 후보",
    "위 내용",
    "위 초안",
    "해당",
    "그 문구",
    "그 지원사업",
    "카스미가 넘긴",
    "마린이 넘긴",
    "handoff",
    "핸드오프",
)

DISCORD_WEBHOOK_RE = re.compile(r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\S+", re.IGNORECASE)
AGENT_PREFIX_RE = re.compile(r"\[(LUCY|MARIN|MEIKO|KASUMI|REZE)_STOXL\b", re.IGNORECASE)
FROM_AGENT_RE = re.compile(r"^from_agent:\s*([A-Z]+)_STOXL\b", re.IGNORECASE | re.MULTILINE)


def _safe(value: Any, max_chars: int = 1600) -> str:
    text = redact_text(str(value or ""), max_chars)
    return DISCORD_WEBHOOK_RE.sub("[REDACTED_WEBHOOK_URL]", text)[:max(max_chars, 0)]


def sanitize_company_context_text(value: Any, max_chars: int = 1600) -> str:
    return _safe(value, max_chars)


@dataclass(frozen=True)
class HandoffContext:
    context_type: str
    source_agent: str
    target_agent: str
    source_channel: str
    target_channel: str
    status: str
    request_summary: str
    handoff_content: str
    next_action: str
    created_at_present: bool = True
    raw_discord_ids_logged: bool = False
    secret_values_logged: bool = False


_CONTEXT_BY_CHANNEL: dict[str, dict[str, Any]] = {}
_CONTEXT_BY_AGENT_PAIR: dict[tuple[str, str], dict[str, Any]] = {}
_CREATED_AT_BY_CHANNEL: dict[str, datetime] = {}


def clear_handoff_context_store() -> None:
    _CONTEXT_BY_CHANNEL.clear()
    _CONTEXT_BY_AGENT_PAIR.clear()
    _CREATED_AT_BY_CHANNEL.clear()


def _normalized_context(target_channel_name: str, context: HandoffContext | dict[str, Any]) -> dict[str, Any]:
    raw = asdict(context) if isinstance(context, HandoffContext) else dict(context)
    target_channel = _safe(target_channel_name or raw.get("target_channel"), 120)
    return {
        "context_type": "handoff",
        "source_agent": _safe(raw.get("source_agent"), 40).lower(),
        "target_agent": _safe(raw.get("target_agent"), 40).lower(),
        "source_channel": _safe(raw.get("source_channel"), 120),
        "target_channel": target_channel,
        "status": _safe(raw.get("status"), 160),
        "request_summary": _safe(raw.get("request_summary"), 500),
        "handoff_content": _safe(raw.get("handoff_content"), 1600),
        "next_action": _safe(raw.get("next_action"), 300),
        "created_at_present": True,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def store_handoff_context(target_channel_name: str, context: HandoffContext | dict[str, Any]) -> dict[str, Any]:
    selected = _normalized_context(target_channel_name, context)
    channel_key = selected["target_channel"].strip().lower()
    if channel_key:
        _CONTEXT_BY_CHANNEL[channel_key] = selected
        _CREATED_AT_BY_CHANNEL[channel_key] = datetime.now(timezone.utc)
    pair = (selected["source_agent"], selected["target_agent"])
    if all(pair):
        _CONTEXT_BY_AGENT_PAIR[pair] = selected
    return dict(selected)


def get_latest_context_for_channel(channel_name: str) -> dict[str, Any] | None:
    channel_key = _safe(channel_name, 120).strip().lower()
    context = _CONTEXT_BY_CHANNEL.get(channel_key)
    if context:
        return dict(context)
    for record in load_recent_records("handoff", limit=20):
        if str(record.get("target_channel") or "").strip().lower() == channel_key:
            return _context_from_memory_record(record)
    return None


def get_latest_context_by_agent_pair(source_agent: str, target_agent: str) -> dict[str, Any] | None:
    pair = (_safe(source_agent, 40).lower(), _safe(target_agent, 40).lower())
    context = _CONTEXT_BY_AGENT_PAIR.get(pair)
    if context:
        return dict(context)
    for record in load_recent_records("handoff", limit=20):
        if (
            str(record.get("source_agent") or "").strip().lower(),
            str(record.get("target_agent") or "").strip().lower(),
        ) == pair:
            return _context_from_memory_record(record)
    return None


def _context_from_memory_record(record: dict[str, Any]) -> dict[str, Any]:
    return _normalized_context(
        str(record.get("target_channel") or ""),
        {
            "source_agent": record.get("source_agent"),
            "target_agent": record.get("target_agent"),
            "source_channel": record.get("source_channel"),
            "target_channel": record.get("target_channel"),
            "status": record.get("status"),
            "request_summary": record.get("summary") or record.get("title"),
            "handoff_content": record.get("content") or record.get("summary"),
            "next_action": record.get("next_action"),
        },
    )


def detect_context_reference_terms(message: str) -> bool:
    normalized = str(message or "").strip().lower()
    return any(term.lower() in normalized for term in CONTEXT_REFERENCE_TERMS)


def _agent_display(agent_id: str) -> str:
    agent = get_agent(agent_id) or {}
    persona = agent.get("webhook_persona") or f"{agent_id.upper()}_STOXL"
    display = agent.get("display_name") or agent_id
    return f"{persona} / {display}"


def format_handoff_context_block(context: dict[str, Any]) -> str:
    selected = _normalized_context(str(context.get("target_channel", "")), context)
    return (
        "[CONTEXT_FROM_RECENT_HANDOFF]\n"
        f"source_agent: {_agent_display(selected['source_agent'])}\n"
        f"target_agent: {_agent_display(selected['target_agent'])}\n"
        f"source_channel: {selected['source_channel']}\n"
        f"target_channel: {selected['target_channel']}\n\n"
        "handoff_content:\n"
        f"{selected['handoff_content']}\n"
        "[/CONTEXT_FROM_RECENT_HANDOFF]"
    )


def context_from_replied_message(
    content: str,
    channel_name: str,
    target_agent: str,
) -> dict[str, Any] | None:
    safe_content = _safe(content, 1600)
    if not safe_content or not (safe_content.startswith("[HANDOFF]") or AGENT_PREFIX_RE.search(safe_content)):
        return None
    match = FROM_AGENT_RE.search(safe_content) or AGENT_PREFIX_RE.search(safe_content)
    source_agent = str(match.group(1) if match else "unknown").lower()
    return _normalized_context(
        channel_name,
        {
            "source_agent": source_agent,
            "target_agent": target_agent,
            "source_channel": "replied-message",
            "target_channel": channel_name,
            "status": "replied message context",
            "request_summary": "Discord reply context",
            "handoff_content": safe_content,
            "next_action": f"{target_agent} review",
        },
    )


def resolve_handoff_context(
    agent_id: str,
    user_message: str,
    channel_name: str,
    replied_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reference_detected = detect_context_reference_terms(user_message)
    latest = get_latest_context_for_channel(channel_name)
    selected = dict(replied_context) if replied_context else (latest if reference_detected else None)
    return {
        "context_reference_detected": reference_detected,
        "latest_context_available": latest is not None,
        "reply_context_available": replied_context is not None,
        "context_used": selected is not None,
        "context_priority": "reply" if replied_context else "latest_channel" if selected else "none",
        "context": selected,
        "context_source_agent": (selected or {}).get("source_agent"),
        "context_target_agent": (selected or {}).get("target_agent") or agent_id,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_contextual_user_message(
    agent_id: str,
    user_message: str,
    channel_name: str,
    replied_context: dict[str, Any] | None = None,
) -> str:
    resolution = resolve_handoff_context(agent_id, user_message, channel_name, replied_context)
    context = resolution.get("context")
    if not isinstance(context, dict):
        return _safe(user_message, 1200)
    return f"{format_handoff_context_block(context)}\n\n[CURRENT_REQUEST]\n{_safe(user_message, 1200)}"
