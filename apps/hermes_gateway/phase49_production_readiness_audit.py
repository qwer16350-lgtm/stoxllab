"""Phase49 production-readiness audit for the STOXL Discord Agent OS path."""

from __future__ import annotations

import json
import re
from typing import Any

from phase48a_human_review_final_closeout import build_phase48a_human_review_final_closeout


VERSION = "phase49_production_readiness_audit_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


AUTOMATION_LEVELS = {
    "level_0_human_review_only": True,
    "level_1_read_only_observation": "partially_verified",
    "level_2_manual_gate_one_shot_execution": True,
    "level_3_supervised_private_test_auto_reply": "prototype_verified",
    "level_4_low_risk_team_auto_ops": False,
    "level_5_limited_production_unattended": False,
}


def build_phase49_production_readiness_audit(closeout: dict[str, Any] | None = None) -> dict[str, Any]:
    final = closeout or build_phase48a_human_review_final_closeout()
    report = {
        "report_type": "phase49_production_readiness_audit",
        "version": VERSION,
        "target_system": "STOXL_Discord_Agent_OS",
        "final_goal_is_operation_automation": True,
        "human_review_only_is_not_final_goal": True,
        "production_unattended_ready": False,
        "safe_for_human_review_only": True,
        "external_action_freeze_active": bool(final.get("external_action_freeze_active")),
        "manual_gate_required_for_any_future_external_action": bool(final.get("future_external_action_requires_new_manual_gate")),
        "actual_external_action_history": {
            "phase41b_discord_reply_completed_once": bool(final.get("actual_discord_reply_completed_once")),
            "phase42_supervised_session_completed_once": bool(final.get("actual_supervised_discord_session_completed_once")),
            "phase45_llm_call_completed_once": bool(final.get("actual_llm_call_completed_once")),
            "discord_send_after_llm": bool(final.get("discord_send_after_llm")),
            "blocked_llm_output_sent": False,
        },
        "automation_levels": dict(AUTOMATION_LEVELS),
        "current_verified_level": 3,
        "current_verified_level_status": "prototype_verified",
        "release_blockers_present": True,
        "ready_for_architecture_lock": True,
        "ready_for_continuous_readonly_foundation": True,
        "ready_for_agent_router_foundation": True,
        "ready_for_rag_foundation": False,
        "ready_for_low_risk_team_auto_ops": False,
        "ready_for_limited_production_unattended": False,
        "automatic_retry_allowed": False,
        "automatic_discord_send_allowed": False,
        "scheduler_cron_live_execution": False,
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
    assert_phase49_production_readiness_audit_safe(report)
    return report


def assert_phase49_production_readiness_audit_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase49 audit contains sensitive values.")
    history = report.get("actual_external_action_history", {})
    for key in ("phase41b_discord_reply_completed_once", "phase42_supervised_session_completed_once", "phase45_llm_call_completed_once"):
        if not history.get(key):
            raise ValueError(f"Phase49 audit missing completed history: {key}")
    for key in (
        "production_unattended_ready",
        "ready_for_rag_foundation",
        "ready_for_low_risk_team_auto_ops",
        "ready_for_limited_production_unattended",
        "automatic_retry_allowed",
        "automatic_discord_send_allowed",
        "scheduler_cron_live_execution",
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
            raise ValueError(f"Phase49 audit unsafe flag is true: {key}")
    if history.get("discord_send_after_llm") or history.get("blocked_llm_output_sent"):
        raise ValueError("Phase49 audit forbids post-LLM Discord send.")
    for key in ("safe_for_human_review_only", "external_action_freeze_active", "manual_gate_required_for_any_future_external_action", "release_blockers_present", "ready_for_architecture_lock"):
        if not report.get(key):
            raise ValueError(f"Phase49 audit required guard is false: {key}")


def render_phase49_production_readiness_audit_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase49 Production Readiness Audit",
            "",
            "- Target system: STOXL_Discord_Agent_OS",
            "- Production unattended ready: false",
            "- Safe for human review only: true",
            "- External action freeze active: true",
            "- Current verified level: Level 3 prototype_verified",
            "- Release blockers present: true",
            "- Ready for continuous read-only foundation: true",
            "- Ready for limited production unattended: false",
        ]
    ) + "\n"
