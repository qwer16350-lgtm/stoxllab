"""Phase53 next read-only capture canary plan."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase53_next_readonly_capture_canary_plan_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase53_next_readonly_capture_canary_plan() -> dict[str, Any]:
    report = {
        "report_type": "phase53_next_readonly_capture_canary_plan",
        "version": VERSION,
        "next_manual_gate_required": True,
        "canary_goal": "capture_one_private_test_human_message_readonly",
        "recommended_timeout_seconds": 120,
        "recommended_max_events": 5,
        "discord_send_allowed": False,
        "reply_allowed": False,
        "llm_allowed": False,
        "rag_allowed": False,
        "embedding_vector_allowed": False,
        "external_execution_allowed": False,
        "scheduler_live_execution_allowed": False,
        "raw_content_dump_allowed": False,
        "raw_discord_ids_dump_allowed": False,
        "ready_for_next_manual_gate": True,
    }
    assert_phase53_next_readonly_capture_canary_plan_safe(report)
    return report


def assert_phase53_next_readonly_capture_canary_plan_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase53 canary plan contains sensitive values.")
    for key in (
        "discord_send_allowed",
        "reply_allowed",
        "llm_allowed",
        "rag_allowed",
        "embedding_vector_allowed",
        "external_execution_allowed",
        "scheduler_live_execution_allowed",
        "raw_content_dump_allowed",
        "raw_discord_ids_dump_allowed",
    ):
        if report.get(key):
            raise ValueError(f"Phase53 canary plan unsafe flag is true: {key}")
    if not report.get("next_manual_gate_required") or not report.get("ready_for_next_manual_gate"):
        raise ValueError("Phase53 canary plan requires manual gate readiness.")


def render_phase53_next_readonly_capture_canary_plan_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase53 Next Read-only Capture Canary Plan",
            "",
            "- Next manual gate required: true",
            "- Canary goal: capture_one_private_test_human_message_readonly",
            f"- Recommended timeout seconds: {report.get('recommended_timeout_seconds')}",
            f"- Recommended max events: {report.get('recommended_max_events')}",
            "- Discord send allowed: false",
            "- Reply allowed: false",
            "- LLM/RAG/external: false",
            "- Ready for next manual gate: true",
        ]
    ) + "\n"
