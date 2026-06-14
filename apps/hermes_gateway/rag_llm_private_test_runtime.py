"""Guarded Phase 33D-1 RAG+LLM private test reply runtime boundary.

The functions in this module are designed for pure decision tests and a future
manually approved live runtime. Tests inject mock LLM and mock Discord send
adapters; this module does not call external providers by itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from llm_safety_policy import build_llm_safety_policy, check_llm_output_allowed
from private_test_reply_safety import (
    build_private_test_reply_safety_policy,
    build_private_test_reply_safety_state,
    check_private_test_reply_safety,
    record_private_test_reply_send_exception,
    record_private_test_reply_sent,
)
from rag_context_safety import build_rag_context_safety_report
from rag_llm_prompt_envelope import build_rag_llm_prompt_envelope
from rag_local_retrieval import run_rag_local_retrieval
from rag_response_packet import build_rag_response_packet
from rag_source_registry import validate_rag_source_name


VERSION = "phase33d_guarded_private_test_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
DEFAULT_SOURCE = "operation"
DEFAULT_QUERY = "STOXL brand tone"
SINGLE_LIVE_TEST_APPROVAL_PHRASE = "I_APPROVE_ONE_PRIVATE_TEST_RAG_LLM_REPLY"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _flag(env: dict[str, Any] | None, key: str, default: bool = False) -> bool:
    source = env if env is not None else os.environ
    value = source.get(key, default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    source = env if env is not None else os.environ
    return str(source.get(key, default) or "").strip()


def _int(env: dict[str, Any] | None, key: str, default: int) -> int:
    try:
        return max(0, int(_value(env, key, str(default))))
    except ValueError:
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
        return getattr(channel, "id" if key == "channel_id" else "name", default)
    return getattr(event, key, default)


def _author_value(event: Any, key: str, default: Any = "") -> Any:
    author = event.get("author", {}) if isinstance(event, dict) else getattr(event, "author", None)
    if isinstance(author, dict):
        return author.get(key, default)
    return getattr(author, key, default)


def _message_hash(event: Any) -> str:
    raw = str(_event_value(event, "id", _event_value(event, "event_id", "")) or "")
    return "redacted-message-id" if not raw else hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _base_decision(reason: str, source: str = DEFAULT_SOURCE, source_valid: bool = True) -> dict[str, Any]:
    return {
        "allowed": False,
        "blocked": True,
        "reason": reason,
        "will_retrieve": False,
        "will_call_llm": False,
        "will_send_discord": False,
        "source": source,
        "source_valid": source_valid,
        "message_sent": False,
        "rag_called": False,
        "llm_api_called": False,
        "discord_send_attempted": False,
        "embedding_called": False,
        "external_execution": False,
    }


def build_single_live_test_manual_approval(env: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    approved_flag = str(source.get("HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED", "") or "").strip().lower()
    approval_phrase = str(source.get("HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE", "") or "").strip()
    return {
        "required": True,
        "approved": approved_flag == "true" and approval_phrase == SINGLE_LIVE_TEST_APPROVAL_PHRASE,
        "approval_phrase_present": bool(approval_phrase),
        "approval_phrase_value_logged": False,
    }


def is_single_live_test_manually_approved(env: Mapping[str, Any] | None = None) -> bool:
    return bool(build_single_live_test_manual_approval(env).get("approved"))


def build_rag_llm_private_reply_preflight(env: dict[str, Any] | None = None, source: str = DEFAULT_SOURCE) -> dict[str, Any]:
    validation = validate_rag_source_name(source)
    checks = [
        ("rag_llm_reply_enabled", _flag(env, "HERMES_RAG_LLM_REPLY_ENABLED")),
        ("reply_mode_private_test_only", _value(env, "HERMES_RAG_LLM_REPLY_MODE", "private_test_only") == "private_test_only"),
        ("discord_send_enabled", _flag(env, "HERMES_DISCORD_SEND_MESSAGES")),
        ("discord_private_test_reply_enabled", _flag(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY")),
        ("discord_reply_mode_private_test_only", _value(env, "HERMES_DISCORD_REPLY_MODE", "private_test_only") == "private_test_only"),
        ("private_test_channel_id_present", bool(_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"))),
        ("rag_enabled", _flag(env, "HERMES_RAG_ENABLED")),
        ("rag_mode_local_readonly", _value(env, "HERMES_RAG_MODE", "local_readonly") == "local_readonly"),
        ("rag_private_test_only", _flag(env, "HERMES_RAG_PRIVATE_TEST_ONLY", True)),
        ("rag_response_packet_required", _flag(env, "HERMES_RAG_REQUIRE_RESPONSE_PACKET", True)),
        ("llm_enabled", _flag(env, "HERMES_LLM_ENABLED")),
        ("llm_api_call_enabled", _flag(env, "HERMES_LLM_API_CALL_ENABLED")),
        ("llm_provider_configured", bool(_value(env, "HERMES_LLM_PROVIDER"))),
        ("llm_model_configured", bool(_value(env, "HERMES_LLM_MODEL"))),
        ("llm_api_key_present", bool(_value(env, "HERMES_LLM_API_KEY"))),
        ("llm_private_test_only", _flag(env, "HERMES_LLM_PRIVATE_TEST_ONLY", True)),
        ("llm_discord_send_enabled", _flag(env, "HERMES_LLM_DISCORD_SEND_ENABLED")),
        ("llm_private_test_reply_enabled", _flag(env, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED")),
        ("discord_external_execution_disabled", not _flag(env, "HERMES_DISCORD_EXTERNAL_EXECUTION")),
        ("llm_external_execution_disabled", not _flag(env, "HERMES_LLM_EXTERNAL_EXECUTION")),
        ("source_valid", bool(validation.get("valid")) and source != "operations"),
    ]
    failed = [name for name, passed in checks if not passed]
    report = {
        "report_type": "rag_llm_private_test_runtime_preflight",
        "version": VERSION,
        "ready": not failed,
        "blocked": bool(failed),
        "blocked_reasons": failed,
        "source": source,
        "source_valid": bool(validation.get("valid")) and source != "operations",
        "private_test_channel_configured": bool(_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID")),
        "rag_mode": _value(env, "HERMES_RAG_MODE", "local_readonly"),
        "provider": _value(env, "HERMES_LLM_PROVIDER"),
        "model_configured": bool(_value(env, "HERMES_LLM_MODEL")),
        "single_live_test_manual_approval": build_single_live_test_manual_approval(env),
        "actual_discord_send": False,
        "actual_llm_api_call": False,
        "embedding_api_called": False,
        "external_execution": False,
        "safety_assertions": _safe_assertions(),
    }
    assert_runtime_report_safe(report)
    return report


def should_allow_rag_llm_private_reply(
    event: Any,
    preflight: dict[str, Any],
    source: str = DEFAULT_SOURCE,
    safety_state: dict[str, Any] | None = None,
    env: dict[str, Any] | None = None,
    bot_user_id: Any = "",
) -> dict[str, Any]:
    validation = validate_rag_source_name(source)
    if not validation.get("valid"):
        return _base_decision("operations_source_blocked_before_retrieval" if source == "operations" else "invalid_source_blocked_before_retrieval", source, False)
    channel_id = str(_event_value(event, "channel_id", "") or "")
    private_channel_id = _value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID")
    channel_scope = str(_event_value(event, "channel_scope", "") or "")
    if channel_scope in {"public", "team", "mapped"}:
        return _base_decision("public_channel_blocked_before_retrieval", source, True)
    if private_channel_id and channel_id != private_channel_id:
        return _base_decision("private_channel_id_mismatch_blocked", source, True)
    author_is_bot = bool(_author_value(event, "bot", False) or _event_value(event, "author_is_bot", False))
    author_id = str(_author_value(event, "id", "") or "")
    if author_is_bot or (bot_user_id and author_id and author_id == str(bot_user_id)):
        return _base_decision("self_or_bot_blocked_before_retrieval", source, True)
    if not preflight.get("ready"):
        return _base_decision("preflight_failed_before_retrieval", source, True)
    safety_policy = build_private_test_reply_safety_policy(_runtime_safety_env(env))
    state = safety_state or build_private_test_reply_safety_state()
    safety = check_private_test_reply_safety(event, safety_policy, state)
    if not safety.get("allowed"):
        reason_map = {
            "duplicate_message": "duplicate_blocked_before_retrieval",
            "cooldown_active": "cooldown_blocked_before_retrieval",
            "reply_budget_exhausted": "budget_exhausted_blocked_before_retrieval",
            "rate_limit_seen": "circuit_breaker_blocked_before_retrieval",
            "send_exception_seen": "circuit_breaker_blocked_before_retrieval",
            "bot_message": "self_or_bot_blocked_before_retrieval",
            "self_message": "self_or_bot_blocked_before_retrieval",
        }
        return _base_decision(reason_map.get(str(safety.get("reason")), str(safety.get("reason", "safety_blocked_before_retrieval"))), source, True)
    allowed = _base_decision("private_test_rag_llm_reply_allowed", source, True)
    allowed.update({"allowed": True, "blocked": False, "will_retrieve": True, "will_call_llm": True, "will_send_discord": True})
    return allowed


def build_rag_llm_reply_pipeline_plan(
    event: Any,
    root: str | Path | None = None,
    env: dict[str, Any] | None = None,
    source: str = DEFAULT_SOURCE,
    query: str = DEFAULT_QUERY,
    safety_state: dict[str, Any] | None = None,
    llm_client: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    send_adapter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    bot_user_id: Any = "",
) -> dict[str, Any]:
    preflight = build_rag_llm_private_reply_preflight(env, source=source)
    decision = should_allow_rag_llm_private_reply(event, preflight, source=source, safety_state=safety_state, env=env, bot_user_id=bot_user_id)
    if not decision.get("allowed"):
        return _attempt(event, decision, preflight=preflight)

    max_docs = _int(env, "HERMES_RAG_LLM_MAX_DOCUMENTS", 5)
    max_chars = _int(env, "HERMES_RAG_LLM_MAX_CONTEXT_CHARS", 3000)
    retrieval = run_rag_local_retrieval(root=root, source=source, query=query, max_files=max_docs + 1, max_chars_per_file=max(max_chars, 4000))
    context = build_rag_context_safety_report(retrieval, source=source, max_documents=max_docs, max_context_chars=max_chars)
    if not context.get("allowed_for_llm_prompt"):
        return _attempt(event, _blocked_after("context_safety_blocked", source), preflight=preflight, retrieval=retrieval, context=context)

    packet = build_rag_response_packet(retrieval)
    if not packet.get("response_available"):
        return _attempt(event, _blocked_after("rag_response_packet_missing", source), preflight=preflight, retrieval=retrieval, context=context, rag_packet=packet)

    envelope = build_rag_llm_prompt_envelope(root=str(root) if root else None, source=source, query=query)
    result = llm_client(envelope) if llm_client else _mock_provider_not_called()
    llm_called = bool(result.get("api_call_attempted"))
    if not result.get("api_call_succeeded"):
        return _attempt(event, _blocked_after("llm_provider_error", source), preflight=preflight, retrieval=retrieval, context=context, rag_packet=packet, envelope=envelope, llm_result=result, llm_called=llm_called)

    output_safety = check_llm_output_allowed(str(result.get("response_text", "")), build_llm_safety_policy({"HERMES_LLM_ALLOW_DISCORD_SEND": "false"}))
    if not output_safety.get("allowed"):
        return _attempt(event, _blocked_after("output_safety_blocked", source), preflight=preflight, retrieval=retrieval, context=context, rag_packet=packet, envelope=envelope, llm_result=result, output_safety=output_safety, llm_called=llm_called)

    payload = build_rag_llm_reply_send_payload(result.get("response_text", ""), packet)
    if not payload.get("safe"):
        return _attempt(event, _blocked_after("packet_safety_failed", source), preflight=preflight, retrieval=retrieval, context=context, rag_packet=packet, envelope=envelope, llm_result=result, output_safety=output_safety, payload=payload, llm_called=llm_called)

    send_result = send_adapter(payload) if send_adapter else {"message_sent": False, "error_type": "send_adapter_missing"}
    if send_result.get("error_type"):
        state = safety_state or build_private_test_reply_safety_state()
        record_private_test_reply_send_exception(event, state, str(send_result.get("error_type")))
        return _attempt(event, _blocked_after("send_exception", source), preflight=preflight, retrieval=retrieval, context=context, rag_packet=packet, envelope=envelope, llm_result=result, output_safety=output_safety, payload=payload, llm_called=llm_called, discord_send_attempted=True)
    if send_result.get("message_sent"):
        state = safety_state or build_private_test_reply_safety_state()
        record_private_test_reply_sent(event, state)
        final = _attempt(event, {"allowed": True, "blocked": False, "reason": "private_test_rag_llm_reply_allowed", "will_retrieve": True, "will_call_llm": True, "will_send_discord": True, "source": source, "source_valid": True, "message_sent": True, "rag_called": True, "llm_api_called": llm_called, "discord_send_attempted": True, "embedding_called": False, "external_execution": False}, preflight=preflight, retrieval=retrieval, context=context, rag_packet=packet, envelope=envelope, llm_result=result, output_safety=output_safety, payload=payload, llm_called=llm_called, discord_send_attempted=True)
        final["message_sent"] = True
        return final
    return _attempt(event, _blocked_after("send_not_confirmed", source), preflight=preflight, retrieval=retrieval, context=context, rag_packet=packet, envelope=envelope, llm_result=result, output_safety=output_safety, payload=payload, llm_called=llm_called, discord_send_attempted=True)


def build_rag_llm_reply_send_payload(response_text: str, rag_packet: dict[str, Any]) -> dict[str, Any]:
    text = _sanitize(str(response_text or ""))
    body = "[RAG+LLM PRIVATE TEST - REVIEW DRAFT]\nThis is a review-only draft. No external action has been taken.\n\n" + text
    citations = [item.get("path", "") for item in rag_packet.get("citations", [])[:3]]
    if citations:
        body += "\n\nSources: " + ", ".join(citations)
    body = body[:1900]
    safe = not SECRET_RE.search(body) and not LONG_ID_RE.search(body) and ":\\" not in body and "\\\\" not in body
    return {
        "payload_type": "rag_llm_private_test_send_payload",
        "version": VERSION,
        "safe": safe,
        "content": body,
        "source": rag_packet.get("source", DEFAULT_SOURCE),
        "will_send_discord": safe,
        "message_sent": False,
        "discord_send_attempted": False,
    }


def record_rag_llm_reply_attempt(attempt: dict[str, Any], root: str | Path | None = None, write: bool = False) -> dict[str, Any]:
    record = {key: value for key, value in attempt.items() if key not in {"payload"}}
    record["event_type"] = "rag_llm_private_test_reply_attempt"
    record["version"] = VERSION
    record["safety_assertions"] = _safe_assertions()
    assert_runtime_report_safe(record)
    if not write:
        return {"written": False, "record": record, "path": ""}
    base = Path(root or Path.cwd()).resolve() / "exports" / "hermes_gateway" / "rag_llm_private_test_replies" / datetime.now(timezone.utc).strftime("%Y%m%d")
    base.mkdir(parents=True, exist_ok=True)
    filename = "rag_llm_private_test_reply_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + str(record.get("redacted_message_id", "redacted-message-id")) + ".json"
    path = base / filename
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"written": True, "record": record, "path": str(path)}


def build_rag_llm_private_test_runtime_report(root: str | Path | None = None, env: dict[str, Any] | None = None) -> dict[str, Any]:
    preflight = build_rag_llm_private_reply_preflight(env, source=DEFAULT_SOURCE)
    manual_approval = build_single_live_test_manual_approval(env)
    report = {
        "report_type": "rag_llm_private_test_runtime_report",
        "version": VERSION,
        "ready": bool(preflight.get("ready")),
        "blocked": bool(preflight.get("blocked")),
        "blocked_reasons": preflight.get("blocked_reasons", []),
        "runtime_option": "--run-discord-private-test-rag-llm-reply",
        "runtime_option_added": True,
        "runtime_executed_by_report": False,
        "actual_discord_send": False,
        "actual_llm_api_call": False,
        "embedding_api_called": False,
        "external_execution": False,
        "single_live_test_manual_approval": manual_approval,
        "preflight": preflight,
        "safety_assertions": _safe_assertions(),
    }
    assert_runtime_report_safe(report)
    return report


def run_discord_private_test_rag_llm_reply_bot(
    root: str | Path | None = None,
    env: dict[str, Any] | None = None,
    start_adapter: Callable[[str | Path | None, dict[str, Any] | None, dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    preflight = build_rag_llm_private_reply_preflight(env, source=DEFAULT_SOURCE)
    manual_approval = build_single_live_test_manual_approval(env)
    if not preflight.get("ready"):
        return {
            "started": False,
            "blocked": True,
            "reason": "rag_llm_private_test_runtime_preflight_failed:" + str(preflight.get("blocked_reasons", ["unknown"])[0]),
            "message_sent": False,
            "token_value_logged": False,
            "single_live_test_manual_approval": manual_approval,
            "preflight": preflight,
            "safety_assertions": _safe_assertions(),
        }
    if not manual_approval.get("approved"):
        return {
            "started": False,
            "blocked": True,
            "reason": "live_execution_requires_separate_manual_approval",
            "message_sent": False,
            "token_value_logged": False,
            "single_live_test_manual_approval": manual_approval,
            "preflight": preflight,
            "safety_assertions": _safe_assertions(),
        }
    if start_adapter is None:
        return {
            "started": False,
            "blocked": True,
            "reason": "rag_llm_private_test_runtime_start_adapter_missing",
            "message_sent": False,
            "token_value_logged": False,
            "single_live_test_manual_approval": manual_approval,
            "preflight": preflight,
            "safety_assertions": _safe_assertions(),
        }
    result = start_adapter(root, env, preflight)
    result.setdefault("started", False)
    result.setdefault("blocked", False)
    result.setdefault("message_sent", False)
    result.setdefault("token_value_logged", False)
    result["single_live_test_manual_approval"] = manual_approval
    result["preflight"] = preflight
    result["safety_assertions"] = _safe_assertions()
    assert_runtime_report_safe(result)
    return result


def render_rag_llm_private_test_runtime_markdown(report: dict[str, Any]) -> str:
    approval = report.get("single_live_test_manual_approval", {})
    return "\n".join(
        [
            "# STOXL RAG+LLM Private Test Runtime",
            "",
            f"- Ready: {str(report.get('ready')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Runtime option: {report.get('runtime_option')}",
            "- Runtime executed by report: false",
            "- Actual Discord send: false",
            "- Actual LLM API call: false",
            "- Embedding API called: false",
            "- External execution: false",
            f"- Single live manual approval required: {str(approval.get('required', True)).lower()}",
            f"- Single live manual approval approved: {str(approval.get('approved', False)).lower()}",
            f"- Approval phrase present: {str(approval.get('approval_phrase_present', False)).lower()}",
            "- Approval phrase value logged: false",
            f"- Blocked reasons: {', '.join(report.get('blocked_reasons', [])) or 'none'}",
        ]
    ) + "\n"


def _blocked_after(reason: str, source: str) -> dict[str, Any]:
    decision = _base_decision(reason, source, True)
    decision["will_retrieve"] = True
    return decision


def _attempt(event: Any, decision: dict[str, Any], **parts: Any) -> dict[str, Any]:
    attempt = {
        "event_type": "rag_llm_private_test_reply_attempt",
        "version": VERSION,
        "created_at": utc_now(),
        "allowed": bool(decision.get("allowed")),
        "blocked": bool(decision.get("blocked")),
        "reason": decision.get("reason", ""),
        "source": decision.get("source", DEFAULT_SOURCE),
        "source_valid": bool(decision.get("source_valid")),
        "redacted_message_id": _message_hash(event),
        "channel_scope": "private_test_only",
        "retrieval_executed": bool(decision.get("rag_called") or decision.get("will_retrieve") and decision.get("reason") not in {"public_channel_blocked_before_retrieval", "private_channel_id_mismatch_blocked", "self_or_bot_blocked_before_retrieval", "duplicate_blocked_before_retrieval", "cooldown_blocked_before_retrieval", "budget_exhausted_blocked_before_retrieval", "invalid_source_blocked_before_retrieval", "operations_source_blocked_before_retrieval", "preflight_failed_before_retrieval"}),
        "context_safety_allowed": bool(parts.get("context", {}).get("allowed_for_llm_prompt")) if isinstance(parts.get("context"), dict) else False,
        "rag_response_packet_created": bool(parts.get("rag_packet", {}).get("response_available")) if isinstance(parts.get("rag_packet"), dict) else False,
        "llm_api_called": bool(parts.get("llm_called", decision.get("llm_api_called", False))),
        "output_safety_allowed": bool(parts.get("output_safety", {}).get("allowed")) if isinstance(parts.get("output_safety"), dict) else False,
        "discord_send_attempted": bool(parts.get("discord_send_attempted", decision.get("discord_send_attempted", False))),
        "message_sent": bool(decision.get("message_sent", False)),
        "rag_called": bool(decision.get("rag_called", False) or parts.get("retrieval")),
        "embedding_api_called": False,
        "external_execution": False,
        "decision": decision,
        "preflight": parts.get("preflight", {}),
        "payload": parts.get("payload", {}),
        "safety_assertions": _safe_assertions(),
    }
    assert_runtime_report_safe(attempt)
    return attempt


def _runtime_safety_env(env: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": _value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "HERMES_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS": _value(env, "HERMES_RAG_LLM_COOLDOWN_SECONDS", "20"),
        "HERMES_PRIVATE_TEST_MAX_REPLIES_PER_SESSION": _value(env, "HERMES_RAG_LLM_MAX_REPLIES_PER_SESSION", "2"),
        "HERMES_DISCORD_EXTERNAL_EXECUTION": _value(env, "HERMES_DISCORD_EXTERNAL_EXECUTION", "false"),
        "HERMES_DISCORD_RAG_ENABLED": "false",
    }


def _mock_provider_not_called() -> dict[str, Any]:
    return {
        "api_call_attempted": False,
        "api_call_succeeded": False,
        "api_call_failed": True,
        "error_type": "llm_client_not_provided",
        "response_text": "",
    }


def _sanitize(text: str) -> str:
    return LONG_ID_RE.sub("[REDACTED_DISCORD_ID]", SECRET_RE.sub("[REDACTED_SECRET]", text))


def _safe_assertions() -> dict[str, bool]:
    return {
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "embedding_called": False,
        "llm_called": False,
        "discord_message_sent": False,
        "external_execution": False,
    }


def assert_runtime_report_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG+LLM runtime report contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG+LLM runtime report contains raw Discord-like IDs.")
    if isinstance(report, dict):
        if report.get("embedding_api_called") or report.get("external_execution"):
            raise ValueError("RAG+LLM runtime report has unsafe execution flags.")
