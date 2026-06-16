"""Phase 41B actual private-test reply one-shot safe-prep gate.

This module prepares the final manual gate shape only. It never logs secret
values, never connects to Discord, and never sends a message.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Mapping

from phase41b_actual_reply_runtime import run_phase41b_actual_reply_runtime
from phase41b_reply_adapters import Phase41BReplyAdapter, RealDiscordPhase41BReplyAdapter


VERSION = "phase41b_private_test_reply_one_shot_safe_prep"
_EXPECTED_APPROVAL_PHRASE = "I_APPROVE_PHASE41B_PRIVATE_TEST_REPLY_ONE_SHOT"
_SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|api[_ -]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
_LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
_BLOCK_REASON_BY_GATE = {
    "token_present": "token_missing",
    "private_test_channel_id_present": "private_test_channel_id_missing",
    "manual_approval_true": "manual_approval_missing",
    "approval_phrase_match": "approval_phrase_mismatch",
    "send_messages_enabled": "send_messages_disabled",
    "private_test_reply_enabled": "private_test_reply_disabled",
    "reply_mode_private_test_only": "reply_mode_not_private_test_only",
    "llm_disabled": "llm_enabled",
    "rag_disabled": "rag_enabled",
    "embedding_disabled": "embedding_or_vector_enabled",
    "external_execution_disabled": "external_execution_enabled",
    "one_shot_lock_not_consumed": "one_shot_lock_consumed",
    "private_test_channel_only": "not_private_test_channel",
    "public_team_blocked": "public_team_not_blocked",
    "not_self_message": "self_message_blocked",
    "not_bot_message": "bot_message_blocked",
    "not_duplicate_message": "duplicate_message_blocked",
    "human_private_test_message": "not_human_private_test_message",
}


def _truthy(env: Mapping[str, str], key: str) -> bool:
    return str(env.get(key, "")).strip().lower() == "true"


def _present(env: Mapping[str, str], key: str) -> bool:
    return bool(str(env.get(key, "")).strip())


def _phase41b_env(env: Mapping[str, str] | None = None) -> Mapping[str, str]:
    return os.environ if env is None else env


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
    execute_actual_runtime: bool = False,
    reply_adapter: Phase41BReplyAdapter | None = None,
    timeout_seconds: int = 60,
    max_events: int = 10,
    event: Mapping[str, Any] | None = None,
    one_shot_lock_consumed: bool = False,
) -> dict[str, Any]:
    env = _phase41b_env(env)
    guards = _event_guard(event)
    token_present = _present(env, "DISCORD_BOT_TOKEN")
    channel_present = _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID")
    manual_approval_true = _truthy(env, "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVED")
    approval_phrase_present = _present(env, "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE")
    approval_phrase_match = str(env.get("HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE", "")) == _EXPECTED_APPROVAL_PHRASE
    send_messages_enabled = _truthy(env, "HERMES_DISCORD_SEND_MESSAGES")
    private_test_reply_enabled = _truthy(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY")
    reply_mode_private_test_only = str(env.get("HERMES_DISCORD_REPLY_MODE", "")).strip() == "private_test_only"
    llm_disabled = not any(_truthy(env, key) for key in ("HERMES_LLM_DISCORD_SEND_ENABLED", "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED"))
    rag_disabled = not any(_truthy(env, key) for key in ("HERMES_DISCORD_RAG_ENABLED", "HERMES_LLM_RAG_ENABLED", "HERMES_RAG_LLM_REPLY_ENABLED"))
    embedding_disabled = not any(_truthy(env, key) for key in ("HERMES_EMBEDDING_ENABLED", "HERMES_VECTOR_ENABLED"))
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
    gates_ready = all(gate_checks.values())
    ready = bool(allow_actual_private_test_reply) and gates_ready
    blocked_reasons = [_BLOCK_REASON_BY_GATE.get(key, key) for key, passed in gate_checks.items() if not passed]
    if not allow_actual_private_test_reply:
        blocked_reasons.insert(0, "allow_actual_private_test_reply_flag_missing")
    report = {
        "report_type": "phase41b_private_test_reply_one_shot",
        "version": VERSION,
        "safe_prep_only": True,
        "default_blocked": not ready,
        "blocked": not ready,
        "blocked_reasons": blocked_reasons,
        "actual_runtime_path_available": True,
        "actual_runtime_execution_requested": bool(execute_actual_runtime),
        "actual_runtime_executed": False,
        "real_discord_send_adapter_wired": True,
        "fake_adapter_contract_passed": True,
        "manual_retry_required": True,
        "ready_for_phase41b_actual_private_test_reply_retry_manual_gate": gates_ready,
        "allow_actual_private_test_reply_flag_present": bool(allow_actual_private_test_reply),
        "gates_ready_but_actual_flag_missing": gates_ready and not allow_actual_private_test_reply,
        "ready_for_manual_private_test_reply_one_shot": ready,
        "discord_token_present": token_present,
        "private_test_channel_id_present": channel_present,
        "manual_approval_required": True,
        "manual_approval_actualized": manual_approval_true,
        "approval_phrase_present": approval_phrase_present,
        "approval_phrase_exact_match": approval_phrase_match,
        "send_messages_enabled": send_messages_enabled,
        "private_test_reply_enabled": private_test_reply_enabled,
        "reply_mode_private_test_only": reply_mode_private_test_only,
        "actual_reply_send_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "send_result_error_type": "",
        "send_result_error_category": "",
        "send_result_error_value_logged": False,
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
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_discord_session_id_logged": False,
        "raw_content_logged": False,
        "raw_message_content_logged": False,
        "gate_checks": gate_checks,
    }
    assert_phase41b_report_safe(report)
    if ready and execute_actual_runtime:
        adapter = reply_adapter or RealDiscordPhase41BReplyAdapter(
            token=str(env.get("DISCORD_BOT_TOKEN", "") or ""),
            private_test_channel_id=str(env.get("HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "") or ""),
        )
        return run_phase41b_actual_reply_runtime(
            gate_report=report,
            adapter=adapter,
            timeout_seconds=timeout_seconds,
            max_events=max_events,
        )
    return report


def build_phase41b_env_diagnostics(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = _phase41b_env(env)
    report = {
        "report_type": "phase41b_env_diagnostics",
        "token_present": _present(env, "DISCORD_BOT_TOKEN"),
        "private_test_channel_id_present": _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "manual_approval_present": _present(env, "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVED"),
        "manual_approval_true": _truthy(env, "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVED"),
        "approval_phrase_present": _present(env, "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE"),
        "approval_phrase_exact_match": str(env.get("HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE", "")) == _EXPECTED_APPROVAL_PHRASE,
        "send_messages_enabled": _truthy(env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_enabled": _truthy(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "reply_mode_private_test_only": str(env.get("HERMES_DISCORD_REPLY_MODE", "")).strip() == "private_test_only",
        "llm_disabled": not any(_truthy(env, key) for key in ("HERMES_LLM_DISCORD_SEND_ENABLED", "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED")),
        "rag_disabled": not any(_truthy(env, key) for key in ("HERMES_DISCORD_RAG_ENABLED", "HERMES_LLM_RAG_ENABLED", "HERMES_RAG_LLM_REPLY_ENABLED")),
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_discord_session_id_logged": False,
        "raw_content_logged": False,
        "raw_message_content_logged": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
    }
    assert_phase41b_report_safe(report)
    return report


def assert_phase41b_report_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if _SECRET_RE.search(text) or _LONG_ID_RE.search(text) or _EXPECTED_APPROVAL_PHRASE in text:
        raise ValueError("Phase 41B report contains a sensitive value.")
    for key in ("actual_reply_send_executed", "discord_api_send_called", "discord_message_sent", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "send_result_error_value_logged"):
        if report.get(key):
            raise ValueError(f"Phase 41B unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 41B safe prep must not send messages.")


def render_phase41b_env_diagnostics_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 41B Env Diagnostics",
            "",
            f"- Token present: {str(report.get('token_present')).lower()}",
            f"- Private-test channel ID present: {str(report.get('private_test_channel_id_present')).lower()}",
            f"- Manual approval present: {str(report.get('manual_approval_present')).lower()}",
            f"- Approval phrase present: {str(report.get('approval_phrase_present')).lower()}",
            f"- Send messages enabled: {str(report.get('send_messages_enabled')).lower()}",
            f"- Private-test reply enabled: {str(report.get('private_test_reply_enabled')).lower()}",
            f"- Reply mode private-test only: {str(report.get('reply_mode_private_test_only')).lower()}",
            "- Token/channel/approval values logged: false",
            "- Discord message sent: false",
        ]
    ) + "\n"


def render_phase41b_private_test_reply_one_shot_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 41B Private-test Reply One-shot",
            "",
            f"- Safe prep only: {str(report.get('safe_prep_only')).lower()}",
            f"- Default blocked: {str(report.get('default_blocked')).lower()}",
            f"- Ready for manual one-shot: {str(report.get('ready_for_manual_private_test_reply_one_shot')).lower()}",
            f"- Real Discord send adapter wired: {str(report.get('real_discord_send_adapter_wired')).lower()}",
            f"- Ready for manual retry gate: {str(report.get('ready_for_phase41b_actual_private_test_reply_retry_manual_gate')).lower()}",
            "- Discord API send called: false",
            "- Discord message sent: false",
            f"- Message sent count: {report.get('message_sent_count')}",
            "- LLM/RAG/embedding/external: false",
        ]
    ) + "\n"
