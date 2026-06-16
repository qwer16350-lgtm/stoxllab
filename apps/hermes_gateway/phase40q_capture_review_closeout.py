"""Phase 40Q capture review and closeout parser."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from phase40p_readonly_capture_schema import ALLOWED_CAPTURE_FIELDS, FORBIDDEN_CAPTURE_FIELDS


VERSION_EMPTY = "phase40q_capture_review_closeout_no_capture_yet"
VERSION_PARSED = "phase40q_capture_review_closeout_redacted_capture_file"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _load_capture_events(capture_file: str | Path | None) -> tuple[bool, list[dict[str, Any]]]:
    if not capture_file:
        return False, []
    path = Path(capture_file)
    if not path.exists() or not path.is_file():
        return False, []
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return True, [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        events = data.get("events", [])
        if isinstance(events, list):
            return True, [item for item in events if isinstance(item, dict)]
        return True, [data]
    return True, []


def _safe_event(event: dict[str, Any]) -> dict[str, Any]:
    return {key: event.get(key) for key in ALLOWED_CAPTURE_FIELDS if key in event}


def build_phase40q_capture_review_closeout(capture_file: str | Path | None = None) -> dict[str, Any]:
    present, events = _load_capture_events(capture_file)
    safe_events = [_safe_event(event) for event in events]
    private_human = sum(1 for item in safe_events if item.get("channel_scope") == "private_test" and item.get("author_kind") == "human" and not item.get("is_self") and not item.get("is_bot"))
    self_count = sum(1 for item in safe_events if bool(item.get("is_self")))
    bot_count = sum(1 for item in safe_events if bool(item.get("is_bot")) or item.get("author_kind") == "bot")
    duplicate_count = sum(1 for item in safe_events if bool(item.get("is_duplicate")))
    public_team_count = sum(1 for item in safe_events if item.get("channel_scope") in {"public", "team"})
    report = {
        "report_type": "phase40q_capture_review_closeout",
        "version": VERSION_PARSED if present else VERSION_EMPTY,
        "report_only": True,
        "capture_file_present": present,
        "capture_review_completed": bool(present and safe_events),
        "live_capture_observed": bool(present and safe_events),
        "captured_event_count": len(safe_events),
        "private_test_human_message_count": private_human,
        "self_message_skipped_count": self_count,
        "bot_message_skipped_count": bot_count,
        "duplicate_message_skipped_count": duplicate_count,
        "public_team_blocked_count": public_team_count,
        "forbidden_fields_present": any(any(field in event for field in FORBIDDEN_CAPTURE_FIELDS) for event in events),
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_phase41_reply_runtime": False,
    }
    assert_phase40q_capture_review_closeout_safe(report)
    return report


def assert_phase40q_capture_review_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40Q closeout contains sensitive values.")
    for key in (
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_phase41_reply_runtime",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40Q unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40Q message_sent_count must remain 0.")


def render_phase40q_capture_review_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40Q Capture Review Closeout",
            "",
            "- Report only: true",
            f"- Capture file present: {str(report.get('capture_file_present')).lower()}",
            f"- Capture review completed: {str(report.get('capture_review_completed')).lower()}",
            f"- Live capture observed: {str(report.get('live_capture_observed')).lower()}",
            f"- Captured event count: {report.get('captured_event_count')}",
            f"- Private-test human message count: {report.get('private_test_human_message_count')}",
            "- Discord message sent: false",
            "- Ready for Phase 41 reply runtime: false",
        ]
    ) + "\n"
