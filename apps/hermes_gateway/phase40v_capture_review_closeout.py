"""Phase 40V hardened capture review closeout."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase40v_capture_review_closeout"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def classify_capture_review(capture: Mapping[str, Any]) -> str:
    if capture.get("raw_content_logged") or capture.get("capture_file_contains_raw_content"):
        return "invalid_raw_content_capture"
    if capture.get("raw_discord_ids_logged") or capture.get("capture_file_contains_raw_discord_ids"):
        return "invalid_raw_discord_id_capture"
    if capture.get("secret_values_logged") or capture.get("capture_file_contains_secret_values"):
        return "invalid_secret_capture"
    if capture.get("channel_scope") in {"public", "team", "public_blocked", "team_blocked"}:
        return "invalid_public_team_capture"
    if (
        capture.get("exit_reason") == "timeout"
        and int(capture.get("captured_event_count", 0) or 0) == 0
        and bool(capture.get("capture_file_written"))
    ):
        return "valid_no_event_timeout_capture"
    if capture.get("channel_scope") == "private_test_only" and capture.get("author_type") == "human":
        return "valid_private_test_human_message_capture"
    return "invalid_public_team_capture"


def build_phase40v_capture_review_closeout(capture: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = {
        "exit_reason": "timeout",
        "captured_event_count": 0,
        "capture_file_written": True,
        "capture_file_path_logged": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "channel_scope": "private_test_only",
        "author_type": "",
    }
    if capture:
        data.update(capture)
    classification = classify_capture_review(data)
    valid = classification in {"valid_no_event_timeout_capture", "valid_private_test_human_message_capture"}
    report = {
        "report_type": "phase40v_capture_review_closeout",
        "version": VERSION,
        "report_only": True,
        "capture_review_completed": True,
        "capture_classification": classification,
        "capture_valid": valid,
        "valid_no_event_timeout_capture": classification == "valid_no_event_timeout_capture",
        "valid_private_test_human_message_capture": classification == "valid_private_test_human_message_capture",
        "capture_file_written": bool(data.get("capture_file_written")),
        "capture_file_path_logged": False,
        "captured_event_count": int(data.get("captured_event_count", 0) or 0),
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "token_value_logged": False,
        "api_key_value_logged": False,
        "approval_phrase_value_logged": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "ready_for_phase40w_synthetic_replay": valid,
    }
    assert_phase40v_capture_review_closeout_safe(report)
    return report


def assert_phase40v_capture_review_closeout_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40V capture review contains sensitive values.")
    for key in (
        "capture_file_path_logged",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
        "token_value_logged",
        "api_key_value_logged",
        "approval_phrase_value_logged",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_called",
        "rag_called",
        "embedding_api_called",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40V unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40V message_sent_count must remain 0.")


def render_phase40v_capture_review_closeout_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40V Capture Review Closeout",
            "",
            f"- Capture classification: {report.get('capture_classification')}",
            f"- Capture valid: {str(report.get('capture_valid')).lower()}",
            "- Raw content/IDs/secrets logged: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
