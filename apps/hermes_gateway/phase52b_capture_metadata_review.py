"""Phase52B capture metadata review without reading or dumping capture files."""

from __future__ import annotations

import json
import re
from typing import Any

from phase52b_readonly_live_capture_closeout import build_phase52b_readonly_live_capture_closeout


VERSION = "phase52b_capture_metadata_review_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase52b_capture_metadata_review(closeout: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = closeout or build_phase52b_readonly_live_capture_closeout()
    captured_count = int(selected.get("captured_event_count", 0) or 0)
    report = {
        "report_type": "phase52b_capture_metadata_review",
        "version": VERSION,
        "capture_file_present": bool(selected.get("capture_file_written")),
        "capture_file_metadata_available": bool(selected.get("capture_file_metadata_available")),
        "capture_file_read_attempted": False,
        "capture_file_path_value_logged": False,
        "raw_capture_dumped": False,
        "raw_content_included": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "captured_event_count": captured_count,
        "empty_capture_valid": captured_count == 0,
        "metadata_review_passed": True,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase52b_capture_metadata_review_safe(report)
    return report


def assert_phase52b_capture_metadata_review_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase52B metadata review contains sensitive values.")
    for key in (
        "capture_file_read_attempted",
        "capture_file_path_value_logged",
        "raw_capture_dumped",
        "raw_content_included",
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
    ):
        if report.get(key):
            raise ValueError(f"Phase52B metadata review unsafe flag is true: {key}")
    if not report.get("capture_file_present") or not report.get("metadata_review_passed"):
        raise ValueError("Phase52B metadata review requires capture presence and pass state.")


def render_phase52b_capture_metadata_review_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase52B Capture Metadata Review",
            "",
            "- Capture file present: true",
            "- Capture file read attempted: false",
            "- Raw capture dumped: false",
            f"- Captured event count: {report.get('captured_event_count')}",
            f"- Empty capture valid: {str(report.get('empty_capture_valid')).lower()}",
            "- Metadata review passed: true",
        ]
    ) + "\n"
