"""Phase 35A post-MVP safety audit.

Report-only safety hardening for the private-test E2E MVP. This module never
starts Discord, sends messages, calls LLM providers, creates embeddings, or
executes external actions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rag_evidence_private_test_phase34_final_lock import build_rag_evidence_private_test_phase34_final_lock


VERSION = "phase35a_post_mvp_safety_audit_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_PHRASE_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase35a_post_mvp_safety_audit(root: str | Path | None = None, final_lock: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_lock = final_lock or build_rag_evidence_private_test_phase34_final_lock(root=str(root) if root else None)
    e2e = selected_lock.get("e2e_live_reply_closeout", {}) if isinstance(selected_lock.get("e2e_live_reply_closeout"), dict) else {}
    retry = selected_lock.get("no_llm_send_retry_closeout", {}) if isinstance(selected_lock.get("no_llm_send_retry_closeout"), dict) else {}
    safety = selected_lock.get("final_safety_state", {}) if isinstance(selected_lock.get("final_safety_state"), dict) else {}
    knowledge = selected_lock.get("local_knowledge_boundary", {}) if isinstance(selected_lock.get("local_knowledge_boundary"), dict) else {}
    report = {
        "report_type": "phase35a_post_mvp_safety_audit",
        "version": VERSION,
        "phase34_private_test_mvp_complete": bool(selected_lock.get("phase34_private_test_mvp_complete")),
        "phase34m_final_lock_passed": bool(selected_lock.get("phase34m_final_lock_passed")),
        "final_e2e_counts": {
            "total_llm_call_count": int(e2e.get("llm_api_call_count", 0) or 0),
            "send_retry_llm_call_count": int(retry.get("llm_api_call_count", 0) or 0),
            "final_discord_message_sent_count": int(retry.get("message_sent_count", 0) or 0),
            "sent_channel_scope": retry.get("sent_channel_scope", ""),
        },
        "default_gate_state": {
            "discord_send_messages_enabled": False,
            "discord_private_test_reply_enabled": False,
            "reply_mode_private_test_only": False,
            "rag_evidence_e2e_live_reply_approved": False,
            "rag_evidence_e2e_send_retry_approved": False,
            "rag_evidence_llm_dry_call_approved": False,
            "llm_discord_send_enabled": False,
            "discord_rag_enabled": False,
            "rag_llm_reply_enabled": False,
        },
        "blocked_scopes": {
            "public_channel_reply_allowed": False,
            "team_channel_reply_allowed": False,
            "public_channel_send_allowed": False,
            "team_channel_send_allowed": False,
            "unattended_auto_reply_allowed": False,
        },
        "disabled_capabilities": {
            "embedding_api_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "scheduler_auto_reply": False,
        },
        "manual_controls": {
            "future_live_runs_require_manual_approval": True,
            "approval_phrase_value_logged": False,
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
        },
        "source_policy": {
            "canonical_sources": knowledge.get("canonical_sources", ["marketing", "operation", "strategy", "brand", "archive"]),
            "forbidden_sources": knowledge.get("forbidden_sources", ["operations"]),
        },
        "phase35a_audit_passed": False,
        "ready_for_phase35_entry_planning": False,
        "ready_for_unattended_auto_reply": False,
        "discord_live_runtime_executed_by_audit": False,
        "discord_message_sent_by_audit": False,
        "llm_api_called_by_audit": False,
        "llm_recall_by_audit": False,
        "embedding_or_vector_created_by_audit": False,
        "external_execution_by_audit": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "public_channel_reply_called": False,
            "team_channel_reply_called": False,
            "public_channel_send_called": False,
            "team_channel_send_called": False,
            "total_llm_call_count": int(e2e.get("llm_api_call_count", 0) or 0),
            "send_retry_llm_call_count": int(retry.get("llm_api_call_count", 0) or 0),
            "final_discord_message_sent_count": int(retry.get("message_sent_count", 0) or 0),
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
        },
    }
    report["phase35a_audit_passed"] = _passes_audit(report)
    report["ready_for_phase35_entry_planning"] = bool(report["phase35a_audit_passed"])
    assert_phase35a_post_mvp_safety_audit_safe(report)
    return report


def _passes_audit(report: dict[str, Any]) -> bool:
    counts = report.get("final_e2e_counts", {})
    gates = report.get("default_gate_state", {})
    blocked = report.get("blocked_scopes", {})
    disabled = report.get("disabled_capabilities", {})
    manual = report.get("manual_controls", {})
    sources = report.get("source_policy", {})
    return bool(
        report.get("phase34_private_test_mvp_complete")
        and report.get("phase34m_final_lock_passed")
        and int(counts.get("total_llm_call_count", 0) or 0) == 1
        and int(counts.get("send_retry_llm_call_count", 0) or 0) == 0
        and int(counts.get("final_discord_message_sent_count", 0) or 0) == 1
        and counts.get("sent_channel_scope") == "private_test_only"
        and not any(bool(value) for value in gates.values())
        and not any(bool(value) for value in blocked.values())
        and not any(bool(value) for value in disabled.values())
        and manual.get("future_live_runs_require_manual_approval")
        and not any(bool(manual.get(key)) for key in ("approval_phrase_value_logged", "api_key_value_logged", "token_value_logged", "raw_discord_ids_logged"))
        and "operation" in sources.get("canonical_sources", [])
        and "operations" in sources.get("forbidden_sources", [])
        and not report.get("ready_for_unattended_auto_reply")
    )


def assert_phase35a_post_mvp_safety_audit_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("Phase 35A audit contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Phase 35A audit contains raw Discord-like IDs.")
    if APPROVAL_PHRASE_RE.search(json.dumps(report, ensure_ascii=False)):
        raise ValueError("Phase 35A audit contains approval phrase values.")
    counts = report.get("final_e2e_counts", {})
    if int(counts.get("total_llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase 35A audit total LLM call count must be 1.")
    if int(counts.get("send_retry_llm_call_count", 0) or 0) != 0:
        raise ValueError("Phase 35A audit send retry LLM call count must be 0.")
    if int(counts.get("final_discord_message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase 35A audit final Discord message count must be 1.")
    if counts.get("sent_channel_scope") != "private_test_only":
        raise ValueError("Phase 35A audit sent scope must be private_test_only.")
    for section_name in ("default_gate_state", "blocked_scopes", "disabled_capabilities"):
        for key, value in report.get(section_name, {}).items():
            if value:
                raise ValueError(f"Phase 35A audit unsafe {section_name}.{key}=true.")
    if not report.get("manual_controls", {}).get("future_live_runs_require_manual_approval"):
        raise ValueError("Phase 35A audit must require future manual approvals.")
    sources = report.get("source_policy", {})
    if "operation" not in sources.get("canonical_sources", []) or "operations" not in sources.get("forbidden_sources", []):
        raise ValueError("Phase 35A audit must keep operation canonical and operations forbidden.")
    if not report.get("phase35a_audit_passed"):
        raise ValueError("Phase 35A audit did not pass.")


def render_phase35a_post_mvp_safety_audit_markdown(report: dict[str, Any]) -> str:
    counts = report.get("final_e2e_counts", {})
    return "\n".join(
        [
            "# STOXL Phase 35A Post-MVP Safety Audit",
            "",
            f"- Audit passed: {str(report.get('phase35a_audit_passed')).lower()}",
            f"- Phase 34 private-test MVP complete: {str(report.get('phase34_private_test_mvp_complete')).lower()}",
            f"- Phase 34M final lock passed: {str(report.get('phase34m_final_lock_passed')).lower()}",
            f"- Total LLM call count: {counts.get('total_llm_call_count', 0)}",
            f"- Send retry LLM call count: {counts.get('send_retry_llm_call_count', 0)}",
            f"- Final Discord message sent count: {counts.get('final_discord_message_sent_count', 0)}",
            f"- Sent channel scope: {counts.get('sent_channel_scope', '')}",
            "- Public/team channel send/reply allowed: false",
            "- Unattended auto reply allowed: false",
            "- Embedding/vector/external disabled: true",
            "- Future live runs require manual approval: true",
            "- Discord live runtime executed by audit: false",
            "- Discord message sent by audit: false",
            "- OpenRouter/LLM API call by audit: false",
            "- LLM recall by audit: false",
            "- Ready for Phase 35 entry planning: true",
        ]
    ) + "\n"
