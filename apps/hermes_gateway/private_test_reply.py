"""Guarded private-test-channel reply policy for Phase 31B."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any


VERSION = "phase31b_private_test_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def _first_env_value(env: dict[str, Any] | None, keys: list[str], default: str = "") -> str:
    if env is not None:
        for key in keys:
            if key in env and env.get(key) is not None:
                return str(env.get(key) or "")
        return default
    for key in keys:
        if key in os.environ:
            return os.environ.get(key, "")
    return default


def _event_value(source: Any, key: str, default: Any = "") -> Any:
    if isinstance(source, dict):
        if key in source:
            return source.get(key, default)
        if key == "channel_id" and isinstance(source.get("channel"), dict):
            return source["channel"].get("id", default)
    if key == "channel_id":
        channel = getattr(source, "channel", None)
        return getattr(channel, "id", default)
    if key == "channel_name":
        channel = getattr(source, "channel", None)
        return getattr(channel, "name", default)
    return getattr(source, key, default)


def _event_author_is_bot(source: Any) -> bool:
    if isinstance(source, dict):
        if source.get("author_is_bot") is True:
            return True
        author = source.get("author", {}) or {}
        return bool(author.get("bot")) if isinstance(author, dict) else False
    author = getattr(source, "author", None)
    return bool(getattr(author, "bot", False) or getattr(source, "author_is_bot", False))


def _event_author_id(source: Any) -> str:
    if isinstance(source, dict):
        author = source.get("author", {}) or {}
        if isinstance(author, dict):
            return str(author.get("id", "") or "")
        return str(source.get("author_id", "") or "")
    author = getattr(source, "author", None)
    return str(getattr(author, "id", "") or getattr(source, "author_id", "") or "")


def redact_text(text: str | None, max_chars: int = 1200) -> str:
    if not text:
        return ""
    redacted = SECRET_RE.sub("[REDACTED_SECRET]", str(text))
    redacted = LONG_ID_RE.sub(lambda match: f"discord_id_redacted:{match.group(0)[-4:]}", redacted)
    return redacted[:max_chars]


def redact_id(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    if LONG_ID_RE.fullmatch(text):
        return f"discord_id_redacted:{text[-4:]}"
    return redact_text(text, 200)


def build_private_test_reply_policy(env: dict[str, Any] | None = None) -> dict[str, Any]:
    channel_id = _first_env_value(env, ["HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "_private_test_channel_id"])
    return {
        "policy_type": "private_test_reply_policy",
        "version": VERSION,
        "send_messages": _flag(_first_env_value(env, ["HERMES_DISCORD_SEND_MESSAGES", "send_messages"], "false")),
        "private_test_reply_enabled": _flag(
            _first_env_value(env, ["HERMES_DISCORD_PRIVATE_TEST_REPLY", "private_test_reply_enabled"], "false")
        ),
        "reply_mode": _first_env_value(env, ["HERMES_DISCORD_REPLY_MODE", "reply_mode"], "disabled"),
        "private_test_channel_configured": bool(channel_id),
        "private_test_channel_id_present": bool(channel_id),
        "_private_test_channel_id": channel_id,
        "allowed_message_source": "agent_placeholder_response",
        "llm_enabled": _flag(_first_env_value(env, ["HERMES_DISCORD_LLM_ENABLED", "llm_enabled"], "false")),
        "rag_enabled": _flag(_first_env_value(env, ["HERMES_DISCORD_RAG_ENABLED", "rag_enabled"], "false")),
        "external_execution": _flag(_first_env_value(env, ["HERMES_DISCORD_EXTERNAL_EXECUTION", "external_execution"], "false")),
    }


def _block(reason: str, event: Any, policy: dict[str, Any]) -> dict[str, Any]:
    channel_id = str(_event_value(event, "channel_id", "") or "")
    return {
        "decision_type": "private_test_reply_decision",
        "version": VERSION,
        "allowed": False,
        "blocked": True,
        "reason": reason,
        "event_id": redact_id(_event_value(event, "id", _event_value(event, "event_id", ""))),
        "channel_name": str(_event_value(event, "channel_name", "")),
        "channel_is_private_test": bool(policy.get("_private_test_channel_id") and channel_id == policy.get("_private_test_channel_id")),
        "will_send": False,
        "message_sent": False,
        "message_source": "agent_placeholder_response",
        "requires_manual_enable": True,
        "safety_assertions": _safety(False),
    }


def _safety(write_allowed: bool) -> dict[str, Any]:
    return {
        "discord_api_write_allowed": bool(write_allowed),
        "message_sent": False,
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
        "raw_token_logged": False,
        "raw_discord_ids_logged": False,
    }


def is_private_test_reply_allowed(event: Any, policy: dict[str, Any]) -> tuple[bool, str]:
    channel_id = str(_event_value(event, "channel_id", "") or "")
    author_id = _event_author_id(event)
    bot_user_id = str(policy.get("_bot_user_id", "") or "")
    if _event_author_is_bot(event) or (bot_user_id and author_id and author_id == bot_user_id):
        return False, "self_message"
    if not policy.get("send_messages"):
        return False, "send_messages_disabled"
    if not policy.get("private_test_reply_enabled"):
        return False, "private_test_reply_disabled"
    if policy.get("reply_mode") != "private_test_only":
        return False, "reply_mode_not_private_test_only"
    if not policy.get("private_test_channel_id_present"):
        return False, "private_test_channel_id_missing"
    if channel_id != policy.get("_private_test_channel_id"):
        return False, "channel_not_private_test"
    if policy.get("llm_enabled"):
        return False, "llm_enabled_blocked"
    if policy.get("rag_enabled"):
        return False, "rag_enabled_blocked"
    if policy.get("external_execution"):
        return False, "external_execution_blocked"
    return True, "private_test_reply_allowed"


def build_private_test_reply_decision(event: Any, placeholder_response: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if placeholder_response.get("response_type") != "agent_placeholder_response":
        return _block("message_source_not_agent_placeholder_response", event, policy)
    allowed, reason = is_private_test_reply_allowed(event, policy)
    if not allowed:
        return _block(reason, event, policy)
    return {
        "decision_type": "private_test_reply_decision",
        "version": VERSION,
        "allowed": True,
        "blocked": False,
        "reason": "private_test_reply_allowed",
        "event_id": redact_id(_event_value(event, "id", _event_value(event, "event_id", ""))),
        "channel_name": str(_event_value(event, "channel_name", "")),
        "channel_is_private_test": True,
        "will_send": True,
        "message_sent": False,
        "message_source": "agent_placeholder_response",
        "requires_manual_enable": False,
        "safety_assertions": _safety(True),
    }


def render_private_test_reply_message(placeholder_response: dict[str, Any]) -> str:
    placeholder = placeholder_response.get("placeholder", {})
    agent = str(placeholder_response.get("agent_route_candidate", "")).title()
    return "\n".join(
        [
            "[STOXL Hermes / Private Test Reply]",
            f"Agent: {redact_text(agent, 80)}",
            "Mode: deterministic placeholder / no LLM",
            f"Title: {redact_text(placeholder.get('title', ''), 160)}",
            f"Summary: {redact_text(placeholder.get('summary', ''), 240)}",
            f"Next step: {redact_text(placeholder.get('next_step', ''), 240)}",
            f"Review note: {redact_text(placeholder.get('review_note', ''), 240)}",
            "Safety:",
            "- LLM: disabled",
            "- RAG: disabled",
            "- External execution: disabled",
        ]
    )


def build_private_test_reply_payload(event: Any, placeholder_response: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    decision = build_private_test_reply_decision(event, placeholder_response, policy)
    payload = {
        "payload_type": "private_test_reply_payload",
        "version": VERSION,
        "decision": decision,
        "content": render_private_test_reply_message(placeholder_response) if decision.get("allowed") else "",
        "will_send": bool(decision.get("allowed")),
        "message_sent": False,
        "channel_id": redact_id(_event_value(event, "channel_id", "")),
        "message_source": "agent_placeholder_response",
        "safety_assertions": decision["safety_assertions"],
    }
    assert_private_test_reply_payload_safe(payload)
    return payload


def assert_private_test_reply_payload_safe(payload: dict[str, Any]) -> None:
    if payload.get("message_sent") is not False:
        raise ValueError("Private test reply payload cannot mark message_sent before runtime send.")
    text = json.dumps(payload, ensure_ascii=False).lower()
    if "sk-" in text or "xoxb-" in text or "mfa." in text or LONG_ID_RE.search(text):
        raise ValueError("Private test reply payload contains unsafe raw values.")
    if payload.get("message_source") != "agent_placeholder_response":
        raise ValueError("Private test reply payload source must be agent_placeholder_response.")


def build_private_test_reply_audit(decision: dict[str, Any], sent: bool = False) -> dict[str, Any]:
    return {
        "event_type": "private_test_reply_sent" if sent else "private_test_reply_blocked",
        "created_at": utc_now(),
        "message_sent": bool(sent),
        "channel_is_private_test": bool(decision.get("channel_is_private_test")),
        "source": "agent_placeholder_response",
        "reason": decision.get("reason", ""),
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
    }


async def send_private_test_reply_only(channel: Any, payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    assert_private_test_reply_payload_safe(payload)
    if not payload.get("will_send"):
        return build_private_test_reply_audit(payload.get("decision", {}), sent=False)
    allowed, reason = is_private_test_reply_allowed({"channel_id": policy.get("_private_test_channel_id")}, policy)
    if not allowed:
        decision = dict(payload.get("decision", {}))
        decision["reason"] = reason
        return build_private_test_reply_audit(decision, sent=False)
    send_func = getattr(channel, "send", None)
    if not callable(send_func):
        decision = dict(payload.get("decision", {}))
        decision["reason"] = "channel_send_unavailable"
        return build_private_test_reply_audit(decision, sent=False)
    await send_func(payload["content"])
    return build_private_test_reply_audit(payload["decision"], sent=True)


def build_private_test_reply_report(root: str | None = None) -> dict[str, Any]:
    from agent_placeholder_response import build_agent_placeholder_response
    from live_event_audit_persistence import build_live_event_audit_record, build_sample_visibility_event
    from live_event_routing_report import build_live_event_routing_report

    visibility = build_sample_visibility_event()
    visibility["event_id"] = "event_redacted_0000"
    audit = build_live_event_audit_record(visibility, content="sample")
    routing = build_live_event_routing_report(audit)
    placeholder = build_agent_placeholder_response(audit, routing)
    event = {"event_id": "event_redacted_0000", "channel_id": "private_test_channel", "channel_name": "private-test"}
    allowed_policy = build_private_test_reply_policy(
        {
            "HERMES_DISCORD_SEND_MESSAGES": "true",
            "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
            "HERMES_DISCORD_REPLY_MODE": "private_test_only",
            "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
            "HERMES_DISCORD_LLM_ENABLED": "false",
            "HERMES_DISCORD_RAG_ENABLED": "false",
            "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        }
    )
    blocked_policy = build_private_test_reply_policy({})
    return {
        "report_type": "private_test_reply_report",
        "version": VERSION,
        "allowed_example": build_private_test_reply_decision(event, placeholder, allowed_policy),
        "blocked_example": build_private_test_reply_decision(event, placeholder, blocked_policy),
        "policy": {key: value for key, value in allowed_policy.items() if not key.startswith("_")},
        "message_sent": False,
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
    }


def render_private_test_reply_report_markdown(report: dict[str, Any]) -> str:
    allowed = report.get("allowed_example", {})
    blocked = report.get("blocked_example", {})
    policy = report.get("policy", {})
    return "\n".join(
        [
            "# STOXL Private Test Reply Report",
            "",
            f"- report_type: {report.get('report_type', '')}",
            f"- version: {report.get('version', '')}",
            f"- private_test_reply_enabled: {str(policy.get('private_test_reply_enabled')).lower()}",
            f"- reply_mode: {policy.get('reply_mode', '')}",
            f"- private_test_channel_id_present: {str(policy.get('private_test_channel_id_present')).lower()}",
            f"- allowed_example: {str(allowed.get('allowed')).lower()}",
            f"- allowed_reason: {allowed.get('reason', '')}",
            f"- blocked_example: {str(blocked.get('blocked')).lower()}",
            f"- blocked_reason: {blocked.get('reason', '')}",
            "- message_sent: false",
            "- llm_called: false",
            "- rag_called: false",
            "- external_execution: false",
        ]
    ) + "\n"
