"""Phase50 release blocker matrix."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase50_release_blocker_matrix_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")

MISSING_BEFORE_PRODUCTION = [
    "continuous_readonly_runtime",
    "review_packet_automation",
    "agent_router",
    "rag_evidence_layer",
    "team_channel_low_risk_policy",
    "scheduler_safety",
    "global_kill_switch",
    "budget_guard",
    "incident_closeout",
]


def build_phase50_release_blocker_matrix() -> dict[str, Any]:
    report = {
        "report_type": "phase50_release_blocker_matrix",
        "version": VERSION,
        "unattended_auto_reply_blocked": True,
        "automatic_retry_blocked": True,
        "automatic_discord_send_blocked": True,
        "llm_repeat_call_blocked": True,
        "raw_output_dump_blocked": True,
        "scheduler_live_execution_blocked": True,
        "production_unattended_ready": False,
        "missing_before_production": list(MISSING_BEFORE_PRODUCTION),
        "release_blockers_present": True,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase50_release_blocker_matrix_safe(report)
    return report


def assert_phase50_release_blocker_matrix_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase50 release blocker matrix contains sensitive values.")
    for key in (
        "unattended_auto_reply_blocked",
        "automatic_retry_blocked",
        "automatic_discord_send_blocked",
        "llm_repeat_call_blocked",
        "raw_output_dump_blocked",
        "scheduler_live_execution_blocked",
        "release_blockers_present",
    ):
        if not report.get(key):
            raise ValueError(f"Phase50 release blocker missing block: {key}")
    if report.get("production_unattended_ready"):
        raise ValueError("Phase50 production unattended must remain not ready.")
    for key in ("llm_api_call_attempted", "llm_api_called", "discord_api_send_called", "discord_message_sent", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        if report.get(key):
            raise ValueError(f"Phase50 release blocker unsafe flag is true: {key}")
    if report.get("missing_before_production") != MISSING_BEFORE_PRODUCTION:
        raise ValueError("Phase50 release blocker missing-before-production list changed.")


def render_phase50_release_blocker_matrix_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase50 Release Blocker Matrix",
            "",
            "- Unattended auto reply blocked: true",
            "- Automatic retry blocked: true",
            "- Automatic Discord send blocked: true",
            "- LLM repeat call blocked: true",
            "- Raw output dump blocked: true",
            "- Scheduler live execution blocked: true",
            "- Production unattended ready: false",
        ]
    ) + "\n"
