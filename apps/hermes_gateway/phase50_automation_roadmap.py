"""Phase50 automation roadmap for the STOXL Discord Agent OS."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase50_automation_roadmap_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")

ROADMAP = [
    "Phase51/52: Continuous read-only runtime + review packet base",
    "Manual Gate: longer read-only live runtime",
    "Phase53/54: Agent router + review packet automation + fake LLM/RAG",
    "Phase55/56: Knowledge/RAG evidence layer + no-send LLM chain",
    "Manual Gate: RAG/LLM one-shot no Discord send",
    "Phase57: Private-test supervised auto reply runtime",
    "Manual Gate: private-test supervised auto reply session",
    "Phase58: Low-risk team-channel auto ops + scheduler dry-run",
    "Manual Gate: limited team-channel canary",
    "Phase59: Production hardening",
    "Final Manual Gate: limited production unattended launch",
]


def build_phase50_automation_roadmap() -> dict[str, Any]:
    report = {
        "report_type": "phase50_automation_roadmap",
        "version": VERSION,
        "target_system": "STOXL_Discord_Agent_OS",
        "remaining_safe_mega_bundles": 7,
        "remaining_manual_gates": 5,
        "next_phase": "phase51_52_continuous_readonly_runtime_foundation",
        "final_manual_gate": "limited_production_unattended_launch",
        "roadmap": list(ROADMAP),
        "automatic_retry_allowed_now": False,
        "automatic_discord_send_allowed_now": False,
        "production_unattended_allowed_now": False,
        "scheduler_cron_live_execution": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase50_automation_roadmap_safe(report)
    return report


def assert_phase50_automation_roadmap_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase50 roadmap contains sensitive values.")
    if report.get("remaining_safe_mega_bundles") != 7 or report.get("remaining_manual_gates") != 5:
        raise ValueError("Phase50 roadmap counts changed.")
    for key in (
        "automatic_retry_allowed_now",
        "automatic_discord_send_allowed_now",
        "production_unattended_allowed_now",
        "scheduler_cron_live_execution",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_api_send_called",
        "discord_message_sent",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase50 roadmap unsafe flag is true: {key}")


def render_phase50_automation_roadmap_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase50 Automation Roadmap",
            "",
            "- Remaining safe mega bundles: 7",
            "- Remaining manual gates: 5",
            "- Next phase: phase51_52_continuous_readonly_runtime_foundation",
            "- Final manual gate: limited_production_unattended_launch",
            "- Production unattended allowed now: false",
        ]
    ) + "\n"
