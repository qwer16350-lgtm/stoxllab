"""Phase 40Y / Phase 41 actual private-test reply preflight gate.

The gate is report-only and never sends a Discord message.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase40y_phase41_reply_preflight_gate"
EXPECTED_APPROVAL_PHRASE = "I_APPROVE_PHASE41_PRIVATE_TEST_REPLY"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _value(env: Mapping[str, str] | None, key: str) -> str:
    return str((env or {}).get(key, "") or "")


def _present(env: Mapping[str, str] | None, key: str) -> bool:
    return bool(_value(env, key).strip())


def _flag(env: Mapping[str, str] | None, key: str) -> bool:
    return _value(env, key).strip().lower() in {"1", "true", "yes", "on"}


def _false_flag(env: Mapping[str, str] | None, key: str) -> bool:
    return not _flag(env, key)


def _conditions(env: Mapping[str, str] | None, event: Mapping[str, Any] | None, one_shot_lock_consumed: bool) -> dict[str, bool]:
    event = event or {}
    return {
        "token_present": _present(env, "DISCORD_BOT_TOKEN"),
        "private_test_channel_id_present": _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "manual_approval_true": _flag(env, "HERMES_PHASE41_PRIVATE_TEST_REPLY_APPROVED"),
        "approval_phrase_exact_match": _value(env, "HERMES_PHASE41_PRIVATE_TEST_REPLY_APPROVAL_PHRASE") == EXPECTED_APPROVAL_PHRASE,
        "send_messages_enabled": _flag(env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_enabled": _flag(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "reply_mode_private_test_only": _value(env, "HERMES_DISCORD_REPLY_MODE") == "private_test_only",
        "public_team_blocked": event.get("channel_scope", "private_test_only") == "private_test_only",
        "not_self": not bool(event.get("is_self")),
        "not_bot": not bool(event.get("is_bot")) and event.get("author_type", "human") != "bot",
        "not_duplicate": not bool(event.get("is_duplicate")),
        "llm_disabled": _false_flag(env, "HERMES_LLM_DISCORD_SEND_ENABLED") and _false_flag(env, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED"),
        "rag_disabled": _false_flag(env, "HERMES_DISCORD_RAG_ENABLED") and _false_flag(env, "HERMES_LLM_RAG_ENABLED") and _false_flag(env, "HERMES_RAG_LLM_REPLY_ENABLED"),
        "embedding_disabled": _false_flag(env, "HERMES_EMBEDDING_API_ENABLED") and _false_flag(env, "HERMES_VECTOR_INDEX_ENABLED"),
        "external_disabled": _false_flag(env, "HERMES_DISCORD_EXTERNAL_EXECUTION"),
        "one_shot_session_lock_available": not one_shot_lock_consumed,
    }


def _block_reason(conditions: Mapping[str, bool]) -> str:
    checks = (
        ("approval_missing", conditions["manual_approval_true"]),
        ("approval_phrase_mismatch", conditions["approval_phrase_exact_match"]),
        ("token_missing_before_login", conditions["token_present"]),
        ("channel_missing_before_login", conditions["private_test_channel_id_present"]),
        ("send_messages_false", conditions["send_messages_enabled"]),
        ("private_test_reply_false", conditions["private_test_reply_enabled"]),
        ("wrong_reply_mode", conditions["reply_mode_private_test_only"]),
        ("public_or_team_channel", conditions["public_team_blocked"]),
        ("self_message", conditions["not_self"]),
        ("bot_message", conditions["not_bot"]),
        ("duplicate_message", conditions["not_duplicate"]),
        ("llm_enabled", conditions["llm_disabled"]),
        ("rag_enabled", conditions["rag_disabled"]),
        ("embedding_enabled", conditions["embedding_disabled"]),
        ("external_execution_enabled", conditions["external_disabled"]),
        ("one_shot_lock_consumed", conditions["one_shot_session_lock_available"]),
    )
    for reason, passed in checks:
        if not passed:
            return reason
    return ""


def build_phase40y_phase41_reply_preflight_gate(
    env: Mapping[str, str] | None = None,
    event: Mapping[str, Any] | None = None,
    *,
    one_shot_lock_consumed: bool = False,
) -> dict[str, Any]:
    conditions = _conditions(env, event, one_shot_lock_consumed)
    reason = _block_reason(conditions)
    ready = not reason
    report = {
        "report_type": "phase40y_phase41_reply_preflight_gate",
        "version": VERSION,
        "report_only": True,
        "phase41_actual_reply_runtime_available": True,
        "default_blocked": True,
        "blocked": not ready,
        "block_reason": reason or "",
        "actual_reply_send_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "ready_for_phase41_manual_private_test_reply": bool(ready),
        "ready_for_actual_reply_send": False,
        "login_attempted": False,
        "token_present": conditions["token_present"],
        "private_test_channel_id_present": conditions["private_test_channel_id_present"],
        "manual_approval_true": conditions["manual_approval_true"],
        "approval_phrase_exact_match": conditions["approval_phrase_exact_match"],
        "send_messages_enabled": conditions["send_messages_enabled"],
        "private_test_reply_enabled": conditions["private_test_reply_enabled"],
        "reply_mode_private_test_only": conditions["reply_mode_private_test_only"],
        "public_team_blocked": conditions["public_team_blocked"],
        "duplicate_self_bot_guard_active": conditions["not_self"] and conditions["not_bot"] and conditions["not_duplicate"],
        "one_shot_session_lock_available": conditions["one_shot_session_lock_available"],
        "llm_called": False,
        "llm_api_call_attempted": False,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_content_logged": False,
    }
    assert_phase40y_phase41_reply_preflight_gate_safe(report)
    return report


def assert_phase40y_phase41_reply_preflight_gate_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40Y preflight gate contains sensitive values.")
    for key in (
        "actual_reply_send_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "ready_for_actual_reply_send",
        "login_attempted",
        "llm_called",
        "llm_api_call_attempted",
        "rag_called",
        "embedding_api_called",
        "external_execution",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_content_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40Y unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40Y message_sent_count must remain 0.")


def render_phase40y_phase41_reply_preflight_gate_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40Y Phase 41 Reply Preflight Gate",
            "",
            "- Phase 41 actual reply runtime available: true",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Block reason: {report.get('block_reason')}",
            "- Actual reply send executed: false",
            "- Discord message sent: false",
            "- Ready for actual reply send: false",
        ]
    ) + "\n"
