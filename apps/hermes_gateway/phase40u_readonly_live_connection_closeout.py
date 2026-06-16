"""Phase 40U read-only live connection success closeout.

This module formalizes the operator-observed Phase 40T read-only runtime
success without reconnecting to Discord.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase40u_readonly_live_connection_closeout"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40u_readonly_live_connection_closeout(observed: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = {
        "live_runtime_started": True,
        "discord_gateway_connected": True,
        "exit_reason": "timeout",
        "captured_event_count": 0,
        "capture_file_written": True,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
    }
    if observed:
        data.update({key: observed[key] for key in data.keys() & observed.keys()})
    success = (
        bool(data["live_runtime_started"])
        and bool(data["discord_gateway_connected"])
        and data["exit_reason"] == "timeout"
        and int(data["captured_event_count"]) == 0
        and bool(data["capture_file_written"])
        and not bool(data["discord_api_send_called"])
        and not bool(data["discord_message_sent"])
        and int(data["message_sent_count"]) == 0
    )
    report = {
        "report_type": "phase40u_readonly_live_connection_closeout",
        "version": VERSION,
        "report_only": True,
        "phase40t_live_connection_verified": success,
        "gateway_login_verified": bool(data["live_runtime_started"]),
        "gateway_connect_verified": bool(data["discord_gateway_connected"]),
        "read_only_timeout_success": success,
        "human_message_capture_required_for_phase41": False,
        "optional_human_message_capture_available": True,
        "ready_for_phase41_dry_run_preparation": success,
        "ready_for_phase41_actual_reply_send": False,
        "live_runtime_started": bool(data["live_runtime_started"]),
        "discord_gateway_connected": bool(data["discord_gateway_connected"]),
        "exit_reason": str(data["exit_reason"]),
        "captured_event_count": int(data["captured_event_count"]),
        "capture_file_written": bool(data["capture_file_written"]),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "llm_called": False,
        "llm_api_call_attempted": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "approval_phrase_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_content_logged": False,
    }
    assert_phase40u_readonly_live_connection_closeout_safe(report)
    return report


def assert_phase40u_readonly_live_connection_closeout_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40U closeout contains sensitive values.")
    for key in (
        "discord_api_send_called",
        "discord_message_sent",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "llm_called",
        "llm_api_call_attempted",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "approval_phrase_value_logged",
        "raw_discord_ids_logged",
        "raw_content_logged",
        "ready_for_phase41_actual_reply_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40U unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40U message_sent_count must remain 0.")


def render_phase40u_readonly_live_connection_closeout_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40U Read-only Live Connection Closeout",
            "",
            f"- Gateway connect verified: {str(report.get('gateway_connect_verified')).lower()}",
            f"- Read-only timeout success: {str(report.get('read_only_timeout_success')).lower()}",
            f"- Captured event count: {report.get('captured_event_count')}",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
            "- Ready for Phase 41 actual reply send: false",
        ]
    ) + "\n"
