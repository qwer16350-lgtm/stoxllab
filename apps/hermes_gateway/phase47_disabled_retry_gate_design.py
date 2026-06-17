"""Phase47 disabled retry gate design packet.

This packet documents the future retry gate shape only. It does not expose a
retry execution path or perform any provider, Discord, RAG, or vector action.
"""

from __future__ import annotations

import json
import re
from typing import Any

from phase47_human_review_closeout import build_phase47_human_review_closeout


VERSION = "phase47_disabled_retry_gate_design_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase47_disabled_retry_gate_design(closeout: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = closeout or build_phase47_human_review_closeout()
    report = {
        "report_type": "phase47_disabled_retry_gate_design",
        "version": VERSION,
        "design_packet_available": True,
        "report_only": True,
        "design_docs_only": True,
        "blocked_report_only": True,
        "phase45_actual_llm_call_completed": bool(selected.get("phase45_actual_llm_call_completed")),
        "phase45_llm_call_count": int(selected.get("phase45_llm_call_count", 0) or 0),
        "output_safety_blocked": bool(selected.get("output_safety_blocked")),
        "human_review_required": bool(selected.get("human_review_required")),
        "retry_gate_implemented": False,
        "retry_execution_available": False,
        "automatic_retry_allowed": False,
        "manual_retry_requires_new_phase": True,
        "manual_retry_requires_new_manual_gate": True,
        "manual_retry_requires_new_approval_phrase": True,
        "manual_retry_requires_cost_guard": True,
        "manual_retry_requires_call_count_guard": True,
        "repeat_phase45_call_allowed": False,
        "discord_send_remains_disabled": True,
        "automatic_send_allowed": False,
        "raw_output_included": False,
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
        "ready_for_phase48_retry_manual_gate_design": False,
        "ready_for_phase48_discord_send_review_gate_design": False,
    }
    assert_phase47_disabled_retry_gate_design_safe(report)
    return report


def assert_phase47_disabled_retry_gate_design_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase47 disabled retry gate design contains sensitive values.")
    if not report.get("phase45_actual_llm_call_completed") or int(report.get("phase45_llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase47 retry design requires exactly one completed historical Phase45 LLM call.")
    if not report.get("output_safety_blocked") or not report.get("human_review_required"):
        raise ValueError("Phase47 retry design requires blocked output and human review.")
    for key in (
        "retry_gate_implemented",
        "retry_execution_available",
        "automatic_retry_allowed",
        "repeat_phase45_call_allowed",
        "automatic_send_allowed",
        "raw_output_included",
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
        "ready_for_phase48_retry_manual_gate_design",
        "ready_for_phase48_discord_send_review_gate_design",
    ):
        if report.get(key):
            raise ValueError(f"Phase47 disabled retry gate design unsafe flag is true: {key}")
    for key in (
        "manual_retry_requires_new_phase",
        "manual_retry_requires_new_manual_gate",
        "manual_retry_requires_new_approval_phrase",
        "manual_retry_requires_cost_guard",
        "manual_retry_requires_call_count_guard",
        "discord_send_remains_disabled",
    ):
        if not report.get(key):
            raise ValueError(f"Phase47 disabled retry gate design required guard is false: {key}")


def render_phase47_disabled_retry_gate_design_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase47 Disabled Retry Gate Design",
            "",
            "- Retry gate implemented: false",
            "- Retry execution available: false",
            "- Automatic retry allowed: false",
            "- Manual retry requires new phase: true",
            "- Manual retry requires new manual gate: true",
            "- Manual retry requires new approval phrase: true",
            "- Manual retry requires cost guard: true",
            "- Manual retry requires call-count guard: true",
            "- Repeat Phase45 call allowed: false",
            "- Discord send remains disabled: true",
            "- Raw output included: false",
            "- Full content included: false",
        ]
    ) + "\n"
