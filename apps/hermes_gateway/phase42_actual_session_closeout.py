"""Phase 42 actual supervised private-test session closeout."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase42_actual_supervised_session_closeout"
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|api[_ -]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


OBSERVED_PHASE42_SUCCESS = {
    "message_sent_count": 1,
    "sent_scope": "private_test_only",
    "runtime_adapter_type": "real_discord",
    "events_observed_count": 2,
    "eligible_private_test_human_message_found": True,
    "session_lock_consumed": True,
}


def build_phase42_actual_session_closeout(observed: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source = {**OBSERVED_PHASE42_SUCCESS, **dict(observed or {})}
    sent_count = int(source.get("message_sent_count", 0) or 0)
    sent_scope = str(source.get("sent_scope", ""))
    session_lock_consumed = bool(source.get("session_lock_consumed"))
    exactly_once_private_test = sent_count == 1 and sent_scope == "private_test_only"
    success = exactly_once_private_test and session_lock_consumed
    report = {
        "report_type": "phase42_actual_session_closeout",
        "version": VERSION,
        "phase42_actual_supervised_private_test_session_succeeded": success,
        "phase42_exactly_once_supervised_success_recorded": success,
        "message_sent_count": sent_count if success else 0,
        "sent_scope": sent_scope if success else "none",
        "runtime_adapter_type": str(source.get("runtime_adapter_type", "redacted")),
        "events_observed_count": int(source.get("events_observed_count", 0) or 0) if success else 0,
        "eligible_private_test_human_message_found": bool(source.get("eligible_private_test_human_message_found")) if success else False,
        "session_lock_consumed": session_lock_consumed,
        "phase42_repeat_supervised_session_locked": success,
        "phase42_repeat_supervised_session_allowed": False,
        "phase41b_repeat_send_locked": True,
        "ready_for_phase42_repeat_supervised_session": False,
        "ready_for_phase41b_repeat_send": False,
        "ready_for_manual_gate_3_actual_llm_one_shot": success,
        "actual_discord_runtime_executed_during_closeout": False,
        "discord_api_send_called_during_closeout": False,
        "discord_message_sent_during_closeout": False,
        "additional_message_sent_count_during_closeout": 0,
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
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_discord_session_id_logged": False,
        "raw_content_logged": False,
        "raw_message_content_logged": False,
    }
    if not success:
        report["blocked_reasons"] = ["phase42_actual_session_success_not_exactly_once_private_test"]
    assert_phase42_closeout_safe(report)
    return report


def assert_phase42_closeout_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 42 closeout contains sensitive values.")
    for key in (
        "phase42_repeat_supervised_session_allowed",
        "ready_for_phase42_repeat_supervised_session",
        "ready_for_phase41b_repeat_send",
        "actual_discord_runtime_executed_during_closeout",
        "discord_api_send_called_during_closeout",
        "discord_message_sent_during_closeout",
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
        "token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_discord_session_id_logged",
        "raw_content_logged",
        "raw_message_content_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 42 closeout unsafe flag is true: {key}")
    if int(report.get("additional_message_sent_count_during_closeout", 0) or 0) != 0:
        raise ValueError("Phase 42 closeout must not add sends.")
    if report.get("phase42_actual_supervised_private_test_session_succeeded"):
        if int(report.get("message_sent_count", 0) or 0) != 1 or report.get("sent_scope") != "private_test_only":
            raise ValueError("Phase 42 closeout success must be exactly one private-test message.")


def render_phase42_actual_session_closeout_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 42 Actual Session Closeout",
            "",
            f"- Phase 42 success recorded: {str(report.get('phase42_actual_supervised_private_test_session_succeeded')).lower()}",
            f"- Message sent count: {report.get('message_sent_count')}",
            f"- Sent scope: {report.get('sent_scope')}",
            f"- Repeat supervised session locked: {str(report.get('phase42_repeat_supervised_session_locked')).lower()}",
            "- Discord API send during closeout: false",
            "- LLM API attempt during closeout: false",
        ]
    ) + "\n"
