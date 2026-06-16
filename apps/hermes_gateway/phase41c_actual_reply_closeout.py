"""Phase 41C actual private-test reply closeout parser scaffold."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase41c_actual_private_test_reply_closeout_safe_prep"
_SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|api[_ -]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
_LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def build_phase41c_actual_reply_closeout(result: Mapping[str, Any] | None = None) -> dict[str, Any]:
    result = result or {}
    count = int(result.get("message_sent_count", 0) or 0)
    channel_scope = str(result.get("sent_channel_scope", "none") or "none")
    repeat_attempted = bool(result.get("repeat_send_attempted"))
    self_loop = bool(result.get("self_loop_message"))
    bot_message = bool(result.get("bot_message"))
    duplicate = bool(result.get("duplicate_message"))
    single_private_success = count == 1 and channel_scope == "private_test" and not repeat_attempted
    no_send = count == 0
    failure = count > 1 or channel_scope in {"public", "team"} or repeat_attempted
    report = {
        "report_type": "phase41c_actual_private_test_reply_closeout",
        "version": VERSION,
        "actual_private_test_reply_verified": single_private_success,
        "no_send_closeout": no_send,
        "failure": failure,
        "message_sent_count": count,
        "sent_channel_scope": channel_scope if channel_scope in {"none", "private_test", "public", "team"} else "redacted",
        "no_repeat_lock_consumed": single_private_success,
        "repeat_send_blocked": True,
        "ready_for_repeat_send": False,
        "ready_for_supervised_session": single_private_success,
        "self_loop_ignored": self_loop,
        "bot_message_ignored": bot_message,
        "duplicate_message_ignored": duplicate,
        "public_team_blocked": channel_scope not in {"public", "team"},
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "raw_discord_ids_logged": False,
        "raw_message_content_logged": False,
        "secret_values_logged": False,
    }
    assert_phase41c_closeout_safe(report)
    return report


def assert_phase41c_closeout_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if _SECRET_RE.search(text) or _LONG_ID_RE.search(text):
        raise ValueError("Phase 41C closeout contains a sensitive value.")
    if report.get("ready_for_repeat_send"):
        raise ValueError("Phase 41C closeout must not allow repeat send.")
    if report.get("sent_channel_scope") in {"public", "team"} and not report.get("failure"):
        raise ValueError("Phase 41C must fail public/team sends.")


def render_phase41c_actual_reply_closeout_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 41C Actual Reply Closeout",
            "",
            f"- Actual private-test reply verified: {str(report.get('actual_private_test_reply_verified')).lower()}",
            f"- Message sent count: {report.get('message_sent_count')}",
            f"- Repeat send blocked: {str(report.get('repeat_send_blocked')).lower()}",
            f"- Ready for supervised session: {str(report.get('ready_for_supervised_session')).lower()}",
        ]
    ) + "\n"
