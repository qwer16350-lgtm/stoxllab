"""Phase 41C actual private-test reply success closeout.

This module records the already observed Phase 41B private-test reply success.
It does not connect to Discord, call Discord APIs, or send a message.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase41c_actual_private_test_reply_closeout_safe_prep"
_SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|api[_ -]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
_LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
_APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")

PHASE41B_FAILED_ATTEMPT = {
    "attempt_label": "phase41b_safe_failed_attempt",
    "send_result_error_type": "RuntimeError",
    "send_result_error_category": "adapter_not_wired_or_contract_error",
    "message_sent_count": 0,
    "discord_api_send_called": False,
    "discord_message_sent": False,
    "counted_as_success": False,
}

PHASE41B_SUCCESS_ATTEMPT = {
    "attempt_label": "phase41b_actual_private_test_reply_success",
    "actual_runtime_executed": True,
    "runtime_adapter_type": "real_discord",
    "real_discord_send_adapter_wired": True,
    "eligible_private_test_human_message_found": True,
    "actual_reply_send_executed": True,
    "discord_api_send_called": True,
    "discord_message_sent": True,
    "message_sent_count": 1,
    "sent_scope": "private_test_only",
    "one_shot_lock_consumed": True,
    "ready_for_phase41c_actual_reply_closeout": True,
    "ready_for_repeat_send": False,
    "counted_as_success": True,
}


def build_phase41c_actual_reply_closeout(result: Mapping[str, Any] | None = None) -> dict[str, Any]:
    result = PHASE41B_SUCCESS_ATTEMPT if result is None else result
    count = int(result.get("message_sent_count", 0) or 0)
    sent_scope = str(result.get("sent_scope", result.get("sent_channel_scope", "none")) or "none")
    if sent_scope == "private_test":
        sent_scope = "private_test_only"
    repeat_attempted = bool(result.get("repeat_send_attempted"))
    self_loop = bool(result.get("self_loop_message"))
    bot_message = bool(result.get("bot_message"))
    duplicate = bool(result.get("duplicate_message"))
    single_private_success = count == 1 and sent_scope == "private_test_only" and not repeat_attempted
    no_send = count == 0
    failure = count > 1 or sent_scope in {"public", "team"} or repeat_attempted
    report = {
        "report_type": "phase41c_actual_private_test_reply_closeout",
        "version": VERSION,
        "report_only": True,
        "phase41c_actual_runtime_executed": False,
        "actual_runtime_executed": False,
        "actual_reply_send_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "discord_api_send_called_during_phase41c": False,
        "discord_message_sent_during_phase41c": False,
        "message_sent_during_phase41c_count": 0,
        "phase41b_actual_result_observed": True,
        "actual_private_test_reply_verified": single_private_success,
        "no_send_closeout": no_send,
        "failure": failure,
        "message_sent_count": count,
        "sent_scope": sent_scope if sent_scope in {"none", "private_test_only", "public", "team"} else "redacted",
        "sent_channel_scope": sent_scope if sent_scope in {"none", "private_test_only", "public", "team"} else "redacted",
        "phase41b_message_sent_count_locked": count if single_private_success else 0,
        "phase41b_sent_scope_locked": "private_test_only" if single_private_success else "none",
        "phase41b_discord_api_send_called_observed": bool(result.get("discord_api_send_called")) and single_private_success,
        "phase41b_discord_message_sent_observed": bool(result.get("discord_message_sent")) and single_private_success,
        "no_repeat_lock_consumed": single_private_success,
        "phase41b_one_shot_lock_consumed": single_private_success,
        "phase41b_repeat_send_locked": True,
        "repeat_send_blocked": True,
        "ready_for_repeat_send": False,
        "ready_for_supervised_session": False,
        "ready_for_phase42_supervised_deterministic_session_manual_gate": single_private_success,
        "self_loop_ignored": self_loop,
        "bot_message_ignored": bot_message,
        "duplicate_message_ignored": duplicate,
        "public_team_blocked": sent_scope not in {"public", "team"},
        "failed_previous_attempt_recorded": True,
        "failed_previous_attempt_message_sent_count": int(PHASE41B_FAILED_ATTEMPT["message_sent_count"]),
        "failed_previous_attempt_counted_as_success": False,
        "final_success_attempt_recorded": single_private_success,
        "final_success_attempt_counted_as_success": single_private_success,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_discord_session_id_logged": False,
        "raw_content_logged": False,
        "raw_message_content_logged": False,
        "secret_values_logged": False,
    }
    assert_phase41c_closeout_safe(report)
    return report


def assert_phase41c_closeout_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if _SECRET_RE.search(text) or _LONG_ID_RE.search(text) or _APPROVAL_RE.search(text):
        raise ValueError("Phase 41C closeout contains a sensitive value.")
    for key in (
        "phase41c_actual_runtime_executed",
        "actual_runtime_executed",
        "actual_reply_send_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "discord_api_send_called_during_phase41c",
        "discord_message_sent_during_phase41c",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_discord_session_id_logged",
        "raw_content_logged",
        "raw_message_content_logged",
        "secret_values_logged",
        "ready_for_repeat_send",
        "ready_for_supervised_session",
    ):
        if report.get(key):
            raise ValueError(f"Phase 41C closeout unsafe flag is true: {key}")
    if report.get("ready_for_repeat_send"):
        raise ValueError("Phase 41C closeout must not allow repeat send.")
    if report.get("sent_scope") in {"public", "team"} and not report.get("failure"):
        raise ValueError("Phase 41C must fail public/team sends.")
    if int(report.get("message_sent_during_phase41c_count", 0) or 0) != 0:
        raise ValueError("Phase 41C must not send messages.")
    if report.get("actual_private_test_reply_verified") and int(report.get("message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase 41C success must record exactly one observed Phase 41B message.")


def render_phase41c_actual_reply_closeout_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 41C Actual Reply Closeout",
            "",
            f"- Actual private-test reply verified: {str(report.get('actual_private_test_reply_verified')).lower()}",
            f"- Message sent count: {report.get('message_sent_count')}",
            f"- Sent scope: {report.get('sent_scope')}",
            f"- Repeat send blocked: {str(report.get('repeat_send_blocked')).lower()}",
            f"- Ready for supervised session: {str(report.get('ready_for_supervised_session')).lower()}",
            f"- Ready for Phase 42 manual gate: {str(report.get('ready_for_phase42_supervised_deterministic_session_manual_gate')).lower()}",
            "- Discord API send during Phase 41C: false",
            "- Discord message sent during Phase 41C: false",
        ]
    ) + "\n"
