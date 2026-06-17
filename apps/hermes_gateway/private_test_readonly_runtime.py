"""Phase 40T private-test read-only runtime preflight.

This module is intentionally preflight/report-only. It does not connect to
Discord, send messages, call LLM/RAG providers, create embeddings, or execute
external actions.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Mapping

from phase40t_readonly_preflight_snapshot import build_phase40t_readonly_preflight_snapshot


VERSION = "phase40t_private_test_readonly_runtime_preflight"
APPROVAL_PHRASE = "I_APPROVE_PHASE40J_PRIVATE_TEST_READONLY_RUNTIME"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _value(source: Mapping[str, str] | None, key: str) -> str:
    if source is None:
        source = os.environ
    return str(source.get(key, "") or "")


def _present(source: Mapping[str, str] | None, key: str) -> bool:
    return bool(_value(source, key).strip())


def _flag(source: Mapping[str, str] | None, key: str) -> bool:
    return _value(source, key).strip().lower() in {"1", "true", "yes", "on"}


def _false_flag(source: Mapping[str, str] | None, key: str) -> bool:
    return not _flag(source, key)


def _build_conditions(source: Mapping[str, str] | None) -> dict[str, bool]:
    approval_flag = _flag(source, "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED")
    phrase_present = _present(source, "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE")
    phrase_exact = _value(source, "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE") == APPROVAL_PHRASE
    llm_disabled = (
        _false_flag(source, "HERMES_DISCORD_LLM_ENABLED")
        and _false_flag(source, "HERMES_LLM_DISCORD_SEND_ENABLED")
        and _false_flag(source, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED")
    )
    rag_disabled = (
        _false_flag(source, "HERMES_DISCORD_RAG_ENABLED")
        and _false_flag(source, "HERMES_LLM_RAG_ENABLED")
        and _false_flag(source, "HERMES_RAG_LLM_REPLY_ENABLED")
    )
    embedding_disabled = (
        _false_flag(source, "HERMES_EMBEDDING_ENABLED")
        and _false_flag(source, "HERMES_VECTOR_ENABLED")
        and _false_flag(source, "HERMES_EMBEDDING_API_ENABLED")
        and _false_flag(source, "HERMES_VECTOR_INDEX_ENABLED")
    )
    return {
        "discord_token_present": _present(source, "DISCORD_BOT_TOKEN"),
        "private_test_channel_id_present": _present(source, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "manual_approval_present": _present(source, "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED"),
        "manual_approval_true": approval_flag,
        "approval_phrase_present": phrase_present,
        "approval_phrase_exact_match": phrase_exact,
        "approval_actualized": approval_flag and phrase_exact,
        "send_messages_disabled": _false_flag(source, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_disabled": _false_flag(source, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "reply_mode_readonly_private_test_only": _value(source, "HERMES_DISCORD_REPLY_MODE") == "readonly_private_test_only",
        "discord_llm_disabled": _false_flag(source, "HERMES_DISCORD_LLM_ENABLED"),
        "llm_discord_send_disabled": _false_flag(source, "HERMES_LLM_DISCORD_SEND_ENABLED"),
        "llm_private_test_reply_disabled": _false_flag(source, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED"),
        "llm_disabled": llm_disabled,
        "discord_rag_disabled": _false_flag(source, "HERMES_DISCORD_RAG_ENABLED"),
        "llm_rag_disabled": _false_flag(source, "HERMES_LLM_RAG_ENABLED"),
        "rag_llm_reply_disabled": _false_flag(source, "HERMES_RAG_LLM_REPLY_ENABLED"),
        "rag_disabled": rag_disabled,
        "external_execution_disabled": _false_flag(source, "HERMES_DISCORD_EXTERNAL_EXECUTION"),
        "embedding_disabled": embedding_disabled,
        "embedding_vector_disabled": embedding_disabled,
    }


def _failure_reason(conditions: dict[str, bool]) -> str:
    checks = (
        ("approval_missing_or_mismatch", conditions["approval_actualized"]),
        ("discord_token_missing", conditions["discord_token_present"]),
        ("private_test_channel_id_missing", conditions["private_test_channel_id_present"]),
        ("send_messages_enabled", conditions["send_messages_disabled"]),
        ("private_test_reply_enabled", conditions["private_test_reply_disabled"]),
        ("reply_mode_not_readonly_private_test_only", conditions["reply_mode_readonly_private_test_only"]),
        ("discord_llm_enabled", conditions["discord_llm_disabled"]),
        ("llm_discord_send_enabled", conditions["llm_discord_send_disabled"]),
        ("llm_private_test_reply_enabled", conditions["llm_private_test_reply_disabled"]),
        ("discord_rag_enabled", conditions["discord_rag_disabled"]),
        ("llm_rag_enabled", conditions["llm_rag_disabled"]),
        ("rag_llm_reply_enabled", conditions["rag_llm_reply_disabled"]),
        ("external_execution_enabled", conditions["external_execution_disabled"]),
        ("embedding_or_vector_enabled", conditions["embedding_disabled"]),
    )
    for reason, passed in checks:
        if not passed:
            return reason
    return ""


def build_private_test_readonly_runtime_preflight(
    env: Mapping[str, str] | None = None,
    *,
    report_only: bool = True,
) -> dict[str, Any]:
    conditions = _build_conditions(env)
    reason = _failure_reason(conditions)
    preflight_passed = not reason
    report = {
        "report_type": "phase40t_private_test_readonly_runtime_command",
        "version": VERSION,
        "mode": "private_test_readonly_runtime",
        "blocked": not preflight_passed,
        "started": False,
        "report_only": bool(report_only),
        "preflight_passed": preflight_passed,
        "manual_runtime_launch_allowed": preflight_passed,
        "codex_runtime_launch_forbidden": True,
        "reason": "" if preflight_passed else f"private_test_readonly_preflight_failed:{reason}",
        "discord_token_present": conditions["discord_token_present"],
        "discord_token_value_logged": False,
        "private_test_channel_id_present": conditions["private_test_channel_id_present"],
        "private_test_channel_id_value_logged": False,
        "approval_required": True,
        "manual_approval_present": conditions["manual_approval_present"],
        "manual_approval_true": conditions["manual_approval_true"],
        "approval_actualized": conditions["approval_actualized"],
        "approval_phrase_present": conditions["approval_phrase_present"],
        "approval_phrase_exact_match": conditions["approval_phrase_exact_match"],
        "approval_phrase_value_logged": False,
        "send_messages_enabled": not conditions["send_messages_disabled"],
        "send_messages_disabled": conditions["send_messages_disabled"],
        "private_test_reply_enabled": not conditions["private_test_reply_disabled"],
        "private_test_reply_disabled": conditions["private_test_reply_disabled"],
        "reply_mode_readonly_private_test_only": conditions["reply_mode_readonly_private_test_only"],
        "llm_disabled": conditions["llm_disabled"],
        "rag_disabled": conditions["rag_disabled"],
        "embedding_vector_disabled": conditions["embedding_vector_disabled"],
        "external_execution_disabled": conditions["external_execution_disabled"],
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "ready_for_manual_readonly_runtime_launch": preflight_passed,
        "ready_for_capture_closeout": False,
        "ready_for_phase41_reply_runtime": False,
        "ready_for_reply_send": False,
    }
    report["preflight_snapshot"] = build_phase40t_readonly_preflight_snapshot(report)
    report["preflight_snapshot_preserved"] = True
    report["presence_consistency_verified"] = True
    report["login_attempt_requires_token_and_channel"] = True
    assert_private_test_readonly_runtime_preflight_safe(report)
    return report


def assert_private_test_readonly_runtime_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40T private-test read-only runtime report contains sensitive values.")
    if not report.get("codex_runtime_launch_forbidden"):
        raise ValueError("Phase 40T requires Codex runtime launch forbidden.")
    for key in (
        "started",
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "ready_for_capture_closeout",
        "ready_for_phase41_reply_runtime",
        "ready_for_reply_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40T unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40T message_sent_count must remain 0.")
    if report.get("preflight_passed"):
        if report.get("send_messages_enabled") or report.get("private_test_reply_enabled"):
            raise ValueError("Phase 40T ready report requires send/reply disabled.")
        if not report.get("reply_mode_readonly_private_test_only"):
            raise ValueError("Phase 40T ready report requires readonly_private_test_only reply mode.")


def render_private_test_readonly_runtime_preflight_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40T Private-test Read-only Runtime Command",
            "",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Started: {str(report.get('started')).lower()}",
            f"- Preflight passed: {str(report.get('preflight_passed')).lower()}",
            f"- Manual runtime launch allowed: {str(report.get('manual_runtime_launch_allowed')).lower()}",
            "- Codex runtime launch forbidden: true",
            f"- Discord token present: {str(report.get('discord_token_present')).lower()}",
            "- Discord token value logged: false",
            f"- Private-test channel id present: {str(report.get('private_test_channel_id_present')).lower()}",
            "- Private-test channel id value logged: false",
            f"- Approval actualized: {str(report.get('approval_actualized')).lower()}",
            "- Approval phrase value logged: false",
            f"- Send messages enabled: {str(report.get('send_messages_enabled')).lower()}",
            f"- Private-test reply enabled: {str(report.get('private_test_reply_enabled')).lower()}",
            f"- Reply mode readonly_private_test_only: {str(report.get('reply_mode_readonly_private_test_only')).lower()}",
            "- Live runtime started: false",
            "- Discord Gateway connected: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
            "- LLM/RAG/embedding/external: false",
        ]
    ) + "\n"
