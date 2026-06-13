"""Session-local safety controls for Phase 31D private test replies."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any


VERSION = "phase31d_private_test_safety"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _int_value(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, 0)


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def _event_value(event: Any, key: str, default: Any = "") -> Any:
    if isinstance(event, dict):
        if key in event:
            return event.get(key, default)
        if key == "channel_id" and isinstance(event.get("channel"), dict):
            return event["channel"].get("id", default)
    if key == "channel_id":
        channel = getattr(event, "channel", None)
        return getattr(channel, "id", default)
    return getattr(event, key, default)


def _author_is_bot(event: Any) -> bool:
    if isinstance(event, dict):
        if event.get("author_is_bot") is True:
            return True
        author = event.get("author", {}) or {}
        return bool(author.get("bot")) if isinstance(author, dict) else False
    author = getattr(event, "author", None)
    return bool(getattr(author, "bot", False) or getattr(event, "author_is_bot", False))


def _message_fingerprint(event: Any) -> str:
    raw = str(_event_value(event, "id", _event_value(event, "event_id", "")) or "")
    if not raw:
        return ""
    return "message_hash:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _safe_state_copy(state: dict[str, Any]) -> dict[str, Any]:
    copy = dict(state)
    copy["processed_message_ids"] = list(state.get("processed_message_ids", []))
    return copy


def build_private_test_reply_safety_policy(env: dict[str, Any] | None = None) -> dict[str, Any]:
    channel_id = _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID") or _env_value(env, "_private_test_channel_id")
    return {
        "policy_type": "private_test_reply_safety_policy",
        "version": VERSION,
        "cooldown_seconds": _int_value(_env_value(env, "HERMES_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS", "10"), 10),
        "max_replies_per_session": _int_value(_env_value(env, "HERMES_PRIVATE_TEST_MAX_REPLIES_PER_SESSION", "3"), 3),
        "rate_limit_circuit_breaker": _flag(_env_value(env, "HERMES_PRIVATE_TEST_RATE_LIMIT_CIRCUIT_BREAKER", "true"), True),
        "disable_after_send_exception": _flag(_env_value(env, "HERMES_PRIVATE_TEST_DISABLE_AFTER_SEND_EXCEPTION", "true"), True),
        "llm_enabled": _flag(_env_value(env, "HERMES_DISCORD_LLM_ENABLED", "false"), False),
        "rag_enabled": _flag(_env_value(env, "HERMES_DISCORD_RAG_ENABLED", "false"), False),
        "external_execution": _flag(_env_value(env, "HERMES_DISCORD_EXTERNAL_EXECUTION", "false"), False),
        "_private_test_channel_id": channel_id,
    }


def build_private_test_reply_safety_state() -> dict[str, Any]:
    return {
        "state_type": "private_test_reply_safety_state",
        "version": VERSION,
        "reply_count": 0,
        "last_reply_at": None,
        "processed_message_ids": [],
        "circuit_breaker_open": False,
        "circuit_breaker_reason": None,
        "message_sent": False,
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
    }


def _decision(allowed: bool, reason: str, policy: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_type": "private_test_reply_safety_decision",
        "allowed": allowed,
        "blocked": not allowed,
        "reason": reason,
        "reply_count": int(state.get("reply_count", 0)),
        "max_replies_per_session": int(policy.get("max_replies_per_session", 3)),
        "cooldown_seconds": int(policy.get("cooldown_seconds", 10)),
        "circuit_breaker_open": bool(state.get("circuit_breaker_open")),
        "message_sent": False,
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
    }


def check_private_test_reply_safety(
    event: Any,
    policy: dict[str, Any],
    state: dict[str, Any],
    now: datetime | str | None = None,
) -> dict[str, Any]:
    current = _parse_time(now) or datetime.now(timezone.utc)
    fingerprint = _message_fingerprint(event)
    channel_id = str(_event_value(event, "channel_id", "") or "")
    private_channel_id = str(policy.get("_private_test_channel_id", "") or "")

    if _author_is_bot(event):
        return _decision(False, "bot_message", policy, state)
    if _event_value(event, "decision", "") == "ignored_self_message":
        return _decision(False, "self_message", policy, state)
    if private_channel_id and channel_id != private_channel_id:
        return _decision(False, "not_private_test_channel", policy, state)
    if state.get("circuit_breaker_open"):
        reason = str(state.get("circuit_breaker_reason") or "circuit_breaker_open")
        if reason == "rate_limit":
            return _decision(False, "rate_limit_seen", policy, state)
        if reason == "send_exception":
            return _decision(False, "send_exception_seen", policy, state)
        return _decision(False, "circuit_breaker_open", policy, state)
    if fingerprint and fingerprint in set(state.get("processed_message_ids", [])):
        return _decision(False, "duplicate_message", policy, state)
    if int(state.get("reply_count", 0)) >= int(policy.get("max_replies_per_session", 3)):
        return _decision(False, "reply_budget_exhausted", policy, state)

    last_reply = _parse_time(state.get("last_reply_at"))
    cooldown = int(policy.get("cooldown_seconds", 10))
    if last_reply and cooldown and current < last_reply + timedelta(seconds=cooldown):
        return _decision(False, "cooldown_active", policy, state)

    return _decision(True, "allowed", policy, state)


def record_private_test_reply_sent(event: Any, state: dict[str, Any], now: datetime | str | None = None) -> dict[str, Any]:
    current = (_parse_time(now) or datetime.now(timezone.utc)).replace(microsecond=0)
    state["reply_count"] = int(state.get("reply_count", 0)) + 1
    state["last_reply_at"] = current.isoformat()
    fingerprint = _message_fingerprint(event)
    if fingerprint and fingerprint not in state.get("processed_message_ids", []):
        state.setdefault("processed_message_ids", []).append(fingerprint)
    state["message_sent"] = False
    return _safe_state_copy(state)


def record_private_test_reply_blocked(event: Any, state: dict[str, Any], reason: str, now: datetime | str | None = None) -> dict[str, Any]:
    state["last_blocked_at"] = (_parse_time(now) or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    state["last_blocked_reason"] = reason
    state["message_sent"] = False
    return _safe_state_copy(state)


def record_private_test_reply_send_exception(
    event: Any,
    state: dict[str, Any],
    error_type: str | None = None,
    now: datetime | str | None = None,
) -> dict[str, Any]:
    error = str(error_type or "send_exception").lower()
    reason = "rate_limit" if "429" in error or "rate" in error else "send_exception"
    state["circuit_breaker_open"] = True
    state["circuit_breaker_reason"] = reason
    state["last_exception_at"] = (_parse_time(now) or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    fingerprint = _message_fingerprint(event)
    if fingerprint and fingerprint not in state.get("processed_message_ids", []):
        state.setdefault("processed_message_ids", []).append(fingerprint)
    state["message_sent"] = False
    return _safe_state_copy(state)


def assert_private_test_reply_safety_report_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if "sk-" in text or "xoxb-" in text or "mfa." in text or "token=" in text:
        raise ValueError("Private test safety report contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("Private test safety report contains raw Discord-like IDs.")
    for key in ("message_sent", "llm_called", "rag_called", "external_execution"):
        if report.get(key):
            raise ValueError(f"Private test safety report has unsafe flag: {key}")


def build_private_test_reply_safety_report(
    policy: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_policy = policy or build_private_test_reply_safety_policy({})
    selected_state = state or build_private_test_reply_safety_state()
    safe_policy = {key: value for key, value in selected_policy.items() if not key.startswith("_")}
    report = {
        "report_type": "private_test_reply_safety_report",
        "version": VERSION,
        "policy": safe_policy,
        "state": _safe_state_copy(selected_state),
        "message_sent": False,
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
    }
    assert_private_test_reply_safety_report_safe(report)
    return report


def render_private_test_reply_safety_report_markdown(report: dict[str, Any]) -> str:
    policy = report.get("policy", {})
    state = report.get("state", {})
    return "\n".join(
        [
            "# Private Test Reply Safety Report",
            "",
            f"- version: {report.get('version', '')}",
            f"- cooldown_seconds: {policy.get('cooldown_seconds')}",
            f"- max_replies_per_session: {policy.get('max_replies_per_session')}",
            f"- rate_limit_circuit_breaker: {str(policy.get('rate_limit_circuit_breaker')).lower()}",
            f"- disable_after_send_exception: {str(policy.get('disable_after_send_exception')).lower()}",
            f"- reply_count: {state.get('reply_count')}",
            f"- circuit_breaker_open: {str(state.get('circuit_breaker_open')).lower()}",
            "- message_sent: false",
            "- llm_called: false",
            "- rag_called: false",
            "- external_execution: false",
        ]
    ) + "\n"
