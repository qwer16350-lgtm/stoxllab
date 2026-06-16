"""Phase 40X no-send reply decision dry-run."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from phase40w_synthetic_private_test_replay import build_synthetic_event


VERSION = "phase40x_reply_decision_dry_run"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def decide_would_reply(event: Mapping[str, Any]) -> tuple[bool, str]:
    if event.get("channel_scope") != "private_test_only":
        return False, "blocked_public_or_team_channel"
    if event.get("is_self"):
        return False, "blocked_self_message"
    if event.get("is_bot") or event.get("author_type") == "bot":
        return False, "blocked_bot_message"
    if event.get("is_duplicate"):
        return False, "blocked_duplicate_message"
    if event.get("author_type") != "human":
        return False, "blocked_non_human_author"
    return True, "private_test_human_message"


def build_phase40x_reply_decision_dry_run(event: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source = dict(event or build_synthetic_event())
    would_reply, reason = decide_would_reply(source)
    report = {
        "report_type": "phase40x_reply_decision_dry_run",
        "version": VERSION,
        "report_only": True,
        "input_source": "synthetic_redacted_fixture",
        "decision_reason": reason,
        "would_reply": bool(would_reply),
        "send_scope": "private_test_only" if would_reply else "blocked",
        "actual_send_allowed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_called": False,
        "llm_api_call_attempted": False,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "reply_payload_frozen": bool(would_reply),
        "reply_payload_preview": {
            "source": "deterministic_placeholder",
            "content_kind": "review_only_placeholder",
            "raw_content_logged": False,
        } if would_reply else {},
        "ready_for_phase41_preflight_gate": bool(would_reply),
        "ready_for_actual_reply_send": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }
    assert_phase40x_reply_decision_dry_run_safe(report)
    return report


def assert_phase40x_reply_decision_dry_run_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text):
        raise ValueError("Phase 40X reply dry-run contains sensitive values.")
    for key in (
        "actual_send_allowed",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_called",
        "llm_api_call_attempted",
        "rag_called",
        "embedding_api_called",
        "external_execution",
        "ready_for_actual_reply_send",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40X unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40X message_sent_count must remain 0.")


def render_phase40x_reply_decision_dry_run_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40X Reply Decision Dry-run",
            "",
            f"- Would reply: {str(report.get('would_reply')).lower()}",
            f"- Decision reason: {report.get('decision_reason')}",
            "- Actual send allowed: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
        ]
    ) + "\n"
