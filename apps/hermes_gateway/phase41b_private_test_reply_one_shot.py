"""Phase 41B actual private-test reply one-shot safe-prep gate.

This module prepares the final manual gate shape only. It never logs secret
values, never connects to Discord, and never sends a message.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase41b_private_test_reply_one_shot_safe_prep"
_EXPECTED_APPROVAL_PHRASE = "I_APPROVE_PHASE41B_PRIVATE_TEST_REPLY_ONE_SHOT"
_SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|api[_ -]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
_LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def _truthy(env: Mapping[str, str], key: str) -> bool:
    return str(env.get(key, "")).strip().lower() == "true"


def _present(env: Mapping[str, str], key: str) -> bool:
    return bool(str(env.get(key, "")).strip())


def _event_guard(event: Mapping[str, Any] | None) -> dict[str, bool]:
    event = event or {}
    channel_scope = str(event.get("channel_scope", "private_test")).strip() or "private_test"
    author_type = str(event.get("author_type", "human")).strip() or "human"
    duplicate = bool(event.get("duplicate"))
    return {
        "private_test_channel_only": channel_scope == "private_test",
        "public_team_blocked": channel_scope not in {"public", "team"},
        "not_self_message": author_type != "self",
        "not_bot_message": author_type != "bot",
        "not_duplicate_message": not duplicate,
        "self_message_ignored": author_type == "self",
        "bot_message_ignored": author_type == "bot",
        "duplicate_message_ignored": duplicate,
        "human_private_test_message": channel_scope == "private_test" and author_type == "human" and not duplicate,
    }


def build_phase41b_private_test_reply_one_shot(
    env: Mapping[str, str] | None = None,
    *,
    allow_actual_private_test_reply: bool = False,
    event: Mapping[str, Any] | None = None,
    one_shot_lock_consumed: bool = False,
) -> dict[str, Any]:
    env = env or {}
    guards = _event_guard(event)
    token_present = _present(env, "DISCORD_BOT_TOKEN")
    channel_present = _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID")
    manual_approval_true = _truthy(env, "HERMES_PHASE41B_MANUAL_APPROVAL")
    approval_phrase_match = str(env.get("HERMES_PHASE41B_APPROVAL_PHRASE", "")) == _EXPECTED_APPROVAL_PHRASE
    send_messages_enabled = _truthy(env, "HERMES_DISCORD_SEND_MESSAGES")
    private_test_reply_enabled = _truthy(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY")
    reply_mode_private_test_only = str(env.get("HERMES_DISCORD_REPLY_MODE", "")).strip() == "private_test_only"
    llm_disabled = not _truthy(env, "HERMES_DISCORD_LLM_ENABLED") and not _truthy(env, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED")
    rag_disabled = not _truthy(env, "HERMES_DISCORD_RAG_ENABLED") and not _truthy(env, "HERMES_LLM_RAG_ENABLED")
    embedding_disabled = not _truthy(env, "HERMES_EMBEDDING_ENABLED") and not _truthy(env, "HERMES_VECTOR_ENABLED")
    external_disabled = not _truthy(env, "HERMES_DISCORD_EXTERNAL_EXECUTION")
    gate_checks = {
        "token_present": token_present,
        "private_test_channel_id_present": channel_present,
        "manual_approval_true": manual_approval_true,
        "approval_phrase_match": approval_phrase_match,
        "send_messages_enabled": send_messages_enabled,
        "private_test_reply_enabled": private_test_reply_enabled,
        "reply_mode_private_test_only": reply_mode_private_test_only,
        "llm_disabled": llm_disabled,
        "rag_disabled": rag_disabled,
        "embedding_disabled": embedding_disabled,
        "external_execution_disabled": external_disabled,
        "one_shot_lock_not_consumed": not one_shot_lock_consumed,
        "private_test_channel_only": guards["private_test_channel_only"],
        "public_team_blocked": guards["public_team_blocked"],
        "not_self_message": guards["not_self_message"],
        "not_bot_message": guards["not_bot_message"],
        "not_duplicate_message": guards["not_duplicate_message"],
        "human_private_test_message": guards["human_private_test_message"],
    }
    ready = bool(allow_actual_private_test_reply) and all(gate_checks.values())
    blocked_reasons = [key for key, passed in gate_checks.items() if not passed]
    if not allow_actual_private_test_reply:
        blocked_reasons.insert(0, "allow_actual_private_test_reply_flag_missing")
    report = {
        "report_type": "phase41b_private_test_reply_one_shot",
        "version": VERSION,
        "safe_prep_only": True,
        "default_blocked": not ready,
        "blocked": not ready,
        "blocked_reasons": blocked_reasons,
        "allow_actual_private_test_reply_flag_present": bool(allow_actual_private_test_reply),
        "ready_for_manual_private_test_reply_one_shot": ready,
        "actual_reply_send_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "public_team_blocked": guards["public_team_blocked"],
        "self_message_ignored": guards["self_message_ignored"],
        "bot_message_ignored": guards["bot_message_ignored"],
        "duplicate_message_ignored": guards["duplicate_message_ignored"],
        "one_shot_lock_consumed": bool(one_shot_lock_consumed),
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_message_content_logged": False,
        "gate_checks": gate_checks,
    }
    assert_phase41b_report_safe(report)
    return report


def assert_phase41b_report_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if _SECRET_RE.search(text) or _LONG_ID_RE.search(text) or _EXPECTED_APPROVAL_PHRASE in text:
        raise ValueError("Phase 41B report contains a sensitive value.")
    for key in ("actual_reply_send_executed", "discord_api_send_called", "discord_message_sent", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        if report.get(key):
            raise ValueError(f"Phase 41B unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 41B safe prep must not send messages.")


def render_phase41b_private_test_reply_one_shot_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 41B Private-test Reply One-shot",
            "",
            f"- Safe prep only: {str(report.get('safe_prep_only')).lower()}",
            f"- Default blocked: {str(report.get('default_blocked')).lower()}",
            f"- Ready for manual one-shot: {str(report.get('ready_for_manual_private_test_reply_one_shot')).lower()}",
            "- Discord API send called: false",
            "- Discord message sent: false",
            f"- Message sent count: {report.get('message_sent_count')}",
            "- LLM/RAG/embedding/external: false",
        ]
    ) + "\n"
