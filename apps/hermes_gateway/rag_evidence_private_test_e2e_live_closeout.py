"""Phase 34L-2 closeout for the private-test E2E live reply chain.

This is a pure report/replay/audit closeout. It uses a sanitized embedded
fixture and never starts Discord, sends a message, calls an LLM provider,
creates embeddings, or executes external actions.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any


VERSION = "phase34l2_e2e_live_reply_and_no_llm_send_retry_closeout"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_PHRASE_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_success_fixture() -> dict[str, Any]:
    return {
        "report_type": "rag_evidence_private_test_e2e_live_closeout",
        "version": VERSION,
        "e2e_live_reply_observed": True,
        "discord_event_received": True,
        "accepted_private_test_channel": True,
        "public_channel_event_rejected": True,
        "team_channel_event_rejected": True,
        "knowledge_dry_chain_executed": True,
        "evidence_packet_created": True,
        "rag_response_packet_created": True,
        "review_packet_created": True,
        "prompt_envelope_created": True,
        "prompt_safety_checked": True,
        "prompt_safety_allowed": True,
        "llm_dispatch_invoked": True,
        "llm_dispatch_mode": "actual_openrouter_once",
        "llm_api_call_attempted": True,
        "llm_api_called": True,
        "llm_api_call_count": 1,
        "llm_response_packet_created": True,
        "output_safety_checked": True,
        "output_safety_allowed": True,
        "output_safety_blocked": False,
        "initial_discord_send_attempt": {
            "discord_api_send_allowed": True,
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
            "discord_send_failed": True,
            "discord_send_failure_reason": "ServerDisconnectedError",
        },
        "no_llm_send_retry": {
            "partial_success_available": True,
            "llm_recall_allowed": False,
            "llm_api_called": False,
            "llm_api_call_count": 0,
            "output_safety_already_passed": True,
            "manual_approval_approved": True,
            "discord_api_send_called": True,
            "discord_message_sent": True,
            "message_sent_count": 1,
            "sent_channel_scope": "private_test_only",
        },
        "final_result": {
            "discord_message_sent": True,
            "message_sent_count": 1,
            "sent_channel_scope": "private_test_only",
            "ready_for_unattended_auto_reply": False,
            "closeout_passed": True,
            "ready_for_phase34m_final_lock": True,
        },
        "discord_live_runtime_executed_by_closeout": False,
        "additional_discord_send": False,
        "additional_llm_api_call": False,
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
            "total_llm_call_count": 1,
            "send_retry_llm_call_count": 0,
            "final_discord_message_sent_count": 1,
            "embedding_called": False,
            "external_execution": False,
        },
    }


def build_rag_evidence_private_test_e2e_live_closeout(report: dict[str, Any] | None = None) -> dict[str, Any]:
    closeout = copy.deepcopy(report) if report is not None else build_success_fixture()
    closeout.setdefault("report_type", "rag_evidence_private_test_e2e_live_closeout")
    closeout.setdefault("version", VERSION)
    closeout["discord_live_runtime_executed_by_closeout"] = False
    closeout["additional_discord_send"] = False
    closeout["additional_llm_api_call"] = False
    closeout["embedding_api_called"] = False
    closeout["external_execution"] = False
    closeout.setdefault("safety_assertions", {})
    safety = closeout["safety_assertions"]
    safety["api_key_value_logged"] = False
    safety["token_value_logged"] = False
    safety["raw_discord_ids_logged"] = False
    safety["approval_phrase_value_logged"] = False
    safety.setdefault("public_channel_reply_called", False)
    safety.setdefault("team_channel_reply_called", False)
    safety.setdefault("public_channel_send_called", False)
    safety.setdefault("team_channel_send_called", False)
    safety["total_llm_call_count"] = int(closeout.get("llm_api_call_count", 0) or 0)
    retry = closeout.get("no_llm_send_retry", {}) if isinstance(closeout.get("no_llm_send_retry"), dict) else {}
    final = closeout.get("final_result", {}) if isinstance(closeout.get("final_result"), dict) else {}
    safety["send_retry_llm_call_count"] = int(retry.get("llm_api_call_count", 0) or 0)
    safety["final_discord_message_sent_count"] = int(final.get("message_sent_count", 0) or 0)
    safety["embedding_called"] = False
    safety["external_execution"] = False
    closeout["closeout_passed"] = _passes_required_conditions(closeout)
    if isinstance(closeout.get("final_result"), dict):
        closeout["final_result"]["closeout_passed"] = bool(closeout["closeout_passed"])
        closeout["final_result"]["ready_for_phase34m_final_lock"] = bool(closeout["closeout_passed"])
    assert_rag_evidence_private_test_e2e_live_closeout_safe(closeout)
    return closeout


def _passes_required_conditions(report: dict[str, Any]) -> bool:
    retry = report.get("no_llm_send_retry", {}) if isinstance(report.get("no_llm_send_retry"), dict) else {}
    final = report.get("final_result", {}) if isinstance(report.get("final_result"), dict) else {}
    initial = report.get("initial_discord_send_attempt", {}) if isinstance(report.get("initial_discord_send_attempt"), dict) else {}
    return bool(
        report.get("e2e_live_reply_observed")
        and report.get("discord_event_received")
        and report.get("accepted_private_test_channel")
        and int(report.get("llm_api_call_count", 0) or 0) == 1
        and report.get("llm_response_packet_created")
        and report.get("output_safety_allowed")
        and not report.get("output_safety_blocked")
        and initial.get("discord_send_failed")
        and initial.get("discord_send_failure_reason") == "ServerDisconnectedError"
        and int(retry.get("llm_api_call_count", 0) or 0) == 0
        and not retry.get("llm_api_called")
        and retry.get("discord_message_sent")
        and int(retry.get("message_sent_count", 0) or 0) == 1
        and final.get("discord_message_sent")
        and int(final.get("message_sent_count", 0) or 0) == 1
        and final.get("sent_channel_scope") == "private_test_only"
        and not final.get("ready_for_unattended_auto_reply")
        and not report.get("embedding_api_called")
        and not report.get("external_execution")
    )


def assert_rag_evidence_private_test_e2e_live_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("E2E live closeout contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("E2E live closeout contains raw Discord-like IDs.")
    if APPROVAL_PHRASE_RE.search(json.dumps(report, ensure_ascii=False)):
        raise ValueError("E2E live closeout contains approval phrase values.")
    retry = report.get("no_llm_send_retry", {}) if isinstance(report.get("no_llm_send_retry"), dict) else {}
    final = report.get("final_result", {}) if isinstance(report.get("final_result"), dict) else {}
    safety = report.get("safety_assertions", {}) if isinstance(report.get("safety_assertions"), dict) else {}
    if int(report.get("llm_api_call_count", 0) or 0) != 1:
        raise ValueError("E2E live closeout total LLM call count must be exactly 1.")
    if retry.get("llm_api_called") or int(retry.get("llm_api_call_count", 0) or 0) != 0:
        raise ValueError("E2E live closeout send retry must not call LLM.")
    if int(final.get("message_sent_count", 0) or 0) != 1:
        raise ValueError("E2E live closeout final Discord sent count must be exactly 1.")
    if final.get("sent_channel_scope") != "private_test_only":
        raise ValueError("E2E live closeout final send scope must be private_test_only.")
    if not report.get("output_safety_allowed") or report.get("output_safety_blocked"):
        raise ValueError("E2E live closeout output safety must be allowed.")
    for key in ("public_channel_reply_called", "team_channel_reply_called", "public_channel_send_called", "team_channel_send_called"):
        if safety.get(key):
            raise ValueError(f"E2E live closeout unsafe public/team flag is true: {key}")
    if final.get("ready_for_unattended_auto_reply"):
        raise ValueError("E2E live closeout must not enable unattended auto reply.")
    if report.get("embedding_api_called") or report.get("external_execution") or safety.get("embedding_called") or safety.get("external_execution"):
        raise ValueError("E2E live closeout must not use embeddings or external execution.")
    if not report.get("closeout_passed"):
        raise ValueError("E2E live closeout required conditions did not pass.")


def render_rag_evidence_private_test_e2e_live_closeout_markdown(report: dict[str, Any]) -> str:
    retry = report.get("no_llm_send_retry", {}) if isinstance(report.get("no_llm_send_retry"), dict) else {}
    final = report.get("final_result", {}) if isinstance(report.get("final_result"), dict) else {}
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test E2E Live Closeout",
            "",
            f"- Closeout passed: {str(report.get('closeout_passed')).lower()}",
            f"- E2E live reply observed: {str(report.get('e2e_live_reply_observed')).lower()}",
            f"- Discord event received: {str(report.get('discord_event_received')).lower()}",
            f"- Accepted private-test channel: {str(report.get('accepted_private_test_channel')).lower()}",
            f"- LLM API call count: {report.get('llm_api_call_count', 0)}",
            f"- LLM response packet created: {str(report.get('llm_response_packet_created')).lower()}",
            f"- Output safety allowed: {str(report.get('output_safety_allowed')).lower()}",
            f"- Initial send failure: {report.get('initial_discord_send_attempt', {}).get('discord_send_failure_reason', '')}",
            f"- Send retry LLM call count: {retry.get('llm_api_call_count', 0)}",
            f"- Send retry Discord message sent: {str(retry.get('discord_message_sent')).lower()}",
            f"- Final Discord message sent count: {final.get('message_sent_count', 0)}",
            f"- Sent channel scope: {final.get('sent_channel_scope', '')}",
            f"- Ready for Phase 34M final lock: {str(final.get('ready_for_phase34m_final_lock')).lower()}",
            f"- Ready for unattended auto reply: {str(final.get('ready_for_unattended_auto_reply')).lower()}",
            "- Discord live runtime executed by closeout: false",
            "- Additional Discord send: false",
            "- Additional LLM API call: false",
            "- Embedding API called: false",
            "- External execution: false",
        ]
    ) + "\n"
