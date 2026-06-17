"""Phase50 final automation architecture lock for STOXL Discord Agent OS."""

from __future__ import annotations

import json
import re
from typing import Any

from phase49_production_readiness_audit import AUTOMATION_LEVELS, build_phase49_production_readiness_audit


VERSION = "phase50_final_automation_architecture_lock_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")

REQUIRED_MODULES = [
    "Discord Event Listener",
    "Event Normalizer",
    "Channel Risk Classifier",
    "Author/Self/Bot/Duplicate Guard",
    "Session Store",
    "Agent Router",
    "Review Packet Composer",
    "Knowledge/RAG Evidence Layer",
    "LLM Draft Generator",
    "Output Safety Classifier",
    "Manual Gate Controller",
    "Send Queue",
    "Scheduler/Cron Controller",
    "Budget/Cost Guard",
    "Rate Limit/Cooldown Guard",
    "Audit Log",
    "Kill Switch",
    "Operations Dashboard",
    "Forbidden Behavior Sentinel",
]


def build_phase50_final_automation_architecture_lock(audit: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = audit or build_phase49_production_readiness_audit()
    report = {
        "report_type": "phase50_final_automation_architecture_lock",
        "version": VERSION,
        "target_system": "STOXL_Discord_Agent_OS",
        "final_goal_is_operation_automation": True,
        "human_review_only_is_not_final_goal": True,
        "production_unattended_ready_now": False,
        "architecture_locked": True,
        "required_modules_defined": True,
        "required_modules": list(REQUIRED_MODULES),
        "manual_gate_boundary_defined": True,
        "automation_levels_defined": True,
        "automation_levels": dict(AUTOMATION_LEVELS),
        "current_verified_level": selected.get("current_verified_level", 3),
        "current_verified_level_status": selected.get("current_verified_level_status", "prototype_verified"),
        "next_safe_bundle": "continuous_readonly_runtime_foundation",
        "scheduler_cron_live_execution": False,
        "unattended_auto_reply_implemented": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_output_included": False,
        "full_content_included": False,
    }
    assert_phase50_final_automation_architecture_lock_safe(report)
    return report


def assert_phase50_final_automation_architecture_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase50 architecture lock contains sensitive values.")
    if report.get("target_system") != "STOXL_Discord_Agent_OS":
        raise ValueError("Phase50 architecture lock target system mismatch.")
    if len(report.get("required_modules", [])) != len(REQUIRED_MODULES):
        raise ValueError("Phase50 architecture lock requires all modules.")
    for key in ("final_goal_is_operation_automation", "human_review_only_is_not_final_goal", "architecture_locked", "required_modules_defined", "manual_gate_boundary_defined", "automation_levels_defined"):
        if not report.get(key):
            raise ValueError(f"Phase50 architecture lock required guard is false: {key}")
    for key in (
        "production_unattended_ready_now",
        "scheduler_cron_live_execution",
        "unattended_auto_reply_implemented",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_api_send_called",
        "discord_message_sent",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "raw_output_included",
        "full_content_included",
    ):
        if report.get(key):
            raise ValueError(f"Phase50 architecture lock unsafe flag is true: {key}")


def render_phase50_final_automation_architecture_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase50 Final Automation Architecture Lock",
            "",
            "- Target system: STOXL_Discord_Agent_OS",
            "- Final goal is operation automation: true",
            "- Human review only is not final goal: true",
            "- Production unattended ready now: false",
            "- Architecture locked: true",
            "- Required modules defined: true",
            "- Next safe bundle: continuous_readonly_runtime_foundation",
        ]
    ) + "\n"
