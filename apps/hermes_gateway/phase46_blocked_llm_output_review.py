"""Phase46 metadata-only review for the blocked Phase45 LLM output."""

from __future__ import annotations

import json
import re
from typing import Any

from actual_one_shot_llm_draft_call_closeout import build_actual_one_shot_llm_draft_call_closeout
from output_safety import build_output_safety_calibration_report


VERSION = "phase46_blocked_llm_output_review_metadata_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase46_blocked_llm_output_review(closeout: dict[str, Any] | None = None) -> dict[str, Any]:
    phase45 = closeout or build_actual_one_shot_llm_draft_call_closeout()
    output = phase45.get("output_safety", {}) if isinstance(phase45.get("output_safety"), dict) else {}
    calibration = build_output_safety_calibration_report()
    report = {
        "report_type": "phase46_blocked_llm_output_review",
        "version": VERSION,
        "review_available": True,
        "report_only": True,
        "metadata_only": True,
        "phase45_actual_llm_call_completed": bool(phase45.get("phase45_actual_llm_one_shot_completed")),
        "phase45_llm_call_count": int(phase45.get("phase45_actual_llm_call_count", 0) or 0),
        "phase45_repeat_llm_call_allowed": bool(phase45.get("phase45_ready_for_repeat_llm_call")),
        "phase45_no_repeat_lock_active": bool(phase45.get("phase45_actual_llm_one_shot_repeat_locked")),
        "output_safety_checked": bool(phase45.get("output_safety_checked")),
        "output_safety_blocked": bool(phase45.get("output_safety_blocked")),
        "blocked_reasons": list(output.get("blocked_reasons", [])),
        "safe_disclaimer_detected": bool(output.get("safe_disclaimer_detected")),
        "safe_disclaimer_reasons": list(output.get("safe_disclaimer_reasons", [])),
        "classifier_calibration_fixture_based_only": True,
        "classifier_negated_external_action_false_positive_count": int(calibration.get("negated_external_action_false_positive_count", 0) or 0),
        "classifier_positive_external_action_blocked_count": int(calibration.get("positive_external_action_blocked_count", 0) or 0),
        "human_review_only": True,
        "raw_output_included": False,
        "full_content_included": False,
        "discord_message_sent": False,
        "ready_for_retry": False,
        "automatic_retry_allowed": False,
        "automatic_send_allowed": False,
        "automatic_output_packet_creation_allowed": False,
        "retry_requires_new_manual_gate": True,
        "retry_requires_new_approval_policy": True,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "additional_llm_api_call": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase46_blocked_llm_output_review_safe(report)
    return report


def assert_phase46_blocked_llm_output_review_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase46 blocked output review contains sensitive values.")
    if not report.get("phase45_actual_llm_call_completed") or int(report.get("phase45_llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase46 review requires exactly one completed Phase45 LLM call.")
    if report.get("phase45_repeat_llm_call_allowed") or not report.get("phase45_no_repeat_lock_active"):
        raise ValueError("Phase46 review requires Phase45 no-repeat lock.")
    if not report.get("output_safety_checked") or not report.get("output_safety_blocked"):
        raise ValueError("Phase46 review requires blocked output safety state.")
    if "external_action_claim" not in report.get("blocked_reasons", []):
        raise ValueError("Phase46 review requires external_action_claim metadata.")
    if int(report.get("classifier_negated_external_action_false_positive_count", 0) or 0) != 0:
        raise ValueError("Phase46 classifier calibration has negated-action false positives.")
    for key in (
        "raw_output_included",
        "full_content_included",
        "discord_message_sent",
        "ready_for_retry",
        "automatic_retry_allowed",
        "automatic_send_allowed",
        "automatic_output_packet_creation_allowed",
        "llm_api_call_attempted",
        "llm_api_called",
        "additional_llm_api_call",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase46 blocked output review unsafe flag is true: {key}")


def render_phase46_blocked_llm_output_review_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase46 Blocked LLM Output Review",
            "",
            f"- Phase45 actual LLM call completed: {str(report.get('phase45_actual_llm_call_completed')).lower()}",
            f"- Phase45 LLM call count: {report.get('phase45_llm_call_count', 0)}",
            f"- Phase45 repeat LLM call allowed: {str(report.get('phase45_repeat_llm_call_allowed')).lower()}",
            f"- Output safety blocked: {str(report.get('output_safety_blocked')).lower()}",
            f"- Blocked reasons: {', '.join(report.get('blocked_reasons', []))}",
            f"- Safe disclaimer detected: {str(report.get('safe_disclaimer_detected')).lower()}",
            "- Raw output included: false",
            "- Full content included: false",
            "- Discord message sent: false",
            "- Ready for retry: false",
            "- Retry requires new manual gate: true",
        ]
    ) + "\n"
