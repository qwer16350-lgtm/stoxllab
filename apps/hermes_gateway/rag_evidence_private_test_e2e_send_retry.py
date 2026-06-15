"""Phase 34L-1E no-LLM retry report for E2E Discord send disconnects.

This module prepares and tests a manual private-test send retry from a prior
partial-success artifact. The default path is blocked and does not call
Discord, LLM providers, embeddings, or external systems.
"""

from __future__ import annotations

import json
import os
import re
import asyncio
from typing import Any, Callable


VERSION = "phase34l1e_send_retry_without_llm"
APPROVAL_PHRASE = "I_APPROVE_ONE_PRIVATE_TEST_E2E_SEND_RETRY_WITHOUT_LLM"
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


def _token_present(env: dict[str, Any] | None = None) -> bool:
    source = os.environ if env is None else env
    return bool(source.get("DISCORD_BOT_TOKEN"))


def build_sample_partial_success_artifact() -> dict[str, Any]:
    return {
        "report_type": "rag_evidence_private_test_e2e_partial_success",
        "version": "phase34l1e_llm_success_send_failed_no_retry_yet",
        "llm_api_called": True,
        "llm_api_call_count": 1,
        "llm_response_packet_created": True,
        "output_safety_checked": True,
        "output_safety_allowed": True,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "send_retry_allowed_without_llm": True,
        "send_retry_requires_manual_approval": True,
        "ready_for_manual_send_retry_without_llm": True,
        "ready_for_phase34l2_e2e_live_reply_closeout": False,
    }


def _manual_approval(env: dict[str, Any] | None = None) -> dict[str, Any]:
    phrase = _env_value(env, "HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVAL_PHRASE", "")
    approved_flag = _flag(_env_value(env, "HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVED", "false"))
    exact = phrase == APPROVAL_PHRASE
    return {
        "required": True,
        "approved": bool(approved_flag and exact),
        "approval_flag_true": bool(approved_flag),
        "approval_phrase_present": bool(phrase),
        "approval_phrase_exact_match": bool(exact),
        "approval_phrase_value_logged": False,
    }


def _partial_success_ready(partial_success: dict[str, Any]) -> bool:
    return bool(
        partial_success.get("ready_for_manual_send_retry_without_llm")
        and partial_success.get("llm_api_called")
        and int(partial_success.get("llm_api_call_count", 0) or 0) == 1
        and partial_success.get("llm_response_packet_created")
        and partial_success.get("output_safety_allowed")
        and not partial_success.get("discord_message_sent")
    )


def _blocked_reasons(
    *,
    allow_send_retry: bool,
    env: dict[str, Any] | None,
    partial_success: dict[str, Any],
    manual: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if not partial_success:
        reasons.append("partial_success_artifact_required")
    elif not _partial_success_ready(partial_success):
        reasons.append("partial_success_not_ready_for_retry")
    if not allow_send_retry:
        reasons.append("allow_rag_evidence_private_test_e2e_send_retry_required")
    if not manual.get("approved"):
        reasons.append("manual_approval_required")
    if not _flag(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES", "false")):
        reasons.append("discord_send_messages_disabled")
    if not _flag(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY", "false")):
        reasons.append("discord_private_test_reply_disabled")
    if _env_value(env, "HERMES_DISCORD_REPLY_MODE", "") != "private_test_only":
        reasons.append("reply_mode_not_private_test_only")
    if not _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", ""):
        reasons.append("private_test_channel_id_missing")
    return reasons


def _safe_retry_content() -> str:
    return (
        "[PRIVATE TEST E2E RETRY / REVIEW ONLY]\n\n"
        "This retry uses an already safety-checked LLM response packet. "
        "No LLM recall is allowed. No external action has been taken."
    )


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
    return _actual_discord_sender_with_token(token, channel_id, content)


def _actual_discord_sender_with_token(token: str, channel_id: str, content: str) -> dict[str, Any]:
    if not token:
        return {"sent": False, "error_type": "discord_token_missing"}
    return asyncio.run(_send_with_discord_py_async(token, channel_id, content))


def build_rag_evidence_private_test_e2e_send_retry_report(
    *,
    allow_send_retry: bool = False,
    env: dict[str, Any] | None = None,
    partial_success: dict[str, Any] | None = None,
    sender: Sender | None = None,
) -> dict[str, Any]:
    selected_partial = build_sample_partial_success_artifact() if partial_success is None else partial_success
    manual = _manual_approval(env)
    channel_id = _env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "")
    token_present = _token_present(env)
    reasons = _blocked_reasons(
        allow_send_retry=allow_send_retry,
        env=env,
        partial_success=selected_partial,
        manual=manual,
    )
    if not reasons and sender is None and not token_present:
        reasons.append("discord_token_missing")
    ready_for_actual_send_retry = not reasons
    send_result = {"sent": False, "error_type": ""}
    actual_sender_available = bool(sender is not None or (ready_for_actual_send_retry and token_present))
    actual_sender_not_provided = False
    if ready_for_actual_send_retry:
        selected_sender = sender or (lambda selected_channel_id, content: _actual_discord_sender_with_token(_env_value(env, "DISCORD_BOT_TOKEN", ""), selected_channel_id, content))
        send_result = selected_sender(channel_id, _safe_retry_content())
        if not send_result.get("sent"):
            reasons.append(str(send_result.get("error_type") or "discord_send_failed"))
            ready_for_actual_send_retry = False

    sent = bool(send_result.get("sent"))
    report = {
        "report_type": "rag_evidence_private_test_e2e_send_retry",
        "version": VERSION,
        "partial_success_available": bool(selected_partial),
        "llm_recall_allowed": False,
        "llm_api_called": False,
        "llm_api_call_count": 0,
        "output_safety_already_passed": bool(selected_partial.get("output_safety_allowed")),
        "manual_approval_required": True,
        "manual_approval": manual,
        "manual_approval_approved": bool(manual.get("approved")),
        "private_test_channel_only": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "discord_token_present": token_present,
        "discord_token_value_logged": False,
        "actual_send_retry_sender_available": actual_sender_available,
        "actual_send_retry_sender_not_provided": actual_sender_not_provided,
        "ready_for_actual_send_retry": bool(ready_for_actual_send_retry),
        "blocked": not bool(ready_for_actual_send_retry),
        "blocked_reasons": [] if ready_for_actual_send_retry else reasons,
        "discord_api_send_allowed": bool(ready_for_actual_send_retry),
        "discord_api_send_called": bool(sent),
        "discord_message_sent": bool(sent),
        "message_sent_count": 1 if sent else 0,
        "sent_channel_scope": "private_test_only" if sent else "",
        "ready_for_manual_send_retry_without_llm": bool(_partial_success_ready(selected_partial)),
        "ready_for_phase34l2_e2e_live_reply_closeout": bool(sent),
        "embedding_api_called": False,
        "external_execution": False,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "llm_call_count": 0,
            "public_channel_send_called": False,
            "team_channel_send_called": False,
            "discord_message_sent_count": 1 if sent else 0,
            "embedding_called": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_private_test_e2e_send_retry_safe(report, allow_sent=sent)
    return report


def render_rag_evidence_private_test_e2e_send_retry_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test E2E Send Retry",
            "",
            f"- Partial success available: {str(report.get('partial_success_available')).lower()}",
            "- LLM recall allowed: false",
            f"- LLM API called: {str(report.get('llm_api_called')).lower()}",
            f"- LLM API call count: {report.get('llm_api_call_count', 0)}",
            f"- Output safety already passed: {str(report.get('output_safety_already_passed')).lower()}",
            "- Manual approval required: true",
            f"- Manual approval approved: {str(report.get('manual_approval_approved')).lower()}",
            "- Private test channel only: true",
            "- Public channel send allowed: false",
            "- Team channel send allowed: false",
            f"- Actual send retry sender available: {str(report.get('actual_send_retry_sender_available')).lower()}",
            f"- Actual send retry sender not provided: {str(report.get('actual_send_retry_sender_not_provided')).lower()}",
            f"- Ready for actual send retry: {str(report.get('ready_for_actual_send_retry')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Blocked reasons: {', '.join(report.get('blocked_reasons', []))}",
            f"- Discord API send called: {str(report.get('discord_api_send_called')).lower()}",
            f"- Discord message sent: {str(report.get('discord_message_sent')).lower()}",
            f"- Message sent count: {report.get('message_sent_count', 0)}",
            f"- Ready for Phase 34L-2 closeout: {str(report.get('ready_for_phase34l2_e2e_live_reply_closeout')).lower()}",
            "- Embedding API called: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_evidence_private_test_e2e_send_retry_safe(report: dict[str, Any], *, allow_sent: bool = False) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if APPROVAL_PHRASE.lower() in text:
        raise ValueError("Send retry report contains approval phrase value.")
    if SECRET_RE.search(text):
        raise ValueError("Send retry report contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Send retry report contains raw Discord-like IDs.")
    if report.get("llm_api_called") or int(report.get("llm_api_call_count", 0) or 0) != 0:
        raise ValueError("Send retry must not call or recall LLM.")
    for key in ("public_channel_send_allowed", "team_channel_send_allowed", "embedding_api_called", "external_execution", "ready_for_unattended_auto_reply"):
        if report.get(key):
            raise ValueError(f"Send retry unsafe flag is true: {key}")
    if report.get("discord_token_value_logged") or report.get("actual_send_retry_sender_not_provided"):
        raise ValueError("Send retry report contains unsafe sender/token state.")
    if report.get("discord_message_sent") and not allow_sent:
        raise ValueError("Send retry marked sent without sent allowance.")
    if int(report.get("message_sent_count", 0) or 0) not in {0, 1}:
        raise ValueError("Send retry message_sent_count must be 0 or 1.")
