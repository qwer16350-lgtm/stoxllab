"""Phase 40T-2 safe Discord login failure closeout.

This report is intentionally diagnostic-only: it records token presence and
login validity booleans without leaking token values, channel IDs, approval
phrases, raw Discord IDs, message content, or tracebacks.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase40t_discord_login_failure_closeout"
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\)|File \".+\", line \d+")


def _env_value_present(env: Mapping[str, str] | None, key: str) -> bool:
    if not env:
        return False
    return bool(str(env.get(key, "") or "").strip())


def classify_discord_login_failure(exc: BaseException | None = None, *, status: int | None = None) -> tuple[str, str]:
    name = exc.__class__.__name__ if exc is not None else "LoginFailure"
    message = str(exc or "").lower()
    status_code = status
    if status_code is None and hasattr(exc, "status"):
        try:
            status_code = int(getattr(exc, "status"))
        except (TypeError, ValueError):
            status_code = None
    if status_code == 401 or "401" in message or "unauthorized" in message or "improper token" in message:
        return name, "invalid_or_unauthorized_token"
    if name == "LoginFailure":
        return name, "invalid_or_unauthorized_token"
    if name == "TimeoutError":
        return name, "login_timeout"
    if name == "KeyboardInterrupt":
        return name, "manual_abort"
    return name, "discord_login_failed"


def build_phase40t_discord_login_failure_closeout(
    env: Mapping[str, str] | None = None,
    *,
    failure_type: str = "LoginFailure",
    failure_reason: str = "invalid_or_unauthorized_token",
    execute_flag_present: bool = True,
) -> dict[str, Any]:
    report = {
        "report_type": "phase40t_discord_login_failure_closeout",
        "version": VERSION,
        "mode": "private_test_readonly_live_execution",
        "execute_flag_present": bool(execute_flag_present),
        "blocked": True,
        "started": False,
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "login_attempted": True,
        "discord_login_succeeded": False,
        "discord_login_failure": True,
        "discord_login_failure_type": str(failure_type),
        "discord_login_failure_reason": str(failure_reason),
        "discord_token_present": _env_value_present(env, "DISCORD_BOT_TOKEN"),
        "discord_token_value_logged": False,
        "discord_token_valid": False,
        "private_test_channel_id_present": _env_value_present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_content_logged": False,
        "secret_values_logged": False,
        "traceback_logged": False,
        "traceback_included": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "send_messages_enabled": False,
        "private_test_reply_enabled": False,
        "reply_mode_readonly_private_test_only": True,
        "retry_attempted": False,
        "automatic_retry_allowed": False,
        "repeat_send_allowed": False,
        "unattended_auto_reply_allowed": False,
        "llm_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "capture_file_written": False,
        "ready_for_capture_closeout": False,
        "ready_for_phase41_reply_runtime": False,
        "ready_for_reply_send": False,
        "operator_action_required": "refresh_or_correct_discord_bot_token",
    }
    assert_phase40t_discord_login_failure_closeout_safe(report)
    return report


def build_phase40t_discord_login_failure_closeout_from_exception(
    env: Mapping[str, str] | None,
    exc: BaseException,
    *,
    execute_flag_present: bool = True,
) -> dict[str, Any]:
    failure_type, failure_reason = classify_discord_login_failure(exc)
    return build_phase40t_discord_login_failure_closeout(
        env=env,
        failure_type=failure_type,
        failure_reason=failure_reason,
        execute_flag_present=execute_flag_present,
    )


def assert_phase40t_discord_login_failure_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text) or TRACEBACK_RE.search(text):
        raise ValueError("Phase 40T login failure closeout contains unsafe diagnostic values.")
    for key in (
        "started",
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_login_succeeded",
        "discord_token_value_logged",
        "discord_token_valid",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_content_logged",
        "secret_values_logged",
        "traceback_logged",
        "traceback_included",
        "discord_api_send_called",
        "discord_message_sent",
        "send_messages_enabled",
        "private_test_reply_enabled",
        "retry_attempted",
        "automatic_retry_allowed",
        "repeat_send_allowed",
        "unattended_auto_reply_allowed",
        "llm_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "capture_file_written",
        "ready_for_capture_closeout",
        "ready_for_phase41_reply_runtime",
        "ready_for_reply_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40T login failure closeout unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40T login failure closeout message_sent_count must remain 0.")


def render_phase40t_discord_login_failure_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40T Discord Login Failure Closeout",
            "",
            f"- Login attempted: {str(report.get('login_attempted')).lower()}",
            f"- Discord login succeeded: {str(report.get('discord_login_succeeded')).lower()}",
            f"- Failure type: {report.get('discord_login_failure_type')}",
            f"- Failure reason: {report.get('discord_login_failure_reason')}",
            f"- Token present: {str(report.get('discord_token_present')).lower()}",
            f"- Token valid: {str(report.get('discord_token_valid')).lower()}",
            "- Token value logged: false",
            "- Private test channel ID value logged: false",
            "- Traceback included: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
            f"- Operator action required: {report.get('operator_action_required')}",
        ]
    ) + "\n"
