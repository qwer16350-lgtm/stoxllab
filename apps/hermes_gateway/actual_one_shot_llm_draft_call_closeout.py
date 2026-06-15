"""Phase 36E closeout for the one-shot LLM draft call.

This module is report-only. It records the observed Phase 36D one-call,
no-send result as a sanitized closeout fixture and never calls an LLM provider,
starts Discord, sends messages, creates embeddings, or executes external
actions.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any


VERSION = "phase36e_actual_one_shot_llm_draft_call_closeout_no_send_final_lock"
CITATION = "knowledge/operation/stoxl_operation_tone_sample.md"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_PHRASE_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_success_fixture() -> dict[str, Any]:
    return {
        "report_type": "actual_one_shot_llm_draft_call_closeout",
        "version": VERSION,
        "closeout_available": True,
        "report_only": True,
        "source_phase36d_actual_call_observed": True,
        "agent": "kasumi",
        "allowed_sources": ["operation"],
        "evidence_citations": [CITATION],
        "provider": "openrouter",
        "model": "openai/gpt-5.4-mini",
        "usage": {
            "prompt_tokens": 143,
            "completion_tokens": 242,
            "total_tokens": 385,
            "cost": 0.00119625,
        },
        "llm_api_call_attempted_count": 1,
        "llm_api_called_count": 1,
        "additional_llm_api_call": False,
        "llm_response_packet_created": True,
        "llm_response_review_only": True,
        "output_safety_checked": True,
        "output_safety_allowed": True,
        "output_safety_blocked": False,
        "discord_live_runtime_executed_by_closeout": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "ready_for_discord_send": False,
        "public_channel_send_called": False,
        "team_channel_send_called": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "approval_phrase_generated": False,
        "manual_approval_actualized_for_send": False,
        "full_content_included": False,
        "response_preview_only": True,
        "response_preview": (
            "Review-only Kasumi operation draft was generated from the cited operation evidence. "
            "No Discord send or external action was performed."
        ),
        "phase36d_actual_llm_draft_call_complete": True,
        "phase36e_closeout_passed": True,
        "ready_for_phase36f_no_send_final_lock": True,
        "ready_for_discord_send_phase": False,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "full_content_included": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "discord_message_sent": False,
            "public_channel_send_called": False,
            "team_channel_send_called": False,
            "llm_call_count": 1,
        },
    }


def build_actual_one_shot_llm_draft_call_closeout(report: dict[str, Any] | None = None) -> dict[str, Any]:
    closeout = copy.deepcopy(report) if report is not None else build_success_fixture()
    closeout.setdefault("report_type", "actual_one_shot_llm_draft_call_closeout")
    closeout.setdefault("version", VERSION)
    closeout["closeout_available"] = True
    closeout["report_only"] = True
    closeout["additional_llm_api_call"] = False
    closeout["discord_live_runtime_executed_by_closeout"] = False
    closeout.setdefault("discord_api_send_called", False)
    closeout.setdefault("discord_message_sent", False)
    closeout["message_sent_count"] = int(closeout.get("message_sent_count", 0) or 0)
    closeout.setdefault("ready_for_discord_send", False)
    closeout.setdefault("ready_for_discord_send_phase", False)
    closeout.setdefault("ready_for_unattended_auto_reply", False)
    closeout.setdefault("public_channel_send_called", False)
    closeout.setdefault("team_channel_send_called", False)
    closeout.setdefault("public_channel_reply_allowed", False)
    closeout.setdefault("team_channel_reply_allowed", False)
    closeout.setdefault("unattended_auto_reply_allowed", False)
    closeout.setdefault("embedding_api_called", False)
    closeout.setdefault("vector_index_created", False)
    closeout.setdefault("external_execution", False)
    closeout.setdefault("approval_phrase_generated", False)
    closeout.setdefault("manual_approval_actualized_for_send", False)
    closeout.setdefault("full_content_included", False)
    closeout.setdefault("response_preview_only", True)
    closeout.setdefault("safety_assertions", {})
    safety = closeout["safety_assertions"]
    safety.setdefault("api_key_value_logged", False)
    safety.setdefault("token_value_logged", False)
    safety.setdefault("raw_discord_ids_logged", False)
    safety.setdefault("approval_phrase_value_logged", False)
    safety.setdefault("full_content_included", False)
    safety.setdefault("embedding_called", False)
    safety.setdefault("vector_index_created", False)
    safety.setdefault("external_execution", False)
    safety.setdefault("discord_message_sent", False)
    safety.setdefault("public_channel_send_called", False)
    safety.setdefault("team_channel_send_called", False)
    safety["llm_call_count"] = int(closeout.get("llm_api_called_count", 0) or 0)
    closeout["phase36e_closeout_passed"] = _passes_closeout(closeout)
    closeout["phase36d_actual_llm_draft_call_complete"] = bool(closeout["phase36e_closeout_passed"])
    closeout["ready_for_phase36f_no_send_final_lock"] = bool(closeout["phase36e_closeout_passed"])
    assert_actual_one_shot_llm_draft_call_closeout_safe(closeout)
    return closeout


def _passes_closeout(report: dict[str, Any]) -> bool:
    return bool(
        report.get("source_phase36d_actual_call_observed")
        and report.get("agent") == "kasumi"
        and report.get("allowed_sources") == ["operation"]
        and report.get("evidence_citations") == [CITATION]
        and report.get("provider") == "openrouter"
        and report.get("model") == "openai/gpt-5.4-mini"
        and int(report.get("llm_api_call_attempted_count", 0) or 0) == 1
        and int(report.get("llm_api_called_count", 0) or 0) == 1
        and report.get("llm_response_packet_created")
        and report.get("llm_response_review_only")
        and report.get("output_safety_checked")
        and report.get("output_safety_allowed")
        and not report.get("output_safety_blocked")
        and not report.get("discord_api_send_called")
        and not report.get("discord_message_sent")
        and int(report.get("message_sent_count", 0) or 0) == 0
        and not report.get("ready_for_discord_send")
        and not report.get("embedding_api_called")
        and not report.get("vector_index_created")
        and not report.get("external_execution")
        and not report.get("full_content_included")
        and report.get("response_preview_only")
    )


def assert_actual_one_shot_llm_draft_call_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered):
        raise ValueError("Phase 36E closeout contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Phase 36E closeout contains raw Discord-like IDs.")
    if APPROVAL_PHRASE_RE.search(text):
        raise ValueError("Phase 36E closeout contains approval phrase values.")
    if int(report.get("llm_api_call_attempted_count", 0) or 0) != 1:
        raise ValueError("Phase 36E closeout LLM attempt count must be exactly 1.")
    if int(report.get("llm_api_called_count", 0) or 0) != 1:
        raise ValueError("Phase 36E closeout LLM call count must be exactly 1.")
    if not report.get("llm_response_packet_created") or not report.get("llm_response_review_only"):
        raise ValueError("Phase 36E closeout requires a review-only LLM response packet.")
    if not report.get("output_safety_checked") or not report.get("output_safety_allowed") or report.get("output_safety_blocked"):
        raise ValueError("Phase 36E closeout output safety must be allowed.")
    for key in (
        "additional_llm_api_call",
        "discord_live_runtime_executed_by_closeout",
        "discord_api_send_called",
        "discord_message_sent",
        "ready_for_discord_send",
        "ready_for_discord_send_phase",
        "public_channel_send_called",
        "team_channel_send_called",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "approval_phrase_generated",
        "manual_approval_actualized_for_send",
        "full_content_included",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Phase 36E closeout unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 36E closeout message sent count must be 0.")
    if not report.get("response_preview_only"):
        raise ValueError("Phase 36E closeout must be preview-only.")
    safety = report.get("safety_assertions", {})
    for key in (
        "api_key_value_logged",
        "token_value_logged",
        "raw_discord_ids_logged",
        "approval_phrase_value_logged",
        "full_content_included",
        "embedding_called",
        "vector_index_created",
        "external_execution",
        "discord_message_sent",
        "public_channel_send_called",
        "team_channel_send_called",
    ):
        if safety.get(key):
            raise ValueError(f"Phase 36E closeout unsafe assertion is true: {key}")
    if int(safety.get("llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase 36E closeout safety assertion LLM call count must be 1.")
    if not report.get("phase36e_closeout_passed"):
        raise ValueError("Phase 36E closeout required conditions did not pass.")


def render_actual_one_shot_llm_draft_call_closeout_markdown(report: dict[str, Any]) -> str:
    usage = report.get("usage", {}) if isinstance(report.get("usage"), dict) else {}
    return "\n".join(
        [
            "# STOXL Actual One-shot LLM Draft Call Closeout",
            "",
            f"- Closeout passed: {str(report.get('phase36e_closeout_passed')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            f"- Source Phase 36D observed: {str(report.get('source_phase36d_actual_call_observed')).lower()}",
            f"- Agent: {report.get('agent', '')}",
            f"- Sources: {', '.join(report.get('allowed_sources', []))}",
            f"- Provider: {report.get('provider', '')}",
            f"- Model: {report.get('model', '')}",
            f"- LLM API call attempted count: {report.get('llm_api_call_attempted_count', 0)}",
            f"- LLM API called count: {report.get('llm_api_called_count', 0)}",
            f"- Total tokens: {usage.get('total_tokens', 0)}",
            f"- LLM response packet created: {str(report.get('llm_response_packet_created')).lower()}",
            f"- Output safety allowed: {str(report.get('output_safety_allowed')).lower()}",
            "- Discord message sent: false",
            "- Message sent count: 0",
            "- Ready for Discord send: false",
            "- Additional LLM API call by closeout: false",
            "- Embedding API called: false",
            "- External execution: false",
            f"- Ready for Phase 36F no-send final lock: {str(report.get('ready_for_phase36f_no_send_final_lock')).lower()}",
        ]
    ) + "\n"
