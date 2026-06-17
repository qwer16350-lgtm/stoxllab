"""Phase46 no-automatic-retry policy for blocked LLM output."""

from __future__ import annotations

import json
import re
from typing import Any

from phase46_blocked_llm_output_review import build_phase46_blocked_llm_output_review


VERSION = "phase46_llm_retry_policy_no_automatic_recall"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase46_llm_retry_policy(review: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = review or build_phase46_blocked_llm_output_review()
    report = {
        "report_type": "phase46_llm_retry_policy",
        "version": VERSION,
        "policy_available": True,
        "report_only": True,
        "phase45_actual_llm_call_completed": bool(selected.get("phase45_actual_llm_call_completed")),
        "phase45_llm_call_count": int(selected.get("phase45_llm_call_count", 0) or 0),
        "automatic_retry_allowed": False,
        "repeat_phase45_call_allowed": False,
        "retry_requires_new_manual_gate": True,
        "retry_requires_new_approval_phrase": True,
        "retry_requires_new_approval_policy": True,
        "retry_requires_cost_guard": True,
        "retry_requires_call_count_guard": True,
        "retry_requires_human_review": True,
        "discord_send_remains_disabled": True,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "additional_llm_api_call": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_output_included": False,
        "full_content_included": False,
        "ready_for_phase47_manual_gate_design": True,
    }
    assert_phase46_llm_retry_policy_safe(report)
    return report


def assert_phase46_llm_retry_policy_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase46 retry policy contains sensitive values.")
    if not report.get("phase45_actual_llm_call_completed") or int(report.get("phase45_llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase46 retry policy requires exactly one completed Phase45 LLM call.")
    for key in (
        "automatic_retry_allowed",
        "repeat_phase45_call_allowed",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "additional_llm_api_call",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "raw_output_included",
        "full_content_included",
    ):
        if report.get(key):
            raise ValueError(f"Phase46 retry policy unsafe flag is true: {key}")
    for key in (
        "retry_requires_new_manual_gate",
        "retry_requires_new_approval_phrase",
        "retry_requires_new_approval_policy",
        "retry_requires_cost_guard",
        "retry_requires_call_count_guard",
        "retry_requires_human_review",
        "discord_send_remains_disabled",
    ):
        if not report.get(key):
            raise ValueError(f"Phase46 retry policy required guard is false: {key}")


def render_phase46_llm_retry_policy_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase46 LLM Retry Policy",
            "",
            "- Automatic retry allowed: false",
            "- Repeat Phase45 call allowed: false",
            "- Retry requires new manual gate: true",
            "- Retry requires new approval phrase: true",
            "- Retry requires cost guard: true",
            "- Retry requires call-count guard: true",
            "- Discord send remains disabled: true",
            "- Additional LLM API call: false",
        ]
    ) + "\n"
