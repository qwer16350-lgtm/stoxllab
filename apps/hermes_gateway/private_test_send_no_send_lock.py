"""Phase 37F private-test send no-send lock."""

from __future__ import annotations

import json
import re
from typing import Any

from actual_private_test_send_manual_preflight import build_actual_private_test_send_manual_preflight
from mock_private_test_send_rehearsal import build_mock_private_test_send_rehearsal


VERSION = "phase37f_private_test_send_no_send_lock"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_private_test_send_no_send_lock(
    preflight: dict[str, Any] | None = None,
    rehearsal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_preflight = preflight or build_actual_private_test_send_manual_preflight()
    selected_rehearsal = rehearsal or build_mock_private_test_send_rehearsal(selected_preflight)
    report = {
        "report_type": "private_test_send_no_send_lock",
        "version": VERSION,
        "no_send_lock_available": True,
        "report_only": True,
        "source_phase37d_manual_preflight_available": bool(selected_preflight.get("preflight_available")),
        "source_phase37e_mock_rehearsal_available": bool(selected_rehearsal.get("mock_rehearsal_available")),
        "mock_send_rehearsal_count_locked": int(selected_rehearsal.get("mock_send_rehearsal_count", 0) or 0),
        "actual_discord_send_count_locked": int(selected_rehearsal.get("actual_message_sent_count", 0) or 0),
        "actual_discord_api_send_called": bool(selected_rehearsal.get("actual_discord_api_send_called")),
        "actual_discord_message_sent": bool(selected_rehearsal.get("actual_discord_message_sent")),
        "actual_message_sent_count": int(selected_rehearsal.get("actual_message_sent_count", 0) or 0),
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "ready_for_actual_private_test_send": False,
        "ready_for_phase38_actual_private_test_send_path": False,
        "ready_for_discord_send": False,
        "public_team_send_forbidden": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "full_content_included": False,
        "phase37f_no_send_lock_passed": False,
        "phase38_not_started": True,
        "requires_explicit_user_approval_for_phase38": True,
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
    report["phase37f_no_send_lock_passed"] = _passes_lock(report)
    assert_private_test_send_no_send_lock_safe(report)
    return report


def _passes_lock(report: dict[str, Any]) -> bool:
    return bool(
        report.get("source_phase37d_manual_preflight_available")
        and report.get("source_phase37e_mock_rehearsal_available")
        and int(report.get("mock_send_rehearsal_count_locked", 0) or 0) == 1
        and int(report.get("actual_discord_send_count_locked", 0) or 0) == 0
        and not report.get("actual_discord_api_send_called")
        and not report.get("actual_discord_message_sent")
        and int(report.get("actual_message_sent_count", 0) or 0) == 0
        and not report.get("ready_for_actual_private_test_send")
        and not report.get("ready_for_phase38_actual_private_test_send_path")
        and not report.get("ready_for_discord_send")
        and report.get("public_team_send_forbidden")
        and not report.get("unattended_auto_reply_allowed")
        and not report.get("embedding_api_called")
        and not report.get("vector_index_created")
        and not report.get("external_execution")
        and report.get("phase38_not_started")
        and report.get("requires_explicit_user_approval_for_phase38")
    )


def assert_private_test_send_no_send_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 37F no-send lock contains sensitive values.")
    if not report.get("phase37f_no_send_lock_passed"):
        raise ValueError("Phase 37F no-send lock did not pass.")
    if int(report.get("mock_send_rehearsal_count_locked", 0) or 0) != 1:
        raise ValueError("Phase 37F mock rehearsal count must be 1.")
    if int(report.get("actual_discord_send_count_locked", 0) or 0) != 0:
        raise ValueError("Phase 37F actual Discord send count must be 0.")
    for key in (
        "actual_discord_api_send_called",
        "actual_discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_live_runtime_executed",
        "ready_for_actual_private_test_send",
        "ready_for_phase38_actual_private_test_send_path",
        "ready_for_discord_send",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "full_content_included",
    ):
        if report.get(key):
            raise ValueError(f"Phase 37F unsafe flag is true: {key}")


def render_private_test_send_no_send_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Private-test Send No-send Lock",
            "",
            f"- No-send lock available: {str(report.get('no_send_lock_available')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            f"- Mock send rehearsal count locked: {report.get('mock_send_rehearsal_count_locked')}",
            f"- Actual Discord send count locked: {report.get('actual_discord_send_count_locked')}",
            "- Actual Discord message sent: false",
            "- Ready for Phase 38 actual private-test send path: false",
            "- Ready for Discord send: false",
            f"- Phase 37F no-send lock passed: {str(report.get('phase37f_no_send_lock_passed')).lower()}",
            "- Phase 38 not started: true",
            "- Requires explicit user approval for Phase 38: true",
        ]
    ) + "\n"
