"""Phase 42 supervised deterministic private-test session preflight."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase42_supervised_private_test_session_preflight"
EXPECTED_APPROVAL_PHRASE = "I_APPROVE_PHASE42_SUPERVISED_PRIVATE_TEST_SESSION"
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|api[_ -]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _truthy(env: Mapping[str, str], key: str) -> bool:
    return str(env.get(key, "")).strip().lower() == "true"


def _positive_int(env: Mapping[str, str], key: str) -> int:
    try:
        return max(0, int(str(env.get(key, "0") or "0")))
    except ValueError:
        return 0


def build_phase42_supervised_private_test_session_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = env or {}
    max_session_messages = _positive_int(env, "HERMES_PHASE42_MAX_SESSION_MESSAGES")
    max_reply_count = _positive_int(env, "HERMES_PHASE42_MAX_REPLY_COUNT")
    max_send_count = _positive_int(env, "HERMES_PHASE42_MAX_SEND_COUNT")
    timeout_seconds = _positive_int(env, "HERMES_PHASE42_TIMEOUT_SECONDS")
    cooldown_seconds = _positive_int(env, "HERMES_PHASE42_COOLDOWN_SECONDS")
    reply_mode_private_test_only = str(env.get("HERMES_DISCORD_REPLY_MODE", "")) == "private_test_only"
    manual_approval_present = bool(str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVED", "")).strip())
    manual_approval_true = _truthy(env, "HERMES_PHASE42_SUPERVISED_SESSION_APPROVED")
    approval_phrase_present = bool(str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE", "")).strip())
    approval_phrase_match = str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE", "")) == EXPECTED_APPROVAL_PHRASE
    deterministic_reply_only = _truthy(env, "HERMES_PHASE42_DETERMINISTIC_REPLY_ONLY")
    frozen_reply_only = _truthy(env, "HERMES_PHASE42_FROZEN_REPLY_ONLY")
    llm_disabled = not any(_truthy(env, key) for key in ("HERMES_DISCORD_LLM_ENABLED", "HERMES_LLM_DISCORD_SEND_ENABLED", "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED"))
    rag_disabled = not any(_truthy(env, key) for key in ("HERMES_DISCORD_RAG_ENABLED", "HERMES_LLM_RAG_ENABLED", "HERMES_RAG_LLM_REPLY_ENABLED"))
    embedding_disabled = not any(_truthy(env, key) for key in ("HERMES_EMBEDDING_ENABLED", "HERMES_VECTOR_ENABLED"))
    external_disabled = not _truthy(env, "HERMES_DISCORD_EXTERNAL_EXECUTION")
    checks = {
        "manual_approval_required": manual_approval_true,
        "approval_phrase_required": approval_phrase_match,
        "max_session_messages_required": max_session_messages > 0,
        "max_reply_count_required": max_reply_count > 0,
        "max_send_count_required": max_send_count > 0,
        "timeout_required": timeout_seconds > 0,
        "cooldown_required": cooldown_seconds > 0,
        "reply_mode_private_test_only": reply_mode_private_test_only,
        "deterministic_reply_only": deterministic_reply_only,
        "frozen_reply_only": frozen_reply_only,
        "llm_disabled": llm_disabled,
        "rag_disabled": rag_disabled,
        "embedding_disabled": embedding_disabled,
        "external_execution_disabled": external_disabled,
    }
    gates_ready = all(checks.values())
    report = {
        "report_type": "phase42_supervised_private_test_session_preflight",
        "version": VERSION,
        "supervised_session_preflight_only": True,
        "default_blocked": True,
        "blocked": True,
        "blocked_reasons": [key for key, value in checks.items() if not value],
        "manual_gate_required": True,
        "manual_gate_open": False,
        "manual_approval_required": True,
        "manual_approval_present": manual_approval_present,
        "manual_approval_true": manual_approval_true,
        "approval_phrase_required": True,
        "approval_phrase_present": approval_phrase_present,
        "approval_phrase_exact_match": approval_phrase_match,
        "gate_checks_ready": gates_ready,
        "actual_supervised_session_executed": False,
        "actual_runtime_executed": False,
        "max_reply_count": max_reply_count,
        "max_session_messages": max_session_messages,
        "max_send_count": max_send_count,
        "timeout_seconds": timeout_seconds,
        "cooldown_seconds": cooldown_seconds,
        "private_test_only": True,
        "reply_mode_private_test_only": reply_mode_private_test_only,
        "private_test_channel_only": True,
        "public_team_blocked": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "deterministic_reply_only": deterministic_reply_only,
        "frozen_reply_only": frozen_reply_only,
        "self_message_ignored": True,
        "bot_message_ignored": True,
        "duplicate_message_ignored": True,
        "session_lock_required": True,
        "session_lock_active": True,
        "no_repeat_uncontrolled_session": True,
        "timeout_no_message_safe_closeout": True,
        "ready_for_phase42_manual_supervised_session": False,
        "ready_for_phase41b_repeat_send": False,
        "ready_for_repeat_send": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "llm_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_discord_session_id_logged": False,
        "raw_content_logged": False,
        "raw_message_content_logged": False,
        "ready_for_supervised_session": False,
    }
    assert_phase42_preflight_safe(report)
    return report


def assert_phase42_preflight_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 42 preflight contains sensitive values.")
    for key in (
        "manual_gate_open",
        "actual_supervised_session_executed",
        "actual_runtime_executed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "ready_for_phase42_manual_supervised_session",
        "ready_for_phase41b_repeat_send",
        "ready_for_repeat_send",
        "llm_api_call_attempted",
        "llm_api_called",
        "llm_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "discord_api_send_called",
        "discord_message_sent",
        "token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_discord_session_id_logged",
        "raw_content_logged",
        "raw_message_content_logged",
        "ready_for_supervised_session",
    ):
        if report.get(key):
            raise ValueError(f"Phase 42 preflight unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 42 preflight must not send messages.")


def render_phase42_supervised_private_test_session_preflight_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 42 Supervised Private-test Session",
            "",
            "- Preflight only: true",
            f"- Default blocked: {str(report.get('default_blocked')).lower()}",
            f"- Max reply count: {report.get('max_reply_count')}",
            f"- Timeout seconds: {report.get('timeout_seconds')}",
            f"- Cooldown seconds: {report.get('cooldown_seconds')}",
            f"- Manual gate open: {str(report.get('manual_gate_open')).lower()}",
            "- Actual runtime executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
