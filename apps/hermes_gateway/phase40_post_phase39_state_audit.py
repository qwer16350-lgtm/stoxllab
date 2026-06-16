"""Phase 40A post-Phase39 state audit, report-only."""

from __future__ import annotations

import json
import re
from typing import Any

from phase39c_actual_send_closeout import build_phase39c_actual_send_closeout
from phase39c_no_repeat_send_lock import build_phase39c_no_repeat_send_lock


VERSION = "phase40_post_phase39_state_audit_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_post_phase39_state_audit(
    closeout: dict[str, Any] | None = None,
    no_repeat_lock: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_closeout = closeout or build_phase39c_actual_send_closeout()
    selected_lock = no_repeat_lock or build_phase39c_no_repeat_send_lock(selected_closeout)
    report = {
        "report_type": "phase40_post_phase39_state_audit",
        "version": VERSION,
        "report_only": True,
        "phase39_completed": True,
        "phase39b_actual_private_test_send_success": bool(selected_closeout.get("phase39b_actual_send_success")),
        "actual_discord_send_count_locked": int(selected_lock.get("actual_discord_send_count_locked", 0) or 0),
        "phase39c_closeout_completed": bool(selected_closeout.get("phase39c_closeout_completed")),
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "unattended_auto_reply_allowed": False,
        "additional_discord_send_called": False,
        "additional_discord_message_sent": False,
        "additional_message_sent_count": 0,
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
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "ready_for_phase40_private_test_runtime_readiness": True,
        "ready_for_live_runtime_execution": False,
    }
    assert_phase40_post_phase39_state_audit_safe(report)
    return report


def assert_phase40_post_phase39_state_audit_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40A audit contains sensitive values.")
    if report.get("actual_discord_send_count_locked") != 1:
        raise ValueError("Phase 40A requires Phase 39 actual send count locked to 1.")
    if not report.get("phase39_completed") or not report.get("phase39c_closeout_completed"):
        raise ValueError("Phase 40A requires completed Phase 39 closeout.")
    for key in (
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "unattended_auto_reply_allowed",
        "additional_discord_send_called",
        "additional_discord_message_sent",
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
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "ready_for_live_runtime_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40A unsafe flag is true: {key}")
    if int(report.get("additional_message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40A forbids additional sends.")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40A message_sent_count must remain 0.")


def render_phase40_post_phase39_state_audit_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40A Post-Phase39 State Audit",
            "",
            "- Report only: true",
            "- Phase 39 completed: true",
            "- Phase 39B actual private-test send success: true",
            "- Actual Discord send count locked: 1",
            "- Phase 40 additional send count: 0",
            "- Live runtime started: false",
            "- Ready for live runtime execution: false",
        ]
    ) + "\n"
