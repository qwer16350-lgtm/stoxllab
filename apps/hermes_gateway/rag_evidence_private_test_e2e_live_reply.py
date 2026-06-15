"""Phase 34L-1 manually approved private-test E2E live reply.

Default behavior is blocked/report-only. A live path can run only when the
explicit CLI allow flag and every manual env gate pass. Tests inject one
private-test event, a mock LLM runner, and a mock sender; the default CLI report
does not connect to Discord, call LLM providers, or send messages.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from knowledge_dry_chain import build_knowledge_dry_chain_report
from rag_evidence_llm_dry_call import (
    APPROVAL_PHRASE as LLM_APPROVAL_PHRASE,
    build_rag_evidence_llm_dry_call_report,
)
from rag_evidence_private_test_e2e_preflight import build_rag_evidence_private_test_e2e_preflight
from rag_evidence_prompt_envelope import build_rag_evidence_prompt_envelope


VERSION = "phase34l1_manual_private_test_e2e_live_reply_one_run"
APPROVAL_PHRASE = "I_APPROVE_ONE_PRIVATE_TEST_RAG_EVIDENCE_E2E_REPLY"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
MENTION_RE = re.compile(r"(@everyone|@here|<@!?\d+>|<@&\d+>)", re.IGNORECASE)

Sender = Callable[[str, str], dict[str, Any]]
ClientRunner = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]
OPENROUTER_API_KEY_ALIASES = ["OPENROUTER_API_KEY", "HERMES_OPENROUTER_API_KEY"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _openrouter_api_key_present(env: dict[str, Any] | None = None) -> bool:
    source = os.environ if env is None else env
    return bool(source.get("OPENROUTER_API_KEY") or source.get("HERMES_OPENROUTER_API_KEY"))


def _openrouter_api_key_value_for_client(env: dict[str, Any] | None = None) -> str:
    source = os.environ if env is None else env
    return str(source.get("OPENROUTER_API_KEY") or source.get("HERMES_OPENROUTER_API_KEY") or "")


def build_manual_approval_report(env: dict[str, Any] | None = None) -> dict[str, Any]:
    approved_flag = _flag(_env_value(env, "HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVED", "false"))
    phrase_value = _env_value(env, "HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVAL_PHRASE", "")
    phrase_ok = phrase_value == APPROVAL_PHRASE
    return {
        "required": True,
        "approved": bool(approved_flag and phrase_ok),
        "approval_flag_true": bool(approved_flag),
        "approval_phrase_present": bool(phrase_value),
        "approval_phrase_exact_match": bool(phrase_ok),
        "approval_phrase_value_logged": False,
    }


def build_llm_manual_approval_report(env: dict[str, Any] | None = None) -> dict[str, Any]:
    approved_flag = _flag(_env_value(env, "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED", "false"))
    phrase_value = _env_value(env, "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE", "")
    phrase_ok = phrase_value == LLM_APPROVAL_PHRASE
    return {
        "required": True,
        "approved": bool(approved_flag and phrase_ok),
        "approval_flag_true": bool(approved_flag),
        "approval_phrase_present": bool(phrase_value),
        "approval_phrase_exact_match": bool(phrase_ok),
        "approval_phrase_value_logged": False,
    }


def _default_state() -> dict[str, Any]:
    return {"processed_message_ids": [], "sent_message_keys": [], "message_sent_count": 0, "llm_api_call_count": 0}


def _safety_assertions(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "api_key_value_logged": False,
        "token_value_logged": False,
        "raw_discord_ids_logged": False,
        "approval_phrase_value_logged": False,
        "public_channel_reply_called": False,
        "team_channel_reply_called": False,
        "llm_call_count": int(report.get("llm_api_call_count", 0) or 0),
        "discord_message_sent_count": int(report.get("message_sent_count", 0) or 0),
        "embedding_called": False,
        "external_execution": False,
    }


def _base_report(env: dict[str, Any] | None, *, allow_live_reply: bool) -> dict[str, Any]:
    manual = build_manual_approval_report(env)
    llm_manual = build_llm_manual_approval_report(env)
    channel_id = _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "")
    send_messages = _flag(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES", "false"))
    private_reply = _flag(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY", "false"))
    reply_mode_private = _env_value(env, "HERMES_DISCORD_REPLY_MODE", "") == "private_test_only"
    return {
        "report_type": "rag_evidence_private_test_e2e_live_reply",
        "version": VERSION,
        "created_at": utc_now(),
        "manual_approval": manual,
        "llm_manual_approval": llm_manual,
        "private_test_channel_configured": bool(channel_id),
        "private_test_channel_only": True,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "openrouter_api_key_present": _openrouter_api_key_present(env),
        "openrouter_api_key_aliases_checked": list(OPENROUTER_API_KEY_ALIASES),
        "openrouter_api_key_value_logged": False,
        "allow_flag_present": bool(allow_live_reply),
        "ready": False,
        "blocked": True,
        "blocked_reasons": [],
        "discord_live_runtime_executed": False,
        "discord_event_received": False,
        "accepted_private_test_channel": False,
        "public_channel_event_rejected": False,
        "team_channel_event_rejected": False,
        "knowledge_dry_chain_executed": False,
        "evidence_packet_created": False,
        "rag_response_packet_created": False,
        "review_packet_created": False,
        "prompt_envelope_created": False,
        "prompt_safety_checked": False,
        "prompt_safety_allowed": False,
        "prompt_safety_blocked": False,
        "llm_stage_reached": False,
        "llm_call_allowed": False,
        "llm_dispatch_invoked": False,
        "llm_dispatch_mode": "",
        "llm_dispatch_blocked_reason": "",
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "llm_api_call_count": 0,
        "llm_response_packet_created": False,
        "output_safety_checked": False,
        "output_safety_allowed": False,
        "output_safety_blocked": False,
        "discord_api_send_allowed": False,
        "discord_send_stage_reached": False,
        "discord_api_send_attempted": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "discord_send_failed": False,
        "discord_send_failure_reason": "",
        "llm_response_available_for_send_retry": False,
        "ready_for_phase34l1e_send_retry_without_llm": False,
        "partial_success_artifact": {},
        "sent_channel_scope": "",
        "sent_message_review_only": False,
        "self_loop_guard_triggered": False,
        "self_message_reply_attempted": False,
        "bot_message_reply_attempted": False,
        "duplicate_send_blocked": False,
        "embedding_api_called": False,
        "external_execution": False,
        "ready_for_phase34l2_e2e_live_reply_closeout": False,
        "ready_for_unattended_auto_reply": False,
        "runtime_flags": {
            "discord_send_messages_enabled": send_messages,
            "discord_private_test_reply_enabled": private_reply,
            "reply_mode_private_test_only": reply_mode_private,
            "private_test_channel_id_present": bool(channel_id),
        },
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "public_channel_reply_called": False,
            "team_channel_reply_called": False,
            "llm_call_count": 0,
            "discord_message_sent_count": 0,
            "embedding_called": False,
            "external_execution": False,
        },
    }


def _preflight_block_reasons(env: dict[str, Any] | None, *, allow_live_reply: bool, preflight: dict[str, Any]) -> list[str]:
    manual = build_manual_approval_report(env)
    llm_manual = build_llm_manual_approval_report(env)
    reasons: list[str] = []
    if not allow_live_reply:
        reasons.append("allow_rag_evidence_private_test_e2e_live_reply_required")
    if not manual.get("approved"):
        reasons.append("manual_approval_required")
    if not llm_manual.get("approved"):
        reasons.append("llm_manual_approval_required")
    if not preflight.get("ready_for_phase34l1_manual_e2e_live_reply"):
        reasons.append("phase34k_e2e_preflight_required")
    if not _flag(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES", "false")):
        reasons.append("discord_send_messages_disabled")
    if not _flag(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY", "false")):
        reasons.append("discord_private_test_reply_disabled")
    if _env_value(env, "HERMES_DISCORD_REPLY_MODE", "") != "private_test_only":
        reasons.append("reply_mode_not_private_test_only")
    if not _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", ""):
        reasons.append("private_test_channel_id_missing")
    return reasons


def _event_channel_scope(event: dict[str, Any], private_channel_id: str) -> str:
    if str(event.get("channel_id", "") or "") == str(private_channel_id or ""):
        return "private_test_only"
    return str(event.get("channel_scope", "") or "unmapped")


def _event_block_reasons(event: dict[str, Any], env: dict[str, Any] | None, state: dict[str, Any]) -> list[str]:
    private_channel_id = _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "")
    scope = _event_channel_scope(event, private_channel_id)
    message_id = str(event.get("message_id", "") or "")
    reasons: list[str] = []
    if event.get("author_is_bot") or event.get("is_self"):
        reasons.append("self_or_bot_message_skipped")
    if message_id and message_id in set(state.get("processed_message_ids", [])):
        reasons.append("duplicate_message_skipped")
    if scope == "public":
        reasons.append("public_channel_event_rejected")
    elif scope == "team":
        reasons.append("team_channel_event_rejected")
    elif scope != "private_test_only":
        reasons.append("private_test_channel_id_mismatch")
    if not str(event.get("content", "") or "").strip():
        reasons.append("message_content_missing")
    return reasons


def _llm_env_for_call(env: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(os.environ if env is None else env)
    source["HERMES_DISCORD_SEND_MESSAGES"] = "false"
    source["HERMES_LLM_DISCORD_SEND_ENABLED"] = "false"
    source["HERMES_DISCORD_RAG_ENABLED"] = "false"
    source["HERMES_DISCORD_EXTERNAL_EXECUTION"] = "false"
    source.setdefault("HERMES_LLM_PROVIDER", "openrouter")
    source.setdefault("HERMES_LLM_MODEL", "openai/gpt-5.4-mini")
    source["HERMES_LLM_ENABLED"] = "true"
    source["HERMES_LLM_API_CALL_ENABLED"] = "true"
    source["HERMES_LLM_DRY_CALL_MODE"] = "private_test_only"
    source["HERMES_LLM_PRIVATE_TEST_ONLY"] = "true"
    source["HERMES_LLM_COST_GUARD_ENABLED"] = "true"
    if not source.get("HERMES_LLM_API_KEY"):
        source["HERMES_LLM_API_KEY"] = _openrouter_api_key_value_for_client(env)
    return source


def _llm_dispatch_blocked_reason(env: dict[str, Any] | None, *, client_runner: ClientRunner | None) -> str:
    if not build_llm_manual_approval_report(env).get("approved"):
        phrase_present = bool(_env_value(env, "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE", ""))
        return "llm_approval_phrase_mismatch" if phrase_present else "llm_approval_missing"
    if client_runner is None and not _openrouter_api_key_present(env):
        return "openrouter_api_key_missing"
    return ""


def _sanitize_mentions(text: str) -> tuple[str, bool]:
    blocked = False

    def replace(match: re.Match[str]) -> str:
        nonlocal blocked
        blocked = True
        value = match.group(0).lower()
        if value in {"@everyone", "@here"}:
            return "[blocked_group_mention]"
        return "[blocked_discord_mention]"

    return MENTION_RE.sub(replace, text), blocked


def _send_content(llm_report: dict[str, Any]) -> tuple[str, bool]:
    client = llm_report.get("client_result", {}) if isinstance(llm_report.get("client_result"), dict) else {}
    response_text = str(client.get("response_text", "") or "")
    content = (
        "[PRIVATE TEST E2E / REVIEW ONLY]\n\n"
        f"{response_text}\n\n"
        "This is a review-only private-test reply. No external action has been taken."
    )
    sanitized, mention_blocked = _sanitize_mentions(content)
    return sanitized[:1600], mention_blocked


def _message_key(content: str) -> str:
    return "rag_evidence_e2e_live:" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _mark_blocked(report: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    report["blocked_reasons"] = reasons
    report["blocked"] = True
    report["ready"] = False
    report["safety_assertions"] = _safety_assertions(report)
    assert_rag_evidence_private_test_e2e_live_reply_safe(
        report,
        allow_sent=bool(report.get("discord_message_sent")),
        allow_llm_called=bool(report.get("llm_api_called")),
    )
    return report


def _discord_send_failure_result(error_type: str) -> dict[str, Any]:
    reason = str(error_type or "discord_send_failed")
    disconnected = reason in {"ServerDisconnectedError", "ConnectionResetError", "ClientConnectionError", "GatewayNotFound"}
    return {
        "attempted": not disconnected,
        "called": not disconnected,
        "reason": reason,
    }


def build_partial_success_artifact(report: dict[str, Any]) -> dict[str, Any]:
    artifact = {
        "report_type": "rag_evidence_private_test_e2e_partial_success",
        "version": "phase34l1e_llm_success_send_failed_no_retry_yet",
        "llm_api_called": bool(report.get("llm_api_called")),
        "llm_api_call_count": int(report.get("llm_api_call_count", 0) or 0),
        "llm_response_packet_created": bool(report.get("llm_response_packet_created")),
        "output_safety_checked": bool(report.get("output_safety_checked")),
        "output_safety_allowed": bool(report.get("output_safety_allowed")),
        "discord_message_sent": False,
        "message_sent_count": 0,
        "send_retry_allowed_without_llm": True,
        "send_retry_requires_manual_approval": True,
        "ready_for_manual_send_retry_without_llm": True,
        "ready_for_phase34l2_e2e_live_reply_closeout": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "llm_call_count": int(report.get("llm_api_call_count", 0) or 0),
            "discord_message_sent_count": 0,
            "embedding_called": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_private_test_e2e_live_reply_safe({**report, "partial_success_artifact": {}}, allow_llm_called=True)
    return artifact


def build_rag_evidence_private_test_e2e_live_reply_report(
    root: str | Path | None = None,
    *,
    allow_live_reply: bool = False,
    env: dict[str, Any] | None = None,
    event: dict[str, Any] | None = None,
    client_runner: ClientRunner | None = None,
    sender: Sender | None = None,
    state: dict[str, Any] | None = None,
    preflight: dict[str, Any] | None = None,
    prompt_envelope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_preflight = preflight or build_rag_evidence_private_test_e2e_preflight(root=root)
    selected_state = state if state is not None else _default_state()
    report = _base_report(env, allow_live_reply=allow_live_reply)
    reasons = _preflight_block_reasons(env, allow_live_reply=allow_live_reply, preflight=selected_preflight)
    if reasons:
        return _mark_blocked(report, reasons)

    selected_event = event
    if selected_event is None:
        return run_actual_discord_private_test_e2e_live_reply(root=root, env=env, state=selected_state)

    report["ready"] = True
    report["blocked"] = False
    report["discord_live_runtime_executed"] = True
    report["discord_event_received"] = True
    event_reasons = _event_block_reasons(selected_event, env, selected_state)
    if selected_event.get("author_is_bot") or selected_event.get("is_self"):
        report["self_loop_guard_triggered"] = True
    if "duplicate_message_skipped" in event_reasons:
        report["duplicate_send_blocked"] = True
    if "public_channel_event_rejected" in event_reasons:
        report["public_channel_event_rejected"] = True
    if "team_channel_event_rejected" in event_reasons:
        report["team_channel_event_rejected"] = True
    if event_reasons:
        return _mark_blocked(report, event_reasons)

    message_id = str(selected_event.get("message_id", "") or "")
    if message_id:
        selected_state.setdefault("processed_message_ids", []).append(message_id)
    report["accepted_private_test_channel"] = True
    report["public_channel_event_rejected"] = True
    report["team_channel_event_rejected"] = True
    knowledge = build_knowledge_dry_chain_report(root=root)
    prompt = prompt_envelope or build_rag_evidence_prompt_envelope(root=root, query=str(selected_event.get("content", "") or "STOXL brand tone"))
    report["knowledge_dry_chain_executed"] = bool(knowledge)
    report["evidence_packet_created"] = bool(knowledge.get("evidence_packet_available"))
    report["rag_response_packet_created"] = bool(knowledge.get("rag_response_packet_available"))
    report["review_packet_created"] = bool(knowledge.get("review_packet_available"))
    report["prompt_envelope_created"] = bool(prompt.get("prompt_envelope_created"))
    report["prompt_safety_checked"] = bool(report["prompt_envelope_created"])
    report["prompt_safety_allowed"] = bool(prompt.get("ready_for_prompt_preview") and prompt.get("review_only"))
    report["prompt_safety_blocked"] = bool(report["prompt_safety_checked"] and not report["prompt_safety_allowed"])
    if report["prompt_safety_blocked"]:
        return _mark_blocked(report, ["prompt_safety_blocked"])

    report["llm_stage_reached"] = True
    dispatch_blocked_reason = _llm_dispatch_blocked_reason(env, client_runner=client_runner)
    if not report["accepted_private_test_channel"]:
        dispatch_blocked_reason = "private_test_channel_not_accepted"
    elif not report["prompt_safety_allowed"]:
        dispatch_blocked_reason = "prompt_safety_not_allowed"
    elif not report.get("manual_approval", {}).get("approved"):
        dispatch_blocked_reason = "e2e_approval_missing"
    report["llm_dispatch_blocked_reason"] = dispatch_blocked_reason
    report["llm_call_allowed"] = bool(not dispatch_blocked_reason)
    if not report["llm_call_allowed"]:
        return _mark_blocked(report, [dispatch_blocked_reason or "llm_call_not_allowed"])

    report["llm_dispatch_invoked"] = True
    report["llm_dispatch_mode"] = "mock_openrouter_once" if client_runner else "actual_openrouter_once"
    try:
        llm_report = build_rag_evidence_llm_dry_call_report(
            root=root,
            query=str(selected_event.get("content", "") or "STOXL brand tone"),
            allow_api_call=True,
            env=_llm_env_for_call(env),
            client_runner=client_runner,
        )
    except Exception:
        report["llm_call_allowed"] = False
        report["llm_dispatch_invoked"] = False
        report["llm_dispatch_mode"] = ""
        report["llm_dispatch_blocked_reason"] = "llm_dispatch_exception"
        return _mark_blocked(report, ["llm_dispatch_exception"])
    report["llm_api_call_attempted"] = bool(llm_report.get("api_call_attempted"))
    report["llm_api_called"] = bool(report["llm_api_call_attempted"])
    report["llm_api_call_count"] = 1 if report["llm_api_call_attempted"] else 0
    report["llm_response_packet_created"] = bool(llm_report.get("api_call_succeeded") or llm_report.get("llm_response_packet_created"))
    report["output_safety_checked"] = bool(report["llm_response_packet_created"])
    report["output_safety_allowed"] = bool(report["output_safety_checked"] and llm_report.get("output_safety_allowed"))
    report["output_safety_blocked"] = bool(report["output_safety_checked"] and not report["output_safety_allowed"])
    selected_state["llm_api_call_count"] = int(selected_state.get("llm_api_call_count", 0)) + int(report["llm_api_call_count"])
    if selected_state["llm_api_call_count"] > 1:
        return _mark_blocked(report, ["llm_api_call_count_exceeded"])
    if report["llm_call_allowed"] and not report["llm_dispatch_invoked"]:
        return _mark_blocked(report, ["llm_dispatch_not_invoked"])
    if report["llm_call_allowed"] and not report["llm_api_call_attempted"]:
        report["llm_call_allowed"] = False
        report["llm_dispatch_blocked_reason"] = "llm_dispatch_noop"
        return _mark_blocked(report, ["llm_api_call_not_attempted"])
    if not report["llm_response_packet_created"]:
        return _mark_blocked(report, ["llm_api_call_failed" if llm_report.get("api_call_failed") else "llm_response_packet_missing"])
    if report["output_safety_blocked"]:
        return _mark_blocked(report, ["output_safety_blocked"])

    content, _mention_blocked = _send_content(llm_report)
    key = _message_key(content)
    if key in set(selected_state.get("sent_message_keys", [])):
        report["duplicate_send_blocked"] = True
        return _mark_blocked(report, ["duplicate_send_prevented"])

    report["discord_api_send_allowed"] = True
    report["discord_send_stage_reached"] = True
    channel_id = _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "")
    selected_sender = sender or _actual_discord_sender
    send_result = selected_sender(channel_id, content)
    sent = bool(send_result.get("sent"))
    if not sent:
        failure = _discord_send_failure_result(str(send_result.get("error_type") or "discord_send_failed"))
        report["discord_api_send_attempted"] = bool(failure["attempted"])
        report["discord_api_send_called"] = bool(failure["called"])
        report["discord_send_failed"] = True
        report["discord_send_failure_reason"] = str(failure["reason"])
        report["llm_response_available_for_send_retry"] = True
        report["ready_for_phase34l1e_send_retry_without_llm"] = True
        report["partial_success_artifact"] = build_partial_success_artifact(report)
        return _mark_blocked(report, [report["discord_send_failure_reason"]])
    report["discord_api_send_attempted"] = True
    report["discord_api_send_called"] = True
    report["discord_message_sent"] = sent
    report["message_sent_count"] = 1 if sent else 0
    report["sent_channel_scope"] = "private_test_only" if sent else ""
    report["sent_message_review_only"] = bool(sent and "[PRIVATE TEST E2E / REVIEW ONLY]" in content)
    report["self_loop_guard_triggered"] = True
    if sent:
        selected_state.setdefault("sent_message_keys", []).append(key)
        selected_state["message_sent_count"] = int(selected_state.get("message_sent_count", 0)) + 1
        report["duplicate_send_blocked"] = True
        report["ready_for_phase34l2_e2e_live_reply_closeout"] = selected_state["message_sent_count"] == 1
    report["safety_assertions"] = _safety_assertions(report)
    assert_rag_evidence_private_test_e2e_live_reply_safe(report, allow_sent=True, allow_llm_called=True)
    return report


async def _actual_discord_sender_async(channel_id: str, content: str) -> dict[str, Any]:
    import discord

    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        return {"sent": False, "error_type": "discord_token_missing"}
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    result: dict[str, Any] = {"sent": False, "error_type": ""}

    @client.event
    async def on_ready() -> None:
        try:
            channel = client.get_channel(int(channel_id)) or await client.fetch_channel(int(channel_id))
            await channel.send(content)
            result["sent"] = True
        except Exception as exc:
            result["error_type"] = exc.__class__.__name__
        finally:
            await client.close()

    await client.start(token)
    return result


def _actual_discord_sender(channel_id: str, content: str) -> dict[str, Any]:
    return asyncio.run(_actual_discord_sender_async(channel_id, content))


def run_actual_discord_private_test_e2e_live_reply(
    root: str | Path | None = None,
    env: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    import discord

    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        report = _base_report(env, allow_live_reply=True)
        return _mark_blocked(report, ["discord_token_missing"])

    private_channel_id = _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "")
    selected_state = state if state is not None else _default_state()
    result: dict[str, Any] = {}

    async def run_once() -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents)

        @client.event
        async def on_message(message: Any) -> None:
            nonlocal result
            event = {
                "message_id": f"message_redacted_{hashlib.sha256(str(message.id).encode('utf-8')).hexdigest()[:8]}",
                "channel_id": str(message.channel.id),
                "channel_name": str(getattr(message.channel, "name", "private-test")),
                "content": str(getattr(message, "content", "") or ""),
                "author_is_bot": bool(getattr(message.author, "bot", False)),
                "is_self": bool(client.user and message.author.id == client.user.id),
            }
            captured: dict[str, str] = {}

            def capture_sender(_channel_id: str, content: str) -> dict[str, Any]:
                captured["content"] = content
                return {"sent": False, "error_type": "async_send_pending"}

            report = build_rag_evidence_private_test_e2e_live_reply_report(
                root=root,
                allow_live_reply=True,
                env=env,
                event=event,
                sender=capture_sender,
                state=selected_state,
            )
            if report.get("blocked_reasons") == ["async_send_pending"]:
                content = captured.get("content", "")
                try:
                    if str(message.channel.id) != str(private_channel_id):
                        send_result = {"sent": False, "error_type": "private_test_channel_id_mismatch"}
                    elif not content:
                        send_result = {"sent": False, "error_type": "send_content_missing"}
                    else:
                        await message.channel.send(content)
                        send_result = {"sent": True}
                except Exception as exc:
                    send_result = {"sent": False, "error_type": exc.__class__.__name__}
                report["discord_api_send_called"] = bool(send_result.get("sent"))
                report["discord_api_send_attempted"] = bool(send_result.get("sent"))
                report["discord_message_sent"] = bool(send_result.get("sent"))
                report["message_sent_count"] = 1 if send_result.get("sent") else 0
                report["discord_send_stage_reached"] = True
                if not send_result.get("sent"):
                    failure = _discord_send_failure_result(str(send_result.get("error_type") or "discord_send_failed"))
                    report["discord_api_send_attempted"] = bool(failure["attempted"])
                    report["discord_api_send_called"] = bool(failure["called"])
                    report["discord_send_failed"] = True
                    report["discord_send_failure_reason"] = str(failure["reason"])
                    report["llm_response_available_for_send_retry"] = True
                    report["ready_for_phase34l1e_send_retry_without_llm"] = True
                    report["partial_success_artifact"] = build_partial_success_artifact(report)
                report["sent_channel_scope"] = "private_test_only" if send_result.get("sent") else ""
                report["sent_message_review_only"] = bool(send_result.get("sent"))
                report["blocked"] = not bool(send_result.get("sent"))
                report["ready"] = bool(send_result.get("sent"))
                report["blocked_reasons"] = [] if send_result.get("sent") else [str(send_result.get("error_type") or "discord_send_failed")]
                report["ready_for_phase34l2_e2e_live_reply_closeout"] = bool(send_result.get("sent"))
                report["safety_assertions"] = _safety_assertions(report)
            result = report
            await client.close()

        await client.start(token)

    asyncio.run(run_once())
    return result or _mark_blocked(_base_report(env, allow_live_reply=True), ["no_discord_event_received"])


def render_rag_evidence_private_test_e2e_live_reply_markdown(report: dict[str, Any]) -> str:
    manual = report.get("manual_approval", {}) if isinstance(report.get("manual_approval"), dict) else {}
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test E2E Live Reply",
            "",
            f"- Ready: {str(report.get('ready')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Blocked reasons: {', '.join(report.get('blocked_reasons', []))}",
            f"- Manual approval approved: {str(manual.get('approved')).lower()}",
            f"- Approval phrase present: {str(manual.get('approval_phrase_present')).lower()}",
            "- Approval phrase value logged: false",
            f"- Private test channel configured: {str(report.get('private_test_channel_configured')).lower()}",
            "- Private test channel only: true",
            "- Public channel reply allowed: false",
            "- Team channel reply allowed: false",
            f"- OpenRouter API key present: {str(report.get('openrouter_api_key_present')).lower()}",
            "- OpenRouter API key value logged: false",
            f"- Discord live runtime executed: {str(report.get('discord_live_runtime_executed')).lower()}",
            f"- Discord event received: {str(report.get('discord_event_received')).lower()}",
            f"- Accepted private-test channel: {str(report.get('accepted_private_test_channel')).lower()}",
            f"- Prompt safety checked: {str(report.get('prompt_safety_checked')).lower()}",
            f"- Prompt safety allowed: {str(report.get('prompt_safety_allowed')).lower()}",
            f"- Prompt safety blocked: {str(report.get('prompt_safety_blocked')).lower()}",
            f"- LLM stage reached: {str(report.get('llm_stage_reached')).lower()}",
            f"- LLM call allowed: {str(report.get('llm_call_allowed')).lower()}",
            f"- LLM dispatch invoked: {str(report.get('llm_dispatch_invoked')).lower()}",
            f"- LLM dispatch mode: {report.get('llm_dispatch_mode', '')}",
            f"- LLM dispatch blocked reason: {report.get('llm_dispatch_blocked_reason', '')}",
            f"- LLM API call attempted: {str(report.get('llm_api_call_attempted')).lower()}",
            f"- LLM API called: {str(report.get('llm_api_called')).lower()}",
            f"- LLM API call count: {report.get('llm_api_call_count', 0)}",
            f"- LLM response packet created: {str(report.get('llm_response_packet_created')).lower()}",
            f"- Output safety checked: {str(report.get('output_safety_checked')).lower()}",
            f"- Output safety allowed: {str(report.get('output_safety_allowed')).lower()}",
            f"- Output safety blocked: {str(report.get('output_safety_blocked')).lower()}",
            f"- Discord message sent: {str(report.get('discord_message_sent')).lower()}",
            f"- Discord send failed: {str(report.get('discord_send_failed')).lower()}",
            f"- Discord send failure reason: {report.get('discord_send_failure_reason', '')}",
            f"- Message sent count: {report.get('message_sent_count', 0)}",
            f"- Ready for no-LLM send retry: {str(report.get('ready_for_phase34l1e_send_retry_without_llm')).lower()}",
            f"- Ready for Phase 34L-2 closeout: {str(report.get('ready_for_phase34l2_e2e_live_reply_closeout')).lower()}",
            "- Ready for unattended auto reply: false",
            "- Embedding API called: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_evidence_private_test_e2e_live_reply_safe(
    report: dict[str, Any],
    *,
    allow_sent: bool = False,
    allow_llm_called: bool = False,
) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if APPROVAL_PHRASE.lower() in text or LLM_APPROVAL_PHRASE.lower() in text:
        raise ValueError("E2E live reply report contains approval phrase value.")
    if SECRET_RE.search(text):
        raise ValueError("E2E live reply report contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("E2E live reply report contains raw Discord-like IDs.")
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "embedding_api_called", "external_execution", "ready_for_unattended_auto_reply"):
        if report.get(key):
            raise ValueError(f"E2E live reply unsafe flag is true: {key}")
    if report.get("discord_message_sent") and not allow_sent:
        raise ValueError("E2E live reply marked sent without sent allowance.")
    if report.get("llm_api_called") and not allow_llm_called:
        raise ValueError("E2E live reply marked LLM-called without LLM allowance.")
    if int(report.get("message_sent_count", 0) or 0) not in {0, 1}:
        raise ValueError("E2E live reply message_sent_count must be 0 or 1.")
    if int(report.get("llm_api_call_count", 0) or 0) not in {0, 1}:
        raise ValueError("E2E live reply llm_api_call_count must be 0 or 1.")
    if report.get("llm_call_allowed"):
        if report.get("llm_dispatch_blocked_reason"):
            raise ValueError("E2E live reply allowed LLM call with a dispatch blocked reason.")
        if not report.get("llm_dispatch_invoked"):
            raise ValueError("E2E live reply allowed LLM call without invoking dispatch.")
        if not report.get("llm_api_call_attempted"):
            raise ValueError("E2E live reply allowed LLM call without attempting API call.")
        if int(report.get("llm_api_call_count", 0) or 0) == 0:
            raise ValueError("E2E live reply allowed LLM call with zero call count.")
    if not report.get("llm_response_packet_created"):
        if report.get("output_safety_checked") or report.get("output_safety_blocked") or "output_safety_blocked" in report.get("blocked_reasons", []):
            raise ValueError("E2E live reply checked/blocked output safety before an LLM response packet existed.")
    if report.get("openrouter_api_key_value_logged"):
        raise ValueError("E2E live reply logged an OpenRouter API key value.")


def build_legacy_invalid_safety_ordering_report(report: dict[str, Any]) -> dict[str, Any]:
    legacy_invalid = bool(
        "output_safety_blocked" in report.get("blocked_reasons", [])
        and (not report.get("llm_api_called") or not report.get("llm_response_packet_created"))
    )
    return {
        "report_type": "rag_evidence_private_test_e2e_live_reply_legacy_ordering_audit",
        "version": "phase34l1a_safety_stage_ordering_hotfix",
        "legacy_invalid_safety_ordering_detected": legacy_invalid,
        "recommended_next_action": "retry_phase34l1_after_hotfix" if legacy_invalid else "no_legacy_ordering_issue_detected",
        "llm_api_called": bool(report.get("llm_api_called")),
        "llm_response_packet_created": bool(report.get("llm_response_packet_created")),
        "output_safety_checked": bool(report.get("output_safety_checked")),
        "output_safety_blocked": bool(report.get("output_safety_blocked")),
        "discord_message_sent": bool(report.get("discord_message_sent")),
        "message_sent_count": int(report.get("message_sent_count", 0) or 0),
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "discord_message_sent": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }


def build_legacy_llm_allowed_noop_report(report: dict[str, Any]) -> dict[str, Any]:
    legacy_noop = bool(
        report.get("llm_stage_reached")
        and report.get("llm_call_allowed")
        and (
            not report.get("llm_dispatch_invoked")
            or not report.get("llm_api_call_attempted")
            or int(report.get("llm_api_call_count", 0) or 0) == 0
            or "llm_api_call_not_attempted" in report.get("blocked_reasons", [])
        )
    )
    return {
        "report_type": "rag_evidence_private_test_e2e_live_reply_legacy_llm_noop_audit",
        "version": "phase34l1c_llm_dispatch_hotfix",
        "legacy_llm_allowed_noop_detected": legacy_noop,
        "recommended_next_action": "retry_phase34l1_after_llm_dispatch_hotfix" if legacy_noop else "no_legacy_llm_noop_detected",
        "llm_stage_reached": bool(report.get("llm_stage_reached")),
        "llm_call_allowed": bool(report.get("llm_call_allowed")),
        "llm_dispatch_invoked": bool(report.get("llm_dispatch_invoked")),
        "llm_api_call_attempted": bool(report.get("llm_api_call_attempted")),
        "llm_api_call_count": int(report.get("llm_api_call_count", 0) or 0),
        "discord_message_sent": bool(report.get("discord_message_sent")),
        "message_sent_count": int(report.get("message_sent_count", 0) or 0),
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "discord_message_sent": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }


def build_legacy_openrouter_key_detection_failure_report(report: dict[str, Any]) -> dict[str, Any]:
    legacy_failure = bool(
        report.get("llm_stage_reached")
        and not report.get("llm_call_allowed")
        and not report.get("llm_dispatch_invoked")
        and report.get("llm_dispatch_blocked_reason") == "openrouter_api_key_missing"
        and not report.get("llm_api_called")
        and not report.get("discord_message_sent")
    )
    return {
        "report_type": "rag_evidence_private_test_e2e_live_reply_openrouter_key_audit",
        "version": "phase34l1d_openrouter_key_alias_hotfix",
        "legacy_openrouter_key_detection_failure_detected": legacy_failure,
        "recommended_next_action": "retry_phase34l1_after_openrouter_key_alias_hotfix" if legacy_failure else "no_legacy_openrouter_key_issue_detected",
        "openrouter_api_key_present": bool(report.get("openrouter_api_key_present")),
        "openrouter_api_key_value_logged": False,
        "llm_stage_reached": bool(report.get("llm_stage_reached")),
        "llm_call_allowed": bool(report.get("llm_call_allowed")),
        "llm_dispatch_invoked": bool(report.get("llm_dispatch_invoked")),
        "llm_dispatch_blocked_reason": report.get("llm_dispatch_blocked_reason", ""),
        "llm_api_called": bool(report.get("llm_api_called")),
        "discord_message_sent": bool(report.get("discord_message_sent")),
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "discord_message_sent": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }
