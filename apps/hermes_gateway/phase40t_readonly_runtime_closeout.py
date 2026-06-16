"""Phase 40T read-only runtime closeout report."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION_EMPTY = "phase40t_readonly_runtime_closeout_empty"
VERSION_ACTUAL = "phase40t_actual_readonly_runtime_closeout"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40t_readonly_runtime_closeout(
    *,
    started: bool = False,
    gateway_connected: bool = False,
    timeout_seconds: int = 60,
    max_events: int = 10,
    exit_reason: str = "not_executed",
    captured_event_count: int = 0,
    captured_private_test_human_message_count: int = 0,
    captured_self_message_count: int = 0,
    captured_bot_message_count: int = 0,
    captured_duplicate_message_count: int = 0,
    captured_public_team_blocked_count: int = 0,
    capture_file_written: bool = False,
    capture_file_path_logged: bool = False,
) -> dict[str, Any]:
    report = {
        "report_type": "phase40t_readonly_runtime_closeout",
        "version": VERSION_ACTUAL if started else VERSION_EMPTY,
        "mode": "private_test_readonly_live_execution",
        "execute_flag_present": bool(started),
        "blocked": False if started else True,
        "started": bool(started),
        "live_runtime_started": bool(started),
        "discord_gateway_connected": bool(gateway_connected),
        "runtime_scope": "private_test_readonly",
        "timeout_seconds": int(timeout_seconds),
        "max_events": int(max_events),
        "exit_reason": str(exit_reason),
        "captured_event_count": int(captured_event_count),
        "captured_private_test_human_message_count": int(captured_private_test_human_message_count),
        "captured_self_message_count": int(captured_self_message_count),
        "captured_bot_message_count": int(captured_bot_message_count),
        "captured_duplicate_message_count": int(captured_duplicate_message_count),
        "captured_public_team_blocked_count": int(captured_public_team_blocked_count),
        "capture_file_written": bool(capture_file_written),
        "capture_file_path_logged": bool(capture_file_path_logged),
        "capture_file_contains_raw_content": False,
        "capture_file_contains_raw_discord_ids": False,
        "capture_file_contains_secret_values": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "send_messages_enabled": False,
        "private_test_reply_enabled": False,
        "reply_mode_readonly_private_test_only": True,
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
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_content_logged": False,
        "ready_for_capture_closeout": bool(started and capture_file_written),
        "ready_for_phase41_reply_runtime": False,
        "ready_for_reply_send": False,
    }
    assert_phase40t_readonly_runtime_closeout_safe(report)
    return report


def assert_phase40t_readonly_runtime_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40T closeout contains sensitive values.")
    for key in (
        "capture_file_contains_raw_content",
        "capture_file_contains_raw_discord_ids",
        "capture_file_contains_secret_values",
        "discord_api_send_called",
        "discord_message_sent",
        "send_messages_enabled",
        "private_test_reply_enabled",
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
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_content_logged",
        "ready_for_phase41_reply_runtime",
        "ready_for_reply_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40T closeout unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40T closeout message_sent_count must remain 0.")


def render_phase40t_readonly_runtime_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40T Read-only Runtime Closeout",
            "",
            f"- Started: {str(report.get('started')).lower()}",
            f"- Discord Gateway connected: {str(report.get('discord_gateway_connected')).lower()}",
            f"- Captured event count: {report.get('captured_event_count')}",
            f"- Capture file written: {str(report.get('capture_file_written')).lower()}",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
            "- Ready for Phase 41 reply runtime: false",
        ]
    ) + "\n"
