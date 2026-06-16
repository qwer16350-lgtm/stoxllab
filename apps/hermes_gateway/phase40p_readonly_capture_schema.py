"""Phase 40P read-only capture schema and redaction policy."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase40p_readonly_capture_schema_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


ALLOWED_CAPTURE_FIELDS = [
    "event_id_hash",
    "message_id_hash",
    "channel_scope",
    "author_kind",
    "is_self",
    "is_bot",
    "is_duplicate",
    "decision",
    "timestamp_iso",
]
FORBIDDEN_CAPTURE_FIELDS = [
    "raw_message_content",
    "raw_author_id",
    "raw_channel_id",
    "discord_token",
    "api_key",
    "approval_phrase",
]


def build_phase40p_readonly_capture_schema() -> dict[str, Any]:
    report = {
        "report_type": "phase40p_readonly_capture_schema",
        "version": VERSION,
        "report_only": True,
        "capture_schema_available": True,
        "capture_file_required_for_closeout": True,
        "capture_file_written_by_codex": False,
        "allowed_capture_fields": ALLOWED_CAPTURE_FIELDS,
        "forbidden_capture_fields": FORBIDDEN_CAPTURE_FIELDS,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase40p_readonly_capture_schema_safe(report)
    return report


def assert_phase40p_readonly_capture_schema_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40P capture schema contains sensitive values.")
    if not report.get("capture_schema_available") or not report.get("capture_file_required_for_closeout"):
        raise ValueError("Phase 40P capture schema must be available and required for closeout.")
    if not set(FORBIDDEN_CAPTURE_FIELDS).isdisjoint(set(report.get("allowed_capture_fields", []))):
        raise ValueError("Phase 40P forbidden capture fields cannot be allowed.")
    for key in (
        "capture_file_written_by_codex",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
        "live_runtime_started",
        "discord_gateway_connected",
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
            raise ValueError(f"Phase 40P unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40P message_sent_count must remain 0.")


def render_phase40p_readonly_capture_schema_markdown(report: dict[str, Any]) -> str:
    allowed = "\n".join(f"- `{item}`" for item in report.get("allowed_capture_fields", []))
    forbidden = "\n".join(f"- `{item}`" for item in report.get("forbidden_capture_fields", []))
    return "\n".join(
        [
            "# STOXL Phase 40P Read-only Capture Schema",
            "",
            "- Report only: true",
            "- Capture schema available: true",
            "- Capture file required for closeout: true",
            "- Capture file written by Codex: false",
            "",
            "## Allowed Fields",
            allowed,
            "",
            "## Forbidden Fields",
            forbidden,
        ]
    ) + "\n"
