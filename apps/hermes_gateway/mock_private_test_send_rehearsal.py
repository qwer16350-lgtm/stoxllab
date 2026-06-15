"""Phase 37E mock private-test send rehearsal, no API send."""

from __future__ import annotations

import json
import re
from typing import Any

from actual_private_test_send_manual_preflight import build_actual_private_test_send_manual_preflight


VERSION = "phase37e_mock_private_test_send_rehearsal_no_api_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_mock_private_test_send_rehearsal(preflight: dict[str, Any] | None = None, *, scope: str = "private_test_only") -> dict[str, Any]:
    selected = preflight or build_actual_private_test_send_manual_preflight()
    report = {
        "report_type": "mock_private_test_send_rehearsal",
        "version": VERSION,
        "mock_rehearsal_available": True,
        "report_only": True,
        "source_phase37d_manual_preflight_available": bool(selected.get("preflight_available")),
        "private_test_scope_only": scope == "private_test_only",
        "would_send_payload_created": True,
        "would_send_payload_scope": scope,
        "would_send_review_only": True,
        "would_send_preview": "Review-only private-test send rehearsal payload. No external action has been taken.",
        "would_send_external_action_claim": False,
        "would_send_full_content_included": False,
        "mock_send_rehearsal_count": 1,
        "actual_discord_api_send_called": False,
        "actual_discord_message_sent": False,
        "actual_message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "approval_phrase_value_logged": False,
        "full_content_included": False,
        "ready_for_phase37f_no_send_lock": True,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "discord_token_value_logged": False,
            "private_test_channel_id_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "full_content_included": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "discord_message_sent": False,
        },
    }
    assert_mock_private_test_send_rehearsal_safe(report)
    return report


def assert_mock_private_test_send_rehearsal_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 37E mock send rehearsal contains sensitive values.")
    if not report.get("private_test_scope_only") or report.get("would_send_payload_scope") != "private_test_only":
        raise ValueError("Phase 37E mock send rehearsal must remain private-test only.")
    if int(report.get("mock_send_rehearsal_count", 0) or 0) != 1:
        raise ValueError("Phase 37E mock send rehearsal count must be 1.")
    if int(report.get("actual_message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 37E actual message sent count must be 0.")
    for key in (
        "actual_discord_api_send_called",
        "actual_discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_live_runtime_executed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "approval_phrase_value_logged",
        "full_content_included",
        "would_send_external_action_claim",
        "would_send_full_content_included",
        "ready_for_actual_private_test_send",
        "ready_for_discord_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 37E unsafe flag is true: {key}")


def render_mock_private_test_send_rehearsal_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Mock Private-test Send Rehearsal",
            "",
            f"- Mock rehearsal available: {str(report.get('mock_rehearsal_available')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            "- Private-test scope only: true",
            f"- Mock send rehearsal count: {report.get('mock_send_rehearsal_count')}",
            "- Actual Discord API send called: false",
            "- Actual Discord message sent: false",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
        ]
    ) + "\n"
