"""Phase51/52 read-only live runtime Manual Gate preflight.

Report-only. This module never starts Discord, sends messages, calls LLM/RAG,
creates embeddings/vector data, starts schedulers, or executes external actions.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Mapping

from private_test_readonly_runtime import APPROVAL_PHRASE


VERSION = "phase51_52_readonly_live_runtime_preflight_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")

AUTHORITATIVE_ENV_KEYS = [
    "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED",
    "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE",
    "HERMES_DISCORD_SEND_MESSAGES",
    "HERMES_DISCORD_PRIVATE_TEST_REPLY",
    "HERMES_DISCORD_REPLY_MODE",
    "HERMES_DISCORD_LLM_ENABLED",
    "HERMES_DISCORD_RAG_ENABLED",
    "HERMES_EMBEDDING_ENABLED",
    "HERMES_VECTOR_ENABLED",
    "HERMES_DISCORD_EXTERNAL_EXECUTION",
]


def _source(env: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if env is None else env


def _value(env: Mapping[str, str] | None, key: str) -> str:
    return str(_source(env).get(key, "") or "")


def _present(env: Mapping[str, str] | None, key: str) -> bool:
    return bool(_value(env, key).strip())


def _true_flag(env: Mapping[str, str] | None, key: str) -> bool:
    return _value(env, key).strip().lower() in {"1", "true", "yes", "on"}


def _false_flag(env: Mapping[str, str] | None, key: str) -> bool:
    return _value(env, key).strip().lower() in {"", "0", "false", "no", "off"}


def evaluate_readonly_live_runtime_gate(env: Mapping[str, str] | None = None) -> dict[str, bool]:
    phrase = _value(env, "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE")
    return {
        "manual_approval_present": _present(env, "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED"),
        "manual_approval_true": _true_flag(env, "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED"),
        "approval_phrase_present": bool(phrase.strip()),
        "approval_phrase_exact_match": phrase == APPROVAL_PHRASE,
        "send_messages_disabled": _false_flag(env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_disabled": _false_flag(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "reply_mode_readonly_private_test_only": _value(env, "HERMES_DISCORD_REPLY_MODE") == "readonly_private_test_only",
        "llm_disabled": _false_flag(env, "HERMES_DISCORD_LLM_ENABLED")
        and _false_flag(env, "HERMES_LLM_DISCORD_SEND_ENABLED")
        and _false_flag(env, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED"),
        "rag_disabled": _false_flag(env, "HERMES_DISCORD_RAG_ENABLED")
        and _false_flag(env, "HERMES_LLM_RAG_ENABLED")
        and _false_flag(env, "HERMES_RAG_LLM_REPLY_ENABLED"),
        "embedding_vector_disabled": _false_flag(env, "HERMES_EMBEDDING_ENABLED")
        and _false_flag(env, "HERMES_VECTOR_ENABLED")
        and _false_flag(env, "HERMES_EMBEDDING_API_ENABLED")
        and _false_flag(env, "HERMES_VECTOR_INDEX_ENABLED"),
        "external_execution_disabled": _false_flag(env, "HERMES_DISCORD_EXTERNAL_EXECUTION"),
    }


def build_phase51_52_readonly_live_runtime_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    gate = evaluate_readonly_live_runtime_gate(env)
    ready = all(gate.values())
    report = {
        "report_type": "phase51_52_readonly_live_runtime_preflight",
        "version": VERSION,
        "report_only": True,
        "manual_gate_required": True,
        "approval_phrase_defined": True,
        "approval_phrase_searchable_in_code": True,
        "approval_phrase_value_logged": False,
        "authoritative_env_keys": list(AUTHORITATIVE_ENV_KEYS),
        **gate,
        "ready_for_manual_readonly_runtime_launch": ready,
        "live_runtime_started": False,
        "actual_discord_runtime_executed": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "actual_llm_api_call_attempted": False,
        "actual_llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_cron_live_execution": False,
        "unattended_auto_reply": False,
        "secret_values_logged": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
    }
    assert_phase51_52_readonly_live_runtime_preflight_safe(report)
    return report


def assert_phase51_52_readonly_live_runtime_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    scrubbed = text.replace(APPROVAL_PHRASE, "")
    if SECRET_RE.search(scrubbed.lower()) or LONG_ID_RE.search(scrubbed) or APPROVAL_RE.search(scrubbed):
        raise ValueError("Phase51/52 read-only preflight contains sensitive values.")
    for key in (
        "approval_phrase_value_logged",
        "live_runtime_started",
        "actual_discord_runtime_executed",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "actual_llm_api_call_attempted",
        "actual_llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_cron_live_execution",
        "unattended_auto_reply",
        "secret_values_logged",
        "raw_content_logged",
        "raw_discord_ids_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase51/52 read-only preflight unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase51/52 read-only preflight message_sent_count must stay 0.")


def render_phase51_52_readonly_live_runtime_preflight_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase51/52 Read-only Live Runtime Preflight",
            "",
            "- Report only: true",
            "- Manual gate required: true",
            "- Approval phrase defined: true",
            "- Approval phrase value logged: false",
            f"- Manual approval present: {str(report.get('manual_approval_present')).lower()}",
            f"- Manual approval true: {str(report.get('manual_approval_true')).lower()}",
            f"- Approval phrase present: {str(report.get('approval_phrase_present')).lower()}",
            f"- Approval phrase exact match: {str(report.get('approval_phrase_exact_match')).lower()}",
            f"- Send messages disabled: {str(report.get('send_messages_disabled')).lower()}",
            f"- Private-test reply disabled: {str(report.get('private_test_reply_disabled')).lower()}",
            f"- Reply mode readonly_private_test_only: {str(report.get('reply_mode_readonly_private_test_only')).lower()}",
            f"- LLM disabled: {str(report.get('llm_disabled')).lower()}",
            f"- RAG disabled: {str(report.get('rag_disabled')).lower()}",
            f"- Embedding/vector disabled: {str(report.get('embedding_vector_disabled')).lower()}",
            f"- External execution disabled: {str(report.get('external_execution_disabled')).lower()}",
            f"- Ready for manual read-only runtime launch: {str(report.get('ready_for_manual_readonly_runtime_launch')).lower()}",
            "- Actual Discord runtime executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
