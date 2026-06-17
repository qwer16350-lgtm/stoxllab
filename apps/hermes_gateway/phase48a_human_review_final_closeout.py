"""Phase48A human-review-only final closeout with external action freeze."""

from __future__ import annotations

import json
import re
from typing import Any

from phase41c_actual_reply_closeout import build_phase41c_actual_reply_closeout
from phase42_actual_session_closeout import build_phase42_actual_session_closeout
from phase47_human_review_closeout import build_phase47_human_review_closeout


VERSION = "phase48a_human_review_final_closeout_external_action_freeze"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase48a_human_review_final_closeout(
    phase41c: dict[str, Any] | None = None,
    phase42: dict[str, Any] | None = None,
    phase47: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reply = phase41c or build_phase41c_actual_reply_closeout()
    session = phase42 or build_phase42_actual_session_closeout()
    closeout = phase47 or build_phase47_human_review_closeout()
    report = {
        "report_type": "phase48a_human_review_final_closeout",
        "version": VERSION,
        "final_closeout_available": True,
        "report_only": True,
        "metadata_only": True,
        "final_closeout_mode": "human_review_only",
        "external_action_freeze_active": True,
        "phase41b_private_test_reply_completed": bool(reply.get("actual_private_test_reply_verified")),
        "phase41b_reply_count": int(reply.get("message_sent_count", 0) or 0),
        "actual_discord_reply_completed_once": bool(reply.get("actual_private_test_reply_verified")) and int(reply.get("message_sent_count", 0) or 0) == 1,
        "phase42_supervised_session_completed": bool(session.get("phase42_actual_supervised_private_test_session_succeeded")),
        "phase42_message_sent_count": int(session.get("message_sent_count", 0) or 0),
        "actual_supervised_discord_session_completed_once": bool(session.get("phase42_actual_supervised_private_test_session_succeeded")) and int(session.get("message_sent_count", 0) or 0) == 1,
        "phase45_actual_llm_call_completed": bool(closeout.get("phase45_actual_llm_call_completed")),
        "phase45_llm_call_count": int(closeout.get("phase45_llm_call_count", 0) or 0),
        "actual_llm_call_completed_once": bool(closeout.get("phase45_actual_llm_call_completed")) and int(closeout.get("phase45_llm_call_count", 0) or 0) == 1,
        "discord_message_sent_after_llm": False,
        "discord_send_after_llm": False,
        "phase45_output_safety_blocked": bool(closeout.get("output_safety_blocked")),
        "blocked_llm_output_raw_included": False,
        "raw_output_included": False,
        "full_content_included": False,
        "phase41b_repeat_allowed": False,
        "phase42_repeat_allowed": False,
        "phase45_repeat_llm_call_allowed": False,
        "automatic_retry_allowed": False,
        "automatic_discord_send_allowed": False,
        "automatic_send_allowed": False,
        "unattended_auto_reply_allowed": False,
        "future_external_action_requires_new_manual_gate": True,
        "future_external_action_requires_new_approval_policy": True,
        "ready_for_production_unattended_mode": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "additional_llm_api_call": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "option_a_archive_human_review_only_finish": True,
        "option_b_phase48b_retry_manual_gate_design_implemented": False,
        "option_c_phase48c_discord_send_review_gate_design_implemented": False,
        "option_d_phase49_production_readiness_audit_implemented": False,
    }
    assert_phase48a_human_review_final_closeout_safe(report)
    return report


def assert_phase48a_human_review_final_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase48A final closeout contains sensitive values.")
    if not report.get("actual_discord_reply_completed_once") or int(report.get("phase41b_reply_count", 0) or 0) != 1:
        raise ValueError("Phase48A requires Phase41B/41C exactly-once reply closeout.")
    if not report.get("actual_supervised_discord_session_completed_once") or int(report.get("phase42_message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase48A requires Phase42 exactly-once supervised session closeout.")
    if not report.get("actual_llm_call_completed_once") or int(report.get("phase45_llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase48A requires Phase45 exactly-once LLM closeout.")
    if not report.get("phase45_output_safety_blocked"):
        raise ValueError("Phase48A requires blocked Phase45 output safety state.")
    for key in (
        "discord_message_sent_after_llm",
        "discord_send_after_llm",
        "blocked_llm_output_raw_included",
        "raw_output_included",
        "full_content_included",
        "phase41b_repeat_allowed",
        "phase42_repeat_allowed",
        "phase45_repeat_llm_call_allowed",
        "automatic_retry_allowed",
        "automatic_discord_send_allowed",
        "automatic_send_allowed",
        "unattended_auto_reply_allowed",
        "ready_for_production_unattended_mode",
        "llm_api_call_attempted",
        "llm_api_called",
        "additional_llm_api_call",
        "discord_api_send_called",
        "discord_message_sent",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "option_b_phase48b_retry_manual_gate_design_implemented",
        "option_c_phase48c_discord_send_review_gate_design_implemented",
        "option_d_phase49_production_readiness_audit_implemented",
    ):
        if report.get(key):
            raise ValueError(f"Phase48A final closeout unsafe flag is true: {key}")
    for key in (
        "external_action_freeze_active",
        "future_external_action_requires_new_manual_gate",
        "future_external_action_requires_new_approval_policy",
    ):
        if not report.get(key):
            raise ValueError(f"Phase48A final closeout required guard is false: {key}")


def render_phase48a_human_review_final_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase48A Human-Review Final Closeout",
            "",
            "- Final closeout mode: human_review_only",
            "- External action freeze active: true",
            f"- Phase41B reply count: {report.get('phase41b_reply_count', 0)}",
            f"- Phase42 message sent count: {report.get('phase42_message_sent_count', 0)}",
            f"- Phase45 LLM call count: {report.get('phase45_llm_call_count', 0)}",
            "- Discord send after LLM: false",
            "- Phase45 output safety blocked: true",
            "- Blocked LLM output raw included: false",
            "- Automatic retry allowed: false",
            "- Automatic Discord send allowed: false",
            "- Unattended auto reply allowed: false",
            "- Production unattended mode ready: false",
        ]
    ) + "\n"
