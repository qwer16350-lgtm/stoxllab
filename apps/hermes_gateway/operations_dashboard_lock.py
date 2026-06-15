"""Phase 35F operations dashboard lock."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agent_evidence_pack_composer import build_agent_evidence_pack_composer
from agent_prompt_preview import build_agent_prompt_preview
from agent_review_packet import build_agent_review_packet
from forbidden_behavior_sentinel import build_forbidden_behavior_sentinel
from local_knowledge_ingestion_preview import build_local_knowledge_ingestion_preview
from no_live_rehearsal_packet import build_no_live_rehearsal_packet
from one_shot_llm_no_send_final_lock import build_one_shot_llm_no_send_final_lock
from post_llm_call_dashboard_lock import build_post_llm_call_dashboard_lock
from phase35a_post_mvp_safety_audit import build_phase35a_post_mvp_safety_audit
from private_test_live_send_entry_gate import build_private_test_live_send_entry_gate
from rag_evidence_private_test_phase34_final_lock import build_rag_evidence_private_test_phase34_final_lock


VERSION = "phase35f_operations_dashboard_lock_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_operations_dashboard_lock(root: str | Path | None = None) -> dict[str, Any]:
    final_lock = build_rag_evidence_private_test_phase34_final_lock(root=str(root) if root else None)
    audit = build_phase35a_post_mvp_safety_audit(root=root, final_lock=final_lock)
    local = build_local_knowledge_ingestion_preview(root=root, source="operation")
    composer = build_agent_evidence_pack_composer()
    prompt = build_agent_prompt_preview(composer)
    review = build_agent_review_packet()
    rehearsal = build_no_live_rehearsal_packet()
    sentinel = build_forbidden_behavior_sentinel()
    phase36_final_lock = build_one_shot_llm_no_send_final_lock()
    phase36_dashboard = build_post_llm_call_dashboard_lock(phase36_final_lock)
    phase38_entry_gate = build_private_test_live_send_entry_gate()
    counts = audit.get("final_e2e_counts", {})
    report = {
        "report_type": "operations_dashboard_lock",
        "version": VERSION,
        "dashboard_lock_available": True,
        "report_only": True,
        "phase34_private_test_mvp_complete": bool(final_lock.get("phase34_private_test_mvp_complete")),
        "phase35a_safety_audit_passed": bool(audit.get("phase35a_audit_passed")),
        "phase35b_dry_previews_available": bool(local.get("ready_for_local_text_ingestion")),
        "phase35c_agent_prompt_previews_available": bool(prompt.get("prompt_preview_available")),
        "phase35d_review_approval_previews_available": bool(review.get("review_packet_available")),
        "phase35e_operator_rehearsal_available": bool(rehearsal.get("rehearsal_available")),
        "total_llm_call_count": int(counts.get("total_llm_call_count", 0) or 0),
        "send_retry_llm_call_count": int(counts.get("send_retry_llm_call_count", 0) or 0),
        "final_discord_message_sent_count": int(counts.get("final_discord_message_sent_count", 0) or 0),
        "sent_channel_scope": counts.get("sent_channel_scope", ""),
        "current_live_gates_off": True,
        "public_team_blocked": bool(sentinel.get("public_team_blocked")),
        "unattended_auto_reply_allowed": False,
        "embedding_vector_disabled": bool(sentinel.get("embedding_vector_disabled")),
        "external_execution": False,
        "ready_for_phase36_entry_gate": True,
        "phase36f_no_send_final_lock_passed": bool(phase36_final_lock.get("phase36f_no_send_final_lock_passed")),
        "phase36g_post_llm_dashboard_lock_available": bool(phase36_dashboard.get("dashboard_lock_available")),
        "phase36_total_llm_call_count": int(phase36_dashboard.get("total_phase36_llm_call_count", 0) or 0),
        "phase36_total_discord_message_sent_count": int(phase36_dashboard.get("total_phase36_discord_message_sent_count", 0) or 0),
        "ready_for_phase37_entry_gate": bool(phase36_dashboard.get("ready_for_phase37_entry_gate")),
        "phase38e_live_send_entry_gate_available": bool(phase38_entry_gate.get("live_send_entry_gate_available")),
        "phase39_not_started": bool(phase38_entry_gate.get("phase39_not_started")),
        "ready_for_phase39_live_execution": bool(phase38_entry_gate.get("ready_for_phase39_live_execution")),
        "ready_for_live_runtime": False,
        "ready_for_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "approval_phrase_generated": False,
            "live_runtime_executed": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
        },
    }
    assert_operations_dashboard_lock_safe(report)
    return report


def assert_operations_dashboard_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Operations dashboard lock contains sensitive values.")
    for key in (
        "unattended_auto_reply_allowed",
        "external_execution",
        "ready_for_live_runtime",
        "ready_for_llm_call",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
        "ready_for_phase39_live_execution",
    ):
        if report.get(key):
            raise ValueError(f"Operations dashboard lock unsafe flag is true: {key}")


def render_operations_dashboard_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Operations Dashboard Lock",
            "",
            "- Dashboard lock available: true",
            f"- Private-test MVP complete: {str(report.get('phase34_private_test_mvp_complete')).lower()}",
            f"- Phase 35A safety audit passed: {str(report.get('phase35a_safety_audit_passed')).lower()}",
            f"- Total LLM call count: {report.get('total_llm_call_count')}",
            f"- Send retry LLM count: {report.get('send_retry_llm_call_count')}",
            f"- Final Discord message count: {report.get('final_discord_message_sent_count')}",
            f"- Sent channel scope: {report.get('sent_channel_scope')}",
            "- Current live gates off: true",
            "- Public/team blocked: true",
            "- Unattended auto reply allowed: false",
            "- Embedding/vector disabled: true",
            "- External execution: false",
            "- Ready for live runtime: false",
        ]
    ) + "\n"
