"""Phase52B metadata-only closeout for the read-only live capture Manual Gate."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase52b_readonly_live_capture_closeout_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase52b_readonly_live_capture_closeout() -> dict[str, Any]:
    report = {
        "report_type": "phase52b_readonly_live_capture_closeout",
        "version": VERSION,
        "metadata_only": True,
        "actual_readonly_runtime_executed": True,
        "discord_gateway_connected": True,
        "runtime_scope": "private_test_readonly",
        "exit_reason": "timeout",
        "timeout_seconds": 60,
        "max_events": 5,
        "captured_event_count": 0,
        "captured_private_test_human_message_count": 0,
        "captured_self_message_count": 0,
        "captured_bot_message_count": 0,
        "captured_duplicate_message_count": 0,
        "captured_public_team_blocked_count": 0,
        "capture_file_written": True,
        "capture_file_metadata_available": True,
        "capture_file_path_value_logged": False,
        "capture_file_read_attempted": False,
        "empty_capture_handled": True,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_cron_live_execution": False,
        "unattended_auto_reply": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "ready_for_capture_to_review_packet_replay": True,
    }
    assert_phase52b_readonly_live_capture_closeout_safe(report)
    return report


def assert_phase52b_readonly_live_capture_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase52B closeout contains sensitive values.")
    for key in (
        "capture_file_path_value_logged",
        "capture_file_read_attempted",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_cron_live_execution",
        "unattended_auto_reply",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase52B closeout unsafe flag is true: {key}")
    for key in (
        "metadata_only",
        "actual_readonly_runtime_executed",
        "discord_gateway_connected",
        "capture_file_written",
        "capture_file_metadata_available",
        "empty_capture_handled",
        "ready_for_capture_to_review_packet_replay",
    ):
        if not report.get(key):
            raise ValueError(f"Phase52B closeout required flag is false: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase52B closeout message_sent_count must stay 0.")


def render_phase52b_readonly_live_capture_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase52B Read-only Live Capture Closeout",
            "",
            "- Metadata only: true",
            "- Actual read-only runtime executed: true",
            "- Discord Gateway connected: true",
            "- Exit reason: timeout",
            f"- Timeout seconds: {report.get('timeout_seconds')}",
            f"- Max events: {report.get('max_events')}",
            f"- Captured event count: {report.get('captured_event_count')}",
            "- Empty capture handled: true",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- LLM/RAG/embedding/external: false",
            "- Ready for capture-to-review-packet replay: true",
        ]
    ) + "\n"
