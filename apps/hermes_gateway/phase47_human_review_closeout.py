"""Phase47 human-review-only closeout for the blocked Phase45 LLM output."""

from __future__ import annotations

import json
import re
from typing import Any

from phase46_blocked_llm_output_review import build_phase46_blocked_llm_output_review


VERSION = "phase47_human_review_only_closeout"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase47_human_review_closeout(review: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = review or build_phase46_blocked_llm_output_review()
    report = {
        "report_type": "phase47_human_review_closeout",
        "version": VERSION,
        "closeout_available": True,
        "report_only": True,
        "metadata_only": True,
        "phase45_actual_llm_call_completed": bool(selected.get("phase45_actual_llm_call_completed")),
        "phase45_llm_call_count": int(selected.get("phase45_llm_call_count", 0) or 0),
        "phase45_repeat_llm_call_allowed": bool(selected.get("phase45_repeat_llm_call_allowed")),
        "phase45_no_repeat_lock_active": bool(selected.get("phase45_no_repeat_lock_active")),
        "output_safety_blocked": bool(selected.get("output_safety_blocked")),
        "blocked_reasons": list(selected.get("blocked_reasons", [])),
        "discord_message_sent": False,
        "human_review_required": True,
        "human_review_only": True,
        "automatic_retry_allowed": False,
        "automatic_send_allowed": False,
        "raw_output_included": False,
        "full_content_included": False,
        "retry_execution_available": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "additional_llm_api_call": False,
        "discord_api_send_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "next_options": [
            "Option A: human-review-only project closeout",
            "Option B: Phase48 new retry Manual Gate design",
            "Option C: Phase48 Discord send review gate design",
        ],
        "phase47_executes_option_b": False,
        "phase47_executes_option_c": False,
    }
    assert_phase47_human_review_closeout_safe(report)
    return report


def assert_phase47_human_review_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase47 human-review closeout contains sensitive values.")
    if not report.get("phase45_actual_llm_call_completed") or int(report.get("phase45_llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase47 closeout requires exactly one completed historical Phase45 LLM call.")
    if report.get("phase45_repeat_llm_call_allowed") or not report.get("phase45_no_repeat_lock_active"):
        raise ValueError("Phase47 closeout requires the Phase45 no-repeat lock.")
    if not report.get("output_safety_blocked"):
        raise ValueError("Phase47 closeout requires blocked output safety metadata.")
    if "external_action_claim" not in report.get("blocked_reasons", []):
        raise ValueError("Phase47 closeout requires external_action_claim metadata.")
    if not report.get("human_review_required") or not report.get("human_review_only"):
        raise ValueError("Phase47 closeout requires human-review-only state.")
    for key in (
        "discord_message_sent",
        "automatic_retry_allowed",
        "automatic_send_allowed",
        "raw_output_included",
        "full_content_included",
        "retry_execution_available",
        "llm_api_call_attempted",
        "llm_api_called",
        "additional_llm_api_call",
        "discord_api_send_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "phase47_executes_option_b",
        "phase47_executes_option_c",
    ):
        if report.get(key):
            raise ValueError(f"Phase47 human-review closeout unsafe flag is true: {key}")


def render_phase47_human_review_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase47 Human-Review Closeout",
            "",
            f"- Phase45 actual LLM call completed: {str(report.get('phase45_actual_llm_call_completed')).lower()}",
            f"- Phase45 LLM call count: {report.get('phase45_llm_call_count', 0)}",
            f"- Output safety blocked: {str(report.get('output_safety_blocked')).lower()}",
            "- Discord message sent: false",
            "- Human review required: true",
            "- Automatic retry allowed: false",
            "- Automatic send allowed: false",
            "- Raw output included: false",
            "- Full content included: false",
            "- Retry execution available: false",
            "- Option A: human-review-only project closeout",
            "- Option B: Phase48 new retry Manual Gate design",
            "- Option C: Phase48 Discord send review gate design",
        ]
    ) + "\n"
