"""Phase 34J-1 one-shot private-test Discord send boundary.

The default path is blocked. A live Discord send is only possible when the
explicit CLI allow flag and every manual private-test gate pass. Tests use a
mock sender; this module does not call LLM providers, embeddings, or external
systems.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from typing import Any, Callable

from rag_evidence_private_test_send_preflight import APPROVAL_PHRASE, build_rag_evidence_private_test_send_preflight
from rag_evidence_would_send_preview import build_rag_evidence_would_send_preview


VERSION = "phase34j1_one_private_test_discord_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
Sender = Callable[[str, str], dict[str, Any]]


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _message_from_preview(preview: dict[str, Any]) -> str:
    message = preview.get("would_send_message", {}) if isinstance(preview.get("would_send_message"), dict) else {}
    content = str(message.get("content_preview", "") or "")
    return content.replace("[REVIEW ONLY / NOT SENT]", "[PRIVATE TEST SEND / REVIEW ONLY]", 1)


def _message_key(content: str) -> str:
    return "rag_evidence_send:" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _default_state() -> dict[str, Any]:
    return {"sent_message_keys": [], "message_sent_count": 0}


async def _send_with_discord_py_async(token: str, channel_id: str, content: str) -> dict[str, Any]:
    import discord

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
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        return {"sent": False, "error_type": "discord_token_missing"}
    return asyncio.run(_send_with_discord_py_async(token, channel_id, content))


def build_rag_evidence_private_test_send_report(
    *,
    allow_send: bool = False,
    env: dict[str, Any] | None = None,
    preview: dict[str, Any] | None = None,
    preflight: dict[str, Any] | None = None,
    sender: Sender | None = None,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_preview = preview or build_rag_evidence_would_send_preview()
    selected_preflight = preflight or build_rag_evidence_private_test_send_preflight(selected_preview, env=env)
    selected_state = state if state is not None else _default_state()
    manual = selected_preflight.get("manual_approval", {}) if isinstance(selected_preflight.get("manual_approval"), dict) else {}
    channel_id = _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "")
    reply_mode_private = _env_value(env, "HERMES_DISCORD_REPLY_MODE", "") == "private_test_only"
    send_messages = _flag(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES", "false"))
    private_reply = _flag(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY", "false"))
    message = _message_from_preview(selected_preview)
    key = _message_key(message)

    blocked_reasons: list[str] = []
    if not allow_send:
        blocked_reasons.append("allow_rag_evidence_private_test_discord_send_required")
    if not manual.get("approved"):
        blocked_reasons.append("manual_approval_required")
    if not selected_preview.get("would_send_preview_created"):
        blocked_reasons.append("would_send_preview_required")
    if not selected_preflight.get("would_send_preview_available"):
        blocked_reasons.append("preflight_required")
    if not selected_preview.get("output_safety_allowed"):
        blocked_reasons.append("output_safety_required")
    if not send_messages:
        blocked_reasons.append("discord_send_messages_disabled")
    if not private_reply:
        blocked_reasons.append("discord_private_test_reply_disabled")
    if not reply_mode_private:
        blocked_reasons.append("reply_mode_not_private_test_only")
    if not channel_id:
        blocked_reasons.append("private_test_channel_id_missing")
    if key in set(selected_state.get("sent_message_keys", [])):
        blocked_reasons.append("duplicate_send_prevented")

    ready = not blocked_reasons
    send_result = {"sent": False, "error_type": ""}
    if ready:
        selected_sender = sender or _actual_discord_sender
        send_result = selected_sender(channel_id, message)
        if send_result.get("sent"):
            selected_state.setdefault("sent_message_keys", []).append(key)
            selected_state["message_sent_count"] = int(selected_state.get("message_sent_count", 0)) + 1
        else:
            blocked_reasons.append(str(send_result.get("error_type") or "discord_send_failed"))
            ready = False

    sent = bool(send_result.get("sent"))
    report = {
        "report_type": "rag_evidence_private_test_send",
        "version": VERSION,
        "would_send_preview_available": bool(selected_preview.get("would_send_preview_created")),
        "preflight_available": bool(selected_preflight),
        "manual_approval": {
            "required": True,
            "approved": bool(manual.get("approved")),
            "approval_phrase_present": bool(manual.get("approval_phrase_present")),
            "approval_phrase_exact_match": bool(manual.get("approval_phrase_exact_match")),
            "approval_phrase_value_logged": False,
        },
        "private_test_channel_configured": bool(channel_id) if allow_send else bool(selected_preflight.get("private_test_channel_configured", True)),
        "private_test_channel_only": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "discord_send_messages_enabled": send_messages,
        "discord_private_test_reply_enabled": private_reply,
        "discord_reply_mode_private_test_only": reply_mode_private,
        "ready": bool(ready),
        "blocked": not bool(ready),
        "blocked_reasons": [] if ready else blocked_reasons,
        "discord_api_send_allowed": bool(ready),
        "discord_api_send_called": sent,
        "discord_message_sent": sent,
        "message_sent_count": 1 if sent else 0,
        "sent_channel_scope": "private_test_only" if sent else "",
        "sent_message_review_only": bool(sent and "[PRIVATE TEST SEND / REVIEW ONLY]" in message),
        "self_loop_guard_expected": bool(sent),
        "ready_for_phase34j2_send_closeout": bool(sent and int(selected_state.get("message_sent_count", 0)) == 1),
        "llm_api_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "public_channel_send_called": False,
            "team_channel_send_called": False,
            "discord_message_sent": sent,
            "message_sent_count": 1 if sent else 0,
            "llm_called": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_private_test_send_safe(report, allow_sent=sent)
    return report


def render_rag_evidence_private_test_send_markdown(report: dict[str, Any]) -> str:
    manual = report.get("manual_approval", {}) if isinstance(report.get("manual_approval"), dict) else {}
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test Send",
            "",
            f"- Ready: {str(report.get('ready')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Blocked reasons: {', '.join(report.get('blocked_reasons', []))}",
            f"- Manual approval approved: {str(manual.get('approved')).lower()}",
            f"- Approval phrase present: {str(manual.get('approval_phrase_present')).lower()}",
            "- Approval phrase value logged: false",
            f"- Private test channel configured: {str(report.get('private_test_channel_configured')).lower()}",
            "- Private test channel only: true",
            "- Public channel send allowed: false",
            "- Team channel send allowed: false",
            f"- Discord API send called: {str(report.get('discord_api_send_called')).lower()}",
            f"- Discord message sent: {str(report.get('discord_message_sent')).lower()}",
            f"- Message sent count: {report.get('message_sent_count', 0)}",
            f"- Self-loop guard expected: {str(report.get('self_loop_guard_expected')).lower()}",
            f"- Ready for Phase 34J-2 send closeout: {str(report.get('ready_for_phase34j2_send_closeout')).lower()}",
            "- LLM API called: false",
            "- Embedding API called: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_evidence_private_test_send_safe(report: dict[str, Any], *, allow_sent: bool = False) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if APPROVAL_PHRASE.lower() in text:
        raise ValueError("RAG evidence private-test send report contains approval phrase value.")
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence private-test send report contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence private-test send report contains raw Discord-like IDs.")
    for key in ("public_channel_send_allowed", "team_channel_send_allowed", "llm_api_called", "embedding_api_called", "external_execution"):
        if report.get(key):
            raise ValueError(f"RAG evidence private-test send unsafe flag is true: {key}")
    if report.get("discord_message_sent") and not allow_sent:
        raise ValueError("RAG evidence private-test send marked sent without explicit sent allowance.")
    if report.get("message_sent_count") not in {0, 1}:
        raise ValueError("RAG evidence private-test send count must be 0 or 1.")
