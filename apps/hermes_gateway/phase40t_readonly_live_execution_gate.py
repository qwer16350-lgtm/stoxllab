"""Phase 40T-1 user-only read-only live execution gate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from private_test_readonly_runtime import build_private_test_readonly_runtime_preflight
from phase40t_readonly_capture_writer import validate_capture_root


VERSION = "phase40t_readonly_live_execution_gate"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40t_readonly_live_execution_gate(
    env: Mapping[str, str] | None = None,
    *,
    execute_flag_present: bool = False,
    timeout_seconds: int = 60,
    max_events: int = 10,
    capture_root: str | Path | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    preflight = build_private_test_readonly_runtime_preflight(env=env, report_only=False)
    preflight_snapshot = dict(preflight.get("preflight_snapshot", {}))
    capture_root_valid, capture_root_reason, _ = validate_capture_root(capture_root, root)
    options_valid = True
    option_reason = ""
    if int(timeout_seconds) <= 0 or int(timeout_seconds) > 300:
        options_valid = False
        option_reason = "invalid_timeout_seconds"
    elif int(max_events) < 0 or int(max_events) > 100:
        options_valid = False
        option_reason = "invalid_max_events"
    elif not capture_root_valid:
        options_valid = False
        option_reason = capture_root_reason
    reason = ""
    if not execute_flag_present:
        reason = "execute_flag_missing"
    elif preflight.get("blocked"):
        reason = str(preflight.get("reason", "private_test_readonly_preflight_failed:unknown")).replace(
            "private_test_readonly_preflight_failed:", ""
        )
    elif not options_valid:
        reason = option_reason
    blocked = bool(reason)
    report = {
        "report_type": "phase40t_readonly_live_execution_gate",
        "version": VERSION,
        "mode": "private_test_readonly_live_execution",
        "execute_flag_present": bool(execute_flag_present),
        "execute_flag_required": True,
        "blocked": blocked,
        "started": False,
        "reason": "" if not blocked else f"readonly_live_execution_preflight_failed:{reason}",
        "preflight_passed": bool(preflight.get("preflight_passed")) and options_valid and bool(execute_flag_present),
        "preflight_snapshot": preflight_snapshot,
        "preflight_snapshot_preserved": bool(preflight_snapshot),
        "presence_consistency_verified": True,
        "login_attempt_requires_token_and_channel": True,
        "login_attempted": False,
        "discord_login_failure": False,
        "manual_runtime_launch_allowed": bool(preflight.get("manual_runtime_launch_allowed")) and options_valid and bool(execute_flag_present),
        "codex_runtime_launch_forbidden": True,
        "timeout_seconds": int(timeout_seconds),
        "max_events": int(max_events),
        "capture_root_valid": bool(capture_root_valid),
        "capture_root_value_logged": False,
        "discord_token_present": bool(preflight.get("discord_token_present")),
        "discord_token_value_logged": False,
        "private_test_channel_id_present": bool(preflight.get("private_test_channel_id_present")),
        "private_test_channel_id_value_logged": False,
        "approval_actualized": bool(preflight.get("approval_actualized")),
        "approval_phrase_present": bool(preflight.get("approval_phrase_present")),
        "approval_phrase_exact_match": bool(preflight.get("approval_phrase_exact_match")),
        "approval_phrase_value_logged": False,
        "send_messages_enabled": bool(preflight.get("send_messages_enabled")),
        "private_test_reply_enabled": bool(preflight.get("private_test_reply_enabled")),
        "reply_mode_readonly_private_test_only": bool(preflight.get("reply_mode_readonly_private_test_only")),
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "capture_file_written": False,
        "capture_file_path_logged": False,
        "capture_file_contains_raw_content": False,
        "capture_file_contains_raw_discord_ids": False,
        "capture_file_contains_secret_values": False,
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
        "ready_for_capture_closeout": False,
        "ready_for_phase41_reply_runtime": False,
        "ready_for_reply_send": False,
    }
    assert_phase40t_readonly_live_execution_gate_safe(report)
    return report


def assert_phase40t_readonly_live_execution_gate_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40T execution gate contains sensitive values.")
    if not report.get("codex_runtime_launch_forbidden"):
        raise ValueError("Phase 40T execution gate requires Codex runtime launch forbidden.")
    for key in (
        "started",
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "capture_file_written",
        "capture_file_contains_raw_content",
        "capture_file_contains_raw_discord_ids",
        "capture_file_contains_secret_values",
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
        "ready_for_capture_closeout",
        "ready_for_phase41_reply_runtime",
        "ready_for_reply_send",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "capture_root_value_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40T execution gate unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40T execution gate message_sent_count must remain 0.")


def render_phase40t_readonly_live_execution_gate_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40T Read-only Live Execution Gate",
            "",
            f"- Execute flag present: {str(report.get('execute_flag_present')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Started: {str(report.get('started')).lower()}",
            f"- Reason: {report.get('reason')}",
            f"- Timeout seconds: {report.get('timeout_seconds')}",
            f"- Max events: {report.get('max_events')}",
            "- Discord Gateway connected: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
        ]
    ) + "\n"
