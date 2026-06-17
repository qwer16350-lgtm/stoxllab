"""Phase48A operator handoff packet for human-review-only closeout."""

from __future__ import annotations

import json
import re
from typing import Any

from phase48a_human_review_final_closeout import build_phase48a_human_review_final_closeout


VERSION = "phase48a_operator_handoff_packet_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase48a_operator_handoff_packet(closeout: dict[str, Any] | None = None) -> dict[str, Any]:
    final = closeout or build_phase48a_human_review_final_closeout()
    report = {
        "report_type": "phase48a_operator_handoff_packet",
        "version": VERSION,
        "handoff_packet_available": True,
        "report_only": True,
        "metadata_only": True,
        "completed_once": {
            "phase41b_private_test_reply": bool(final.get("actual_discord_reply_completed_once")),
            "phase42_supervised_private_test_session": bool(final.get("actual_supervised_discord_session_completed_once")),
            "phase45_llm_openrouter_call": bool(final.get("actual_llm_call_completed_once")),
        },
        "counts": {
            "phase41b_reply_count": int(final.get("phase41b_reply_count", 0) or 0),
            "phase42_message_sent_count": int(final.get("phase42_message_sent_count", 0) or 0),
            "phase45_llm_call_count": int(final.get("phase45_llm_call_count", 0) or 0),
            "discord_send_after_llm_count": 0,
        },
        "blocked_disabled": {
            "phase41b_repeat_allowed": False,
            "phase42_repeat_allowed": False,
            "phase45_repeat_llm_call_allowed": False,
            "automatic_retry_allowed": False,
            "automatic_discord_send_allowed": False,
            "unattended_auto_reply_allowed": False,
            "raw_output_dump_allowed": False,
            "production_unattended_mode_ready": False,
        },
        "forbidden_behaviors": [
            "Phase45 repeat LLM call",
            "blocked output auto retry",
            "blocked output auto Discord send",
            "unattended auto reply",
            "raw output dump",
            "production unattended mode",
        ],
        "next_decision_options": [
            "Option A: archive / human review only finish",
            "Option B: Phase48B retry Manual Gate design",
            "Option C: Phase48C Discord send review gate design",
            "Option D: Phase49 production-readiness audit",
        ],
        "phase48a_implements_option_b": False,
        "phase48a_implements_option_c": False,
        "phase48a_implements_option_d": False,
        "manual_gate_required_conditions": [
            "new explicit phase",
            "new explicit Manual Gate",
            "new approval policy",
            "new approval phrase",
            "cost guard",
            "call-count guard",
            "Discord disabled by default",
            "no automatic send",
        ],
        "external_action_freeze_active": bool(final.get("external_action_freeze_active")),
        "future_external_action_requires_new_manual_gate": bool(final.get("future_external_action_requires_new_manual_gate")),
        "future_external_action_requires_new_approval_policy": bool(final.get("future_external_action_requires_new_approval_policy")),
        "blocked_llm_output_raw_included": False,
        "full_content_included": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "additional_llm_api_call": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase48a_operator_handoff_packet_safe(report)
    return report


def assert_phase48a_operator_handoff_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase48A operator handoff contains sensitive values.")
    completed = report.get("completed_once", {})
    counts = report.get("counts", {})
    if not all(bool(completed.get(key)) for key in ("phase41b_private_test_reply", "phase42_supervised_private_test_session", "phase45_llm_openrouter_call")):
        raise ValueError("Phase48A operator handoff requires all exactly-once historical completions.")
    if int(counts.get("phase41b_reply_count", 0) or 0) != 1 or int(counts.get("phase42_message_sent_count", 0) or 0) != 1 or int(counts.get("phase45_llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase48A operator handoff requires exactly-once counts.")
    blocked = report.get("blocked_disabled", {})
    for key in (
        "phase41b_repeat_allowed",
        "phase42_repeat_allowed",
        "phase45_repeat_llm_call_allowed",
        "automatic_retry_allowed",
        "automatic_discord_send_allowed",
        "unattended_auto_reply_allowed",
        "raw_output_dump_allowed",
        "production_unattended_mode_ready",
    ):
        if blocked.get(key):
            raise ValueError(f"Phase48A operator handoff unsafe blocked flag is true: {key}")
    for key in (
        "phase48a_implements_option_b",
        "phase48a_implements_option_c",
        "phase48a_implements_option_d",
        "blocked_llm_output_raw_included",
        "full_content_included",
        "llm_api_call_attempted",
        "llm_api_called",
        "additional_llm_api_call",
        "discord_api_send_called",
        "discord_message_sent",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase48A operator handoff unsafe flag is true: {key}")
    if not report.get("external_action_freeze_active") or not report.get("future_external_action_requires_new_manual_gate"):
        raise ValueError("Phase48A operator handoff requires external action freeze and future manual gate.")


def render_phase48a_operator_handoff_packet_markdown(report: dict[str, Any]) -> str:
    counts = report.get("counts", {})
    return "\n".join(
        [
            "# STOXL Phase48A Operator Handoff Packet",
            "",
            f"- Phase41B reply count: {counts.get('phase41b_reply_count', 0)}",
            f"- Phase42 message sent count: {counts.get('phase42_message_sent_count', 0)}",
            f"- Phase45 LLM call count: {counts.get('phase45_llm_call_count', 0)}",
            "- Phase45 repeat LLM call forbidden: true",
            "- Blocked output auto retry forbidden: true",
            "- Blocked output auto Discord send forbidden: true",
            "- Unattended auto reply forbidden: true",
            "- Raw output dump forbidden: true",
            "- Production unattended mode ready: false",
            "- Future external action requires new Manual Gate: true",
        ]
    ) + "\n"
