"""Phase 34M final lock for the private-test E2E RAG+LLM+Discord MVP.

This module is report-only. It uses the Phase 34L-2 closeout fixture and never
starts Discord, sends messages, calls LLM providers, creates embeddings, or
executes external actions.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any

from knowledge_ingestion_boundary import build_knowledge_ingestion_boundary_report
from rag_evidence_private_test_e2e_live_closeout import build_rag_evidence_private_test_e2e_live_closeout


VERSION = "phase34m_private_test_e2e_mvp_final_lock"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_PHRASE_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_rag_evidence_private_test_phase34_final_lock(
    root: str | None = None,
    *,
    closeout: dict[str, Any] | None = None,
    knowledge_boundary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_closeout = copy.deepcopy(closeout) if closeout is not None else build_rag_evidence_private_test_e2e_live_closeout()
    selected_knowledge = copy.deepcopy(knowledge_boundary) if knowledge_boundary is not None else build_knowledge_ingestion_boundary_report(root=root)
    final = selected_closeout.get("final_result", {}) if isinstance(selected_closeout.get("final_result"), dict) else {}
    retry = selected_closeout.get("no_llm_send_retry", {}) if isinstance(selected_closeout.get("no_llm_send_retry"), dict) else {}
    initial = selected_closeout.get("initial_discord_send_attempt", {}) if isinstance(selected_closeout.get("initial_discord_send_attempt"), dict) else {}
    canonical_sources = list(selected_knowledge.get("canonical_sources", ["marketing", "operation", "strategy", "brand", "archive"]))
    if "operation" not in canonical_sources:
        canonical_sources.append("operation")

    report = {
        "report_type": "rag_evidence_private_test_phase34_final_lock",
        "version": VERSION,
        "phase34_private_test_mvp_complete": True,
        "local_knowledge_boundary": {
            "ready_for_local_text_ingestion": bool(selected_knowledge.get("ready_for_local_text_ingestion", True)),
            "ready_for_embedding": False,
            "ready_for_external_sources": False,
            "canonical_sources": canonical_sources,
            "forbidden_sources": ["operations"],
        },
        "e2e_live_reply_closeout": {
            "closeout_passed": bool(selected_closeout.get("closeout_passed")),
            "e2e_live_reply_observed": bool(selected_closeout.get("e2e_live_reply_observed")),
            "llm_api_call_count": int(selected_closeout.get("llm_api_call_count", 0) or 0),
            "llm_response_packet_created": bool(selected_closeout.get("llm_response_packet_created")),
            "output_safety_allowed": bool(selected_closeout.get("output_safety_allowed")),
            "initial_discord_send_failure_reason": initial.get("discord_send_failure_reason", ""),
        },
        "no_llm_send_retry_closeout": {
            "llm_recall_allowed": bool(retry.get("llm_recall_allowed")),
            "llm_api_call_count": int(retry.get("llm_api_call_count", 0) or 0),
            "discord_message_sent": bool(retry.get("discord_message_sent")),
            "message_sent_count": int(retry.get("message_sent_count", 0) or 0),
            "sent_channel_scope": retry.get("sent_channel_scope", ""),
        },
        "final_safety_state": {
            "public_channel_reply_allowed": False,
            "team_channel_reply_allowed": False,
            "public_channel_send_allowed": False,
            "team_channel_send_allowed": False,
            "ready_for_unattended_auto_reply": bool(final.get("ready_for_unattended_auto_reply")),
            "embedding_api_called": False,
            "external_execution": False,
        },
        "manual_gates_required_for_future_live_runs": True,
        "default_runtime_sends_disabled": True,
        "phase34m_final_lock_passed": False,
        "ready_for_next_phase": "blocked",
        "discord_live_runtime_executed_by_final_lock": False,
        "additional_discord_send": False,
        "additional_llm_api_call": False,
        "llm_recall": False,
        "embedding_api_called": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "public_channel_reply_called": False,
            "team_channel_reply_called": False,
            "public_channel_send_called": False,
            "team_channel_send_called": False,
            "total_llm_call_count": int(selected_closeout.get("llm_api_call_count", 0) or 0),
            "send_retry_llm_call_count": int(retry.get("llm_api_call_count", 0) or 0),
            "final_discord_message_sent_count": int(final.get("message_sent_count", 0) or 0),
            "embedding_called": False,
            "external_execution": False,
        },
    }
    report["phase34m_final_lock_passed"] = _passes_final_lock(report)
    report["phase34_private_test_mvp_complete"] = bool(report["phase34m_final_lock_passed"])
    report["ready_for_next_phase"] = "phase35_or_commit_only" if report["phase34m_final_lock_passed"] else "blocked"
    assert_rag_evidence_private_test_phase34_final_lock_safe(report)
    return report


def _passes_final_lock(report: dict[str, Any]) -> bool:
    knowledge = report.get("local_knowledge_boundary", {})
    closeout = report.get("e2e_live_reply_closeout", {})
    retry = report.get("no_llm_send_retry_closeout", {})
    safety = report.get("final_safety_state", {})
    return bool(
        knowledge.get("ready_for_local_text_ingestion")
        and "operation" in knowledge.get("canonical_sources", [])
        and "operations" in knowledge.get("forbidden_sources", [])
        and closeout.get("closeout_passed")
        and int(closeout.get("llm_api_call_count", 0) or 0) == 1
        and closeout.get("llm_response_packet_created")
        and closeout.get("output_safety_allowed")
        and closeout.get("initial_discord_send_failure_reason") == "ServerDisconnectedError"
        and not retry.get("llm_recall_allowed")
        and int(retry.get("llm_api_call_count", 0) or 0) == 0
        and retry.get("discord_message_sent")
        and int(retry.get("message_sent_count", 0) or 0) == 1
        and retry.get("sent_channel_scope") == "private_test_only"
        and not safety.get("public_channel_reply_allowed")
        and not safety.get("team_channel_reply_allowed")
        and not safety.get("public_channel_send_allowed")
        and not safety.get("team_channel_send_allowed")
        and not safety.get("ready_for_unattended_auto_reply")
        and not safety.get("embedding_api_called")
        and not safety.get("external_execution")
        and report.get("manual_gates_required_for_future_live_runs")
        and report.get("default_runtime_sends_disabled")
    )


def assert_rag_evidence_private_test_phase34_final_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("Phase 34 final lock contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Phase 34 final lock contains raw Discord-like IDs.")
    if APPROVAL_PHRASE_RE.search(json.dumps(report, ensure_ascii=False)):
        raise ValueError("Phase 34 final lock contains approval phrase values.")
    closeout = report.get("e2e_live_reply_closeout", {})
    retry = report.get("no_llm_send_retry_closeout", {})
    safety = report.get("final_safety_state", {})
    knowledge = report.get("local_knowledge_boundary", {})
    assertions = report.get("safety_assertions", {})
    if int(closeout.get("llm_api_call_count", 0) or 0) != 1:
        raise ValueError("Phase 34 final lock total LLM call count must be 1.")
    if retry.get("llm_recall_allowed") or int(retry.get("llm_api_call_count", 0) or 0) != 0:
        raise ValueError("Phase 34 final lock send retry must not call LLM.")
    if int(retry.get("message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase 34 final lock final Discord message count must be 1.")
    if retry.get("sent_channel_scope") != "private_test_only":
        raise ValueError("Phase 34 final lock send scope must be private_test_only.")
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed"):
        if safety.get(key):
            raise ValueError(f"Phase 34 final lock unsafe public/team flag is true: {key}")
    if safety.get("ready_for_unattended_auto_reply"):
        raise ValueError("Phase 34 final lock must keep unattended auto reply false.")
    if safety.get("embedding_api_called") or safety.get("external_execution") or assertions.get("embedding_called") or assertions.get("external_execution"):
        raise ValueError("Phase 34 final lock must keep embedding/external execution false.")
    if "operation" not in knowledge.get("canonical_sources", []) or "operations" not in knowledge.get("forbidden_sources", []):
        raise ValueError("Phase 34 final lock must keep operation canonical and operations forbidden.")
    if not report.get("manual_gates_required_for_future_live_runs"):
        raise ValueError("Phase 34 final lock must require future manual gates.")
    if not report.get("phase34m_final_lock_passed"):
        raise ValueError("Phase 34 final lock did not pass.")


def render_rag_evidence_private_test_phase34_final_lock_markdown(report: dict[str, Any]) -> str:
    closeout = report.get("e2e_live_reply_closeout", {})
    retry = report.get("no_llm_send_retry_closeout", {})
    safety = report.get("final_safety_state", {})
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test Phase 34 Final Lock",
            "",
            f"- Phase 34 private-test MVP complete: {str(report.get('phase34_private_test_mvp_complete')).lower()}",
            f"- Final lock passed: {str(report.get('phase34m_final_lock_passed')).lower()}",
            f"- E2E closeout passed: {str(closeout.get('closeout_passed')).lower()}",
            f"- Total E2E LLM call count: {closeout.get('llm_api_call_count', 0)}",
            f"- Send retry LLM call count: {retry.get('llm_api_call_count', 0)}",
            f"- Final Discord message sent count: {retry.get('message_sent_count', 0)}",
            f"- Sent channel scope: {retry.get('sent_channel_scope', '')}",
            f"- Public/team channel send/reply allowed: {str(any(safety.get(key) for key in ('public_channel_reply_allowed', 'team_channel_reply_allowed', 'public_channel_send_allowed', 'team_channel_send_allowed'))).lower()}",
            f"- Ready for unattended auto reply: {str(safety.get('ready_for_unattended_auto_reply')).lower()}",
            f"- Embedding API called: {str(safety.get('embedding_api_called')).lower()}",
            f"- External execution: {str(safety.get('external_execution')).lower()}",
            "- Discord live runtime executed by final lock: false",
            "- Discord message sent by final lock: false",
            "- OpenRouter/LLM API call by final lock: false",
            "- LLM recall by final lock: false",
            f"- Ready for next phase: {report.get('ready_for_next_phase', '')}",
        ]
    ) + "\n"
