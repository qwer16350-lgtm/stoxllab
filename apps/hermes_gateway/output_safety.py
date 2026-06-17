"""Phase46 output-safety calibration helpers.

Report-only helpers for fixture-based classifier checks. This module never
calls LLM providers, Discord, RAG, embeddings, or external systems.
"""

from __future__ import annotations

import json
import re
from typing import Any

from llm_safety_policy import build_llm_safety_policy, check_llm_output_allowed


VERSION = "phase46_output_safety_calibration"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


NEGATED_EXTERNAL_ACTION_FIXTURES = [
    "This is a review-only draft. No external action has been taken.",
    "Review-only draft. Not sent, not published, and not approved.",
    "No final publishing has been made.",
    "No approval has been granted.",
    "No email has been sent.",
    "Nothing has been published, submitted, sent, uploaded, approved, confirmed, or externally delivered.",
]

POSITIVE_EXTERNAL_ACTION_FIXTURES = [
    "External action has been taken.",
    "I took external action.",
    "This is approved.",
    "I sent the email.",
]


def check_output_safety_fixture(text: str) -> dict[str, Any]:
    policy = build_llm_safety_policy({})
    decision = check_llm_output_allowed(text, policy)
    return {
        "report_type": "phase46_output_safety_fixture_decision",
        "version": VERSION,
        "allowed": bool(decision.get("allowed")),
        "blocked": bool(decision.get("blocked")),
        "blocked_reasons": list(decision.get("blocked_reasons", [])),
        "safe_disclaimer_detected": bool(decision.get("safe_disclaimer_detected")),
        "safe_disclaimer_reasons": list(decision.get("safe_disclaimer_reasons", [])),
        "raw_output_included": False,
        "full_content_included": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }


def build_output_safety_calibration_report() -> dict[str, Any]:
    negated = [check_output_safety_fixture(text) for text in NEGATED_EXTERNAL_ACTION_FIXTURES]
    positive = [check_output_safety_fixture(text) for text in POSITIVE_EXTERNAL_ACTION_FIXTURES]
    report = {
        "report_type": "phase46_output_safety_calibration",
        "version": VERSION,
        "fixture_based_only": True,
        "negated_external_action_fixture_count": len(negated),
        "positive_external_action_fixture_count": len(positive),
        "negated_external_action_false_positive_count": sum(1 for item in negated if item["blocked"]),
        "positive_external_action_blocked_count": sum(1 for item in positive if item["blocked"]),
        "negated_fixture_results": negated,
        "positive_fixture_results": positive,
        "raw_output_included": False,
        "full_content_included": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_output_safety_report_safe(report)
    return report


def assert_output_safety_report_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Output safety calibration contains sensitive values.")
    for key in (
        "raw_output_included",
        "full_content_included",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_message_sent",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Output safety calibration unsafe flag is true: {key}")
    if int(report.get("negated_external_action_false_positive_count", 0) or 0) != 0:
        raise ValueError("Negated external-action fixtures must not be blocked.")


def render_output_safety_calibration_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase46 Output Safety Calibration",
            "",
            f"- Fixture based only: {str(report.get('fixture_based_only')).lower()}",
            f"- Negated fixture false positives: {report.get('negated_external_action_false_positive_count', 0)}",
            f"- Positive fixture blocked count: {report.get('positive_external_action_blocked_count', 0)}",
            "- Raw output included: false",
            "- Full content included: false",
            "- LLM API called: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
