"""Phase 41B actual private-test deterministic reply one-shot runtime."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from phase41b_reply_adapters import DETERMINISTIC_REPLY_TEXT, Phase41BReplyAdapter, Phase41BReplyEvent


VERSION = "phase41b_actual_private_test_reply_one_shot"
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _eligible(event: Phase41BReplyEvent) -> bool:
    return event.channel_scope == "private_test" and event.author_type == "human" and not event.duplicate


def run_phase41b_actual_reply_runtime(
    *,
    gate_report: Mapping[str, Any],
    adapter: Phase41BReplyAdapter,
    timeout_seconds: int = 60,
    max_events: int = 10,
) -> dict[str, Any]:
    if not gate_report.get("ready_for_manual_private_test_reply_one_shot"):
        report = _base_report(gate_report)
        report.update(
            {
                "blocked": True,
                "blocked_reasons": list(gate_report.get("blocked_reasons", [])) or ["phase41b_gate_not_ready"],
                "actual_runtime_path_available": True,
                "actual_runtime_executed": False,
                "runtime_adapter_type": getattr(adapter, "adapter_type", "unknown"),
            }
        )
        assert_phase41b_runtime_report_safe(report)
        return report

    events = adapter.collect_events(timeout_seconds=timeout_seconds, max_events=max_events)
    eligible_event = next((event for event in events if _eligible(event)), None)
    report = _base_report(gate_report)
    report.update(
        {
            "version": VERSION,
            "safe_prep_only": False,
            "blocked": False,
            "blocked_reasons": [],
            "actual_runtime_path_available": True,
            "actual_runtime_executed": True,
            "runtime_adapter_type": getattr(adapter, "adapter_type", "unknown"),
            "events_observed_count": len(events),
            "eligible_private_test_human_message_found": eligible_event is not None,
            "self_message_ignored": any(event.author_type == "self" for event in events),
            "bot_message_ignored": any(event.author_type == "bot" for event in events),
            "duplicate_message_ignored": any(event.duplicate for event in events),
            "public_team_blocked": all(event.channel_scope not in {"public", "team"} for event in events),
        }
    )
    if eligible_event is None:
        report.update(_no_send_result("no_eligible_private_test_human_message"))
    else:
        send_result = adapter.send_reply(eligible_event, DETERMINISTIC_REPLY_TEXT)
        sent_count = int(send_result.message_sent_count or 0)
        sent_once = bool(send_result.message_sent) and sent_count == 1 and send_result.sent_scope == "private_test_only"
        report.update(
            {
                "actual_reply_send_executed": sent_once,
                "discord_api_send_called": bool(send_result.api_send_called),
                "discord_message_sent": bool(send_result.message_sent),
                "message_sent_count": sent_count,
                "sent_scope": send_result.sent_scope,
                "send_result_error_type": send_result.error_type,
                "ready_for_phase41c_actual_reply_closeout": sent_once,
                "ready_for_repeat_send": False,
                "ready_for_supervised_session": False,
                "one_shot_lock_consumed": sent_once,
            }
        )
        if not sent_once:
            report["blocked"] = True
            report["blocked_reasons"] = ["reply_send_failed_or_not_exactly_once"]
    assert_phase41b_runtime_report_safe(report)
    return report


def _base_report(gate_report: Mapping[str, Any]) -> dict[str, Any]:
    report = dict(gate_report)
    report.update(
        {
            "report_type": "phase41b_private_test_reply_one_shot",
            "llm_api_call_attempted": False,
            "llm_api_called": False,
            "llm_called": False,
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
            "discord_token_value_logged": False,
            "private_test_channel_id_value_logged": False,
            "approval_phrase_value_logged": False,
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
            "raw_content_logged": False,
            "raw_message_content_logged": False,
            "full_content_dump": False,
        }
    )
    return report


def _no_send_result(reason: str) -> dict[str, Any]:
    return {
        "actual_reply_send_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "sent_scope": "none",
        "blocked": True,
        "blocked_reasons": [reason],
        "ready_for_phase41c_actual_reply_closeout": False,
        "ready_for_repeat_send": False,
        "ready_for_supervised_session": False,
    }


def assert_phase41b_runtime_report_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 41B runtime report contains sensitive values.")
    for key in (
        "llm_api_call_attempted",
        "llm_api_called",
        "llm_called",
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
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_content_logged",
        "raw_message_content_logged",
        "full_content_dump",
        "ready_for_repeat_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 41B runtime unsafe flag is true: {key}")
    sent_count = int(report.get("message_sent_count", 0) or 0)
    if sent_count > 1:
        raise ValueError("Phase 41B runtime allows at most one message.")
    if sent_count == 1 and report.get("sent_scope") != "private_test_only":
        raise ValueError("Phase 41B runtime success must be private-test only.")
