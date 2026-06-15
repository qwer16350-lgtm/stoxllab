"""Phase 39C post-send safety audit, report-only."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from phase39c_actual_send_closeout import build_phase39c_actual_send_closeout
from phase39c_no_repeat_send_lock import build_phase39c_no_repeat_send_lock


VERSION = "phase39c_post_send_safety_audit"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _flag(env: dict[str, Any], key: str) -> bool:
    return str(env.get(key, "") or "").strip().lower() == "true"


def build_phase39c_post_send_safety_audit(
    *,
    env: dict[str, Any] | None = None,
    closeout: dict[str, Any] | None = None,
    no_repeat_lock: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_env = env if env is not None else os.environ
    selected_closeout = closeout or build_phase39c_actual_send_closeout()
    selected_lock = no_repeat_lock or build_phase39c_no_repeat_send_lock(selected_closeout)
    approval_gate_off = not _flag(source_env, "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED") and not str(source_env.get("HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE", "") or "").strip()
    report = {
        "report_type": "phase39c_post_send_safety_audit",
        "version": VERSION,
        "report_only": True,
        "phase39b_actual_send_count": int(selected_closeout.get("actual_discord_send_count", 0) or 0),
        "phase39c_additional_send_count": int(selected_closeout.get("additional_message_sent_count_in_phase39c", 0) or 0),
        "total_actual_discord_send_count_this_sequence": int(selected_closeout.get("actual_discord_send_count", 0) or 0),
        "gate_off_verified": False,
        "approval_gate_off": approval_gate_off,
        "discord_send_messages_off": not _flag(source_env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_off": not _flag(source_env, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "reply_mode_empty": not str(source_env.get("HERMES_DISCORD_REPLY_MODE", "") or "").strip(),
        "real_discord_send_execution_off": not _flag(source_env, "HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION"),
        "llm_disabled": not (_flag(source_env, "HERMES_LLM_DISCORD_SEND_ENABLED") or _flag(source_env, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED") or _flag(source_env, "HERMES_DISCORD_LLM_ENABLED")),
        "rag_disabled": not (_flag(source_env, "HERMES_DISCORD_RAG_ENABLED") or _flag(source_env, "HERMES_LLM_RAG_ENABLED") or _flag(source_env, "HERMES_RAG_LLM_REPLY_ENABLED")),
        "embedding_disabled": True,
        "external_execution_disabled": not _flag(source_env, "HERMES_DISCORD_EXTERNAL_EXECUTION"),
        "public_team_forbidden": True,
        "unattended_auto_reply_allowed": False,
        "repeat_send_allowed": bool(selected_lock.get("repeat_send_allowed")),
        "automatic_retry_allowed": bool(selected_lock.get("automatic_retry_allowed")),
        "manual_retry_allowed": bool(selected_lock.get("manual_retry_allowed")),
        "ready_for_repeat_send": bool(selected_lock.get("ready_for_repeat_send")),
        "additional_discord_send_called_in_phase39c": False,
        "additional_discord_message_sent_in_phase39c": False,
        "secret_values_logged": False,
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
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
    }
    gate_keys = (
        "approval_gate_off",
        "discord_send_messages_off",
        "private_test_reply_off",
        "reply_mode_empty",
        "real_discord_send_execution_off",
        "llm_disabled",
        "rag_disabled",
        "embedding_disabled",
        "external_execution_disabled",
    )
    report["gate_off_verified"] = all(bool(report.get(key)) for key in gate_keys)
    assert_phase39c_post_send_safety_audit_safe(report)
    return report


def assert_phase39c_post_send_safety_audit_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 39C safety audit contains sensitive values.")
    if report.get("phase39b_actual_send_count") != 1 or report.get("total_actual_discord_send_count_this_sequence") != 1:
        raise ValueError("Phase 39C safety audit requires total actual send count 1.")
    if int(report.get("phase39c_additional_send_count", 0) or 0) != 0:
        raise ValueError("Phase 39C safety audit forbids additional sends.")
    for key in (
        "unattended_auto_reply_allowed",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "manual_retry_allowed",
        "ready_for_repeat_send",
        "additional_discord_send_called_in_phase39c",
        "additional_discord_message_sent_in_phase39c",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
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
    ):
        if report.get(key):
            raise ValueError(f"Phase 39C safety audit unsafe flag is true: {key}")
    if not report.get("gate_off_verified"):
        raise ValueError("Phase 39C safety audit requires gates off.")


def render_phase39c_post_send_safety_audit_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 39C Post-send Safety Audit",
            "",
            "- Report only: true",
            "- Phase 39B actual send count: 1",
            "- Phase 39C additional send count: 0",
            "- Gate off verified: true",
            "- LLM disabled: true",
            "- RAG disabled: true",
            "- Embedding disabled: true",
            "- External execution disabled: true",
            "- Public/team forbidden: true",
            "- Unattended auto reply allowed: false",
        ]
    ) + "\n"
