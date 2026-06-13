"""Guarded private-test-only LLM reply policy for Phase 32D."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_client import build_llm_client_config, call_llm_once, public_llm_client_config, redact_text, validate_llm_client_config
from llm_prompt_envelope import build_llm_prompt_envelope
from llm_response_packet import assert_llm_response_packet_safe, build_llm_response_packet
from llm_safety_policy import build_llm_safety_policy, check_llm_output_allowed
from private_test_reply import redact_id
from private_test_reply_safety import (
    build_private_test_reply_safety_policy,
    build_private_test_reply_safety_state,
    check_private_test_reply_safety,
    record_private_test_reply_blocked,
    record_private_test_reply_send_exception,
    record_private_test_reply_sent,
)


VERSION = "phase32d_guarded_private_test_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _int(value: Any, default: int) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def _first_value(env: dict[str, Any] | None, keys: list[str], default: str = "") -> str:
    if env is not None:
        for key in keys:
            if key in env and env.get(key) is not None:
                return str(env.get(key) or "")
        return default
    for key in keys:
        if key in os.environ:
            return os.environ.get(key, "")
    return default


def _event_value(event: Any, key: str, default: Any = "") -> Any:
    if isinstance(event, dict):
        if key in event:
            return event.get(key, default)
        if key == "channel_id" and isinstance(event.get("channel"), dict):
            return event["channel"].get("id", default)
        if key == "channel_name" and isinstance(event.get("channel"), dict):
            return event["channel"].get("name", default)
    if key in {"channel_id", "channel_name"}:
        channel = getattr(event, "channel", None)
        attr = "id" if key == "channel_id" else "name"
        return getattr(channel, attr, default)
    return getattr(event, key, default)


def _author_is_bot(event: Any) -> bool:
    if isinstance(event, dict):
        if event.get("author_is_bot") is True:
            return True
        author = event.get("author", {}) or {}
        return bool(author.get("bot")) if isinstance(author, dict) else False
    author = getattr(event, "author", None)
    return bool(getattr(author, "bot", False) or getattr(event, "author_is_bot", False))


def _author_id(event: Any) -> str:
    if isinstance(event, dict):
        author = event.get("author", {}) or {}
        if isinstance(author, dict):
            return str(author.get("id", "") or "")
        return str(event.get("author_id", "") or "")
    author = getattr(event, "author", None)
    return str(getattr(author, "id", "") or getattr(event, "author_id", "") or "")


def _message_id(event: Any) -> str:
    return str(_event_value(event, "id", _event_value(event, "event_id", "")) or "")


def _content(event: Any) -> str:
    return str(_event_value(event, "content", "") or "")


def _content_hash(event: Any) -> str:
    text = _content(event)
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _safe_assertions(discord_sent: bool = False, llm_called: bool = False) -> dict[str, bool]:
    return {
        "api_key_value_logged": False,
        "discord_message_sent": bool(discord_sent),
        "rag_called": False,
        "external_execution": False,
        "raw_discord_ids_logged": False,
        "llm_called": bool(llm_called),
    }


def build_llm_private_test_reply_preflight(env: dict[str, Any] | None = None) -> dict[str, Any]:
    llm_config = build_llm_client_config(env)
    discord_send_enabled = _flag(_first_value(env, ["HERMES_DISCORD_SEND_MESSAGES", "send_messages"], "false"))
    discord_private_reply = _flag(_first_value(env, ["HERMES_DISCORD_PRIVATE_TEST_REPLY", "private_test_reply_enabled"], "false"))
    reply_mode = _first_value(env, ["HERMES_DISCORD_REPLY_MODE", "reply_mode"], "disabled")
    channel_id = _first_value(env, ["HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "_private_test_channel_id"], "")
    llm_reply_enabled = _flag(_env_value(env, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED", "false"))
    llm_reply_mode = _env_value(env, "HERMES_LLM_PRIVATE_TEST_REPLY_MODE", "disabled")
    require_packet = _flag(_env_value(env, "HERMES_LLM_PRIVATE_TEST_REPLY_REQUIRE_PACKET", "true"), True)
    rag_enabled = (
        _flag(_env_value(env, "HERMES_DISCORD_RAG_ENABLED", "false"))
        or _flag(_env_value(env, "HERMES_LLM_RAG_ENABLED", "false"))
        or bool(llm_config.get("rag_enabled"))
    )
    external_execution = (
        _flag(_env_value(env, "HERMES_DISCORD_EXTERNAL_EXECUTION", "false"))
        or _flag(_env_value(env, "HERMES_LLM_EXTERNAL_EXECUTION", "false"))
        or bool(llm_config.get("external_execution"))
    )
    dry_run_only = _flag(_env_value(env, "HERMES_LLM_DRY_RUN_ONLY", "true"), True)
    blocked_reasons: list[str] = []
    checks = [
        ("discord_send_disabled", discord_send_enabled),
        ("private_test_reply_disabled", discord_private_reply),
        ("reply_mode_not_private_test_only", reply_mode == "private_test_only"),
        ("private_test_channel_id_missing", bool(channel_id)),
        ("llm_disabled", bool(llm_config.get("llm_enabled"))),
        ("llm_api_call_disabled", bool(llm_config.get("api_call_enabled"))),
        ("llm_provider_not_openrouter", llm_config.get("provider") == "openrouter"),
        ("llm_model_missing", bool(llm_config.get("model"))),
        ("llm_api_key_missing", bool(llm_config.get("api_key_present"))),
        ("llm_dry_run_only_enabled", not dry_run_only),
        ("llm_dry_call_mode_not_private_test_only", llm_config.get("dry_call_mode") == "private_test_only"),
        ("llm_discord_send_disabled", bool(llm_config.get("discord_send_enabled"))),
        ("llm_private_test_only_disabled", bool(llm_config.get("private_test_only"))),
        ("llm_cost_guard_disabled", bool(llm_config.get("cost_guard_enabled"))),
        ("llm_private_test_reply_disabled", llm_reply_enabled),
        ("llm_private_test_reply_mode_not_private_test_only", llm_reply_mode == "private_test_only"),
        ("llm_private_test_reply_require_packet_disabled", require_packet),
        ("rag_enabled", not rag_enabled),
        ("external_execution_enabled", not external_execution),
    ]
    for reason, passed in checks:
        if not passed:
            blocked_reasons.append(reason)
    report = {
        "report_type": "llm_private_test_reply_preflight",
        "version": VERSION,
        "ready": not blocked_reasons,
        "blocked": bool(blocked_reasons),
        "blocked_reasons": blocked_reasons,
        "private_test_channel_configured": bool(channel_id),
        "llm_provider": llm_config.get("provider", ""),
        "llm_model_configured": bool(llm_config.get("model")),
        "discord_send_enabled": discord_send_enabled,
        "llm_discord_send_enabled": bool(llm_config.get("discord_send_enabled")),
        "rag_enabled": rag_enabled,
        "external_execution": external_execution,
        "reply_mode": reply_mode,
        "llm_reply_mode": llm_reply_mode,
        "require_packet": require_packet,
        "max_replies_per_session": _int(_env_value(env, "HERMES_LLM_PRIVATE_TEST_REPLY_MAX_PER_SESSION", "3"), 3),
        "cooldown_seconds": _int(_env_value(env, "HERMES_LLM_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS", "15"), 15),
        "client_config": public_llm_client_config(llm_config),
        "safety_assertions": _safe_assertions(),
    }
    assert_llm_private_test_reply_report_safe(report)
    return report


def should_allow_llm_private_test_reply(
    event: Any,
    visibility_decision: str,
    safety_decision: dict[str, Any] | None,
    preflight: dict[str, Any],
    output_safety: dict[str, Any] | None = None,
    packet: dict[str, Any] | None = None,
    bot_user_id: Any = "",
) -> dict[str, Any]:
    reason = ""
    channel_id = str(_event_value(event, "channel_id", "") or "")
    private_channel_id = str(_first_value(None, ["HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"], "") or preflight.get("_private_test_channel_id", ""))
    author_id = _author_id(event)
    if _author_is_bot(event) or (bot_user_id and author_id and str(bot_user_id) == author_id) or visibility_decision == "ignored_self_message":
        reason = "self_message"
    elif visibility_decision != "accepted_private_test_channel":
        reason = "private_test_channel_only"
    elif private_channel_id and channel_id != private_channel_id:
        reason = "private_test_channel_only"
    elif preflight.get("ready") is not True:
        reason = "llm_preflight_failed"
    elif safety_decision and not safety_decision.get("allowed"):
        reason = str(safety_decision.get("reason") or "safety_blocked")
    elif output_safety is not None and not output_safety.get("allowed"):
        reason = "output_safety_blocked"
    elif packet is not None:
        try:
            assert_llm_response_packet_safe(packet)
        except Exception:
            reason = "packet_safety_failed"
        if not reason and not packet.get("response_available"):
            reason = "packet_safety_failed"
    if reason:
        return _decision(False, reason)
    will_call_llm = output_safety is None and packet is None
    return {
        "allowed": True,
        "blocked": False,
        "reason": "llm_private_test_reply_allowed",
        "will_call_llm": bool(will_call_llm),
        "will_send_discord": bool(packet is not None),
        "message_sent": False,
        "rag_called": False,
        "external_execution": False,
    }


def _decision(allowed: bool, reason: str) -> dict[str, Any]:
    return {
        "allowed": allowed,
        "blocked": not allowed,
        "reason": reason,
        "will_call_llm": False,
        "will_send_discord": False,
        "message_sent": False,
        "rag_called": False,
        "external_execution": False,
    }


def build_llm_private_test_reply_request(event: Any, agent_route_candidate: str = "marin") -> dict[str, Any]:
    envelope = build_llm_prompt_envelope(agent_route_candidate, _content(event), policy={"max_input_chars": 4000})
    envelope["messages_preview"][0]["content"] += (
        ' Use review-only wording. Preferred safety wording: "This is a review-only draft. '
        'No external action has been taken." Never claim approval, publishing, submission, upload, email send, '
        "contract, price, delivery, RAG access, or external execution."
    )
    return {
        "request_type": "llm_private_test_reply_request",
        "version": VERSION,
        "agent_route_candidate": agent_route_candidate,
        "channel_scope": "private_test_only",
        "event_id": redact_id(_message_id(event)),
        "channel_name": str(_event_value(event, "channel_name", "")),
        "content_hash": _content_hash(event),
        "prompt_envelope": envelope,
        "message_sent": False,
        "rag_called": False,
        "external_execution": False,
    }


def build_llm_private_test_reply_payload(packet: dict[str, Any], max_chars: int = 1800) -> dict[str, Any]:
    assert_llm_response_packet_safe(packet)
    if not packet.get("response_available") or not packet.get("output_safety", {}).get("allowed"):
        raise ValueError("LLM response packet is not sendable.")
    response = redact_text(str(packet.get("response_text", "") or ""), max_chars)
    content = "\n".join(
        [
            "[PRIVATE TEST - LLM REVIEW DRAFT]",
            "This is a review-only draft. No external action has been taken.",
            "",
            response,
        ]
    )[:1900]
    payload = {
        "payload_type": "llm_private_test_reply_payload",
        "version": VERSION,
        "source": "llm_response_packet",
        "content": content,
        "will_send": True,
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "safety_assertions": _safe_assertions(),
    }
    assert_llm_private_test_reply_report_safe(payload)
    return payload


def build_llm_private_test_reply_attempt(
    event: Any,
    env: dict[str, Any] | None = None,
    safety_state: dict[str, Any] | None = None,
    agent_route_candidate: str = "marin",
    llm_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    preflight = build_llm_private_test_reply_preflight(env)
    safety_policy = build_private_test_reply_safety_policy(
        {
            "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": _first_value(env, ["HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "_private_test_channel_id"], ""),
            "HERMES_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS": _env_value(env, "HERMES_LLM_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS", "15"),
            "HERMES_PRIVATE_TEST_MAX_REPLIES_PER_SESSION": _env_value(env, "HERMES_LLM_PRIVATE_TEST_REPLY_MAX_PER_SESSION", "3"),
        }
    )
    state = safety_state if safety_state is not None else build_private_test_reply_safety_state()
    safety_decision = check_private_test_reply_safety(event, safety_policy, state)
    initial = should_allow_llm_private_test_reply(event, "accepted_private_test_channel", safety_decision, preflight)
    if initial.get("blocked"):
        record_private_test_reply_blocked(event, state, initial["reason"])
        return record_llm_private_test_reply_result(event, preflight, initial, safety_decision=safety_decision)

    request = build_llm_private_test_reply_request(event, agent_route_candidate)
    config = build_llm_client_config(env)
    call_config = dict(config)
    call_config["discord_send_enabled"] = False
    call_config["discord_runtime_send_messages"] = False
    validation = validate_llm_client_config(call_config)
    result = llm_result or (call_llm_once(request["prompt_envelope"], call_config) if not validation.get("blocked") else _blocked_llm_result(config))
    output_safety = check_llm_output_allowed(result.get("response_text", ""), build_llm_safety_policy(env))
    dry_report = {
        "report_type": "llm_dry_call_report",
        "version": VERSION,
        "request": {"agent_route_candidate": agent_route_candidate, "channel_scope": "private_test_only"},
        "client_result": result,
        "output_safety": output_safety,
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
    }
    packet = build_llm_response_packet(dry_report)
    final = should_allow_llm_private_test_reply(event, "accepted_private_test_channel", safety_decision, preflight, output_safety, packet)
    payload = build_llm_private_test_reply_payload(packet) if final.get("allowed") else {}
    return record_llm_private_test_reply_result(
        event,
        preflight,
        final,
        request=request,
        client_result=result,
        output_safety=output_safety,
        packet=packet,
        payload=payload,
        safety_decision=safety_decision,
    )


def _blocked_llm_result(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_type": "llm_client_result",
        "version": VERSION,
        "provider": config.get("provider", ""),
        "model": config.get("model", ""),
        "api_call_attempted": False,
        "api_call_succeeded": False,
        "api_call_failed": True,
        "error_type": "client_config_blocked",
        "response_text": "",
        "usage": {"input_chars": 0, "output_chars": 0, "estimated_cost_krw": None, "provider_usage": {}},
        "safety_assertions": _safe_assertions(),
    }


def record_llm_private_test_reply_result(
    event: Any,
    preflight: dict[str, Any],
    decision: dict[str, Any],
    *,
    request: dict[str, Any] | None = None,
    client_result: dict[str, Any] | None = None,
    output_safety: dict[str, Any] | None = None,
    packet: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    safety_decision: dict[str, Any] | None = None,
    message_sent: bool = False,
) -> dict[str, Any]:
    result = {
        "event_type": "llm_private_test_reply_attempt",
        "version": VERSION,
        "created_at": utc_now(),
        "event_id": redact_id(_message_id(event)),
        "channel_name": str(_event_value(event, "channel_name", "")),
        "channel_scope": "private_test_only",
        "allowed": bool(decision.get("allowed")),
        "blocked": bool(decision.get("blocked")),
        "reason": decision.get("reason", ""),
        "llm_api_called": bool(client_result and client_result.get("api_call_attempted")),
        "output_safety_allowed": bool(output_safety and output_safety.get("allowed")),
        "packet_created": bool(packet),
        "discord_send_attempted": bool(message_sent),
        "message_sent": bool(message_sent),
        "provider": preflight.get("llm_provider", ""),
        "model": (client_result or {}).get("model", ""),
        "usage": (client_result or {}).get("usage", {}),
        "preflight": preflight,
        "request": request or {},
        "client_result": client_result or {},
        "output_safety": output_safety or {},
        "packet_summary": {
            "response_available": bool(packet and packet.get("response_available")),
            "output_safety_allowed": bool(packet and packet.get("output_safety", {}).get("allowed")),
            "message_sent": False,
            "discord_send_attempted": False,
            "rag_called": False,
            "external_execution": False,
        },
        "packet": packet or {},
        "payload_preview": {"available": bool(payload), "content_length": len(str((payload or {}).get("content", "")))},
        "safety_decision": safety_decision or {},
        "safety_assertions": _safe_assertions(discord_sent=message_sent, llm_called=bool(client_result and client_result.get("api_call_attempted"))),
    }
    assert_llm_private_test_reply_report_safe(result)
    return result


def write_llm_private_test_reply_audit(record: dict[str, Any], root: str | Path | None = None) -> dict[str, str]:
    repo_root = Path(root or Path.cwd()).resolve()
    stamp = str(record.get("created_at", utc_now()))[:10].replace("-", "")
    event_part = str(record.get("event_id", "event") or "event").replace(":", "-")
    out_dir = repo_root / "exports" / "hermes_gateway" / "llm_private_test_replies" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"llm_private_test_reply_{str(record.get('created_at', utc_now()))[:19].replace('-', '').replace(':', '').replace('T', '_')}_{event_part}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"json_path": str(path)}


async def send_llm_private_test_reply_only(channel: Any, payload: dict[str, Any]) -> dict[str, Any]:
    assert_llm_private_test_reply_report_safe(payload)
    send_func = getattr(channel, "send", None)
    if not callable(send_func):
        return {"message_sent": False, "reason": "channel_send_unavailable"}
    await send_func(payload["content"])
    return {"message_sent": True, "reason": "llm_private_test_reply_sent"}


def render_llm_private_test_reply_report_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL LLM Private Test Reply Preflight",
            "",
            f"- ready: {str(report.get('ready')).lower()}",
            f"- blocked: {str(report.get('blocked')).lower()}",
            f"- blocked_reasons: {', '.join(report.get('blocked_reasons', []))}",
            f"- provider: {report.get('llm_provider', '')}",
            f"- model_configured: {str(report.get('llm_model_configured')).lower()}",
            f"- private_test_channel_configured: {str(report.get('private_test_channel_configured')).lower()}",
            f"- discord_send_enabled: {str(report.get('discord_send_enabled')).lower()}",
            f"- llm_discord_send_enabled: {str(report.get('llm_discord_send_enabled')).lower()}",
            f"- rag_enabled: {str(report.get('rag_enabled')).lower()}",
            f"- external_execution: {str(report.get('external_execution')).lower()}",
            f"- max_replies_per_session: {report.get('max_replies_per_session')}",
            f"- cooldown_seconds: {report.get('cooldown_seconds')}",
        ]
    ) + "\n"


def assert_llm_private_test_reply_report_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("LLM private test reply report contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("LLM private test reply report contains raw Discord-like IDs.")
    if report.get("rag_called"):
        raise ValueError("LLM private test reply report has unsafe execution flags.")
    if report.get("event_type") == "llm_private_test_reply_attempt" and report.get("external_execution"):
        raise ValueError("LLM private test reply report has unsafe execution flags.")
