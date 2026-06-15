"""Phase 36D manually gated one-shot LLM draft call.

The default path is blocked and performs no provider call. A provider call can
be attempted only when the explicit CLI allow flag, manual approval env gate,
OpenRouter key presence, kasumi candidate, operation source, and no-send safety
conditions all pass.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Callable

from actual_one_shot_llm_draft_call_preflight import (
    MODEL,
    OPENROUTER_KEY_ALIASES,
    PROVIDER,
    build_actual_one_shot_llm_draft_call_preflight,
)
from llm_client import call_llm_once, redact_text
from llm_safety_policy import build_llm_safety_policy, check_llm_output_allowed


VERSION = "phase36d_actual_one_shot_llm_draft_call_no_discord_send"
APPROVAL_FLAG = "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVED"
APPROVAL_PHRASE = "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVAL_PHRASE"
EXPECTED_APPROVAL_PHRASE = "I_APPROVE_ONE_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_NO_SEND"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
PUBLIC_TEAM_SEND_RE = re.compile(r"(?i)(send|sent|post|posted|publish|published|reply|replied).{0,80}(public|team|channel|discord)|(?:public|team).{0,80}(send|sent|reply|replied|post|posted)")
CITATION = "knowledge/operation/stoxl_operation_tone_sample.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _env(env: dict[str, Any] | None) -> dict[str, Any]:
    return env if env is not None else os.environ


def _flag(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _key_value(env: dict[str, Any] | None) -> str:
    source = _env(env)
    for key in OPENROUTER_KEY_ALIASES:
        value = str(source.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _manual_approval(env: dict[str, Any] | None) -> dict[str, bool]:
    source = _env(env)
    flag_true = _flag(source.get(APPROVAL_FLAG))
    phrase = str(source.get(APPROVAL_PHRASE, "") or "")
    exact = phrase == EXPECTED_APPROVAL_PHRASE
    return {
        "required": True,
        "approved": flag_true and exact,
        "approval_flag_true": flag_true,
        "approval_phrase_present": bool(phrase),
        "approval_phrase_exact_match": exact,
        "approval_phrase_value_logged": False,
    }


def _blocked_client_result(reason: str) -> dict[str, Any]:
    return {
        "result_type": "llm_client_result",
        "provider": PROVIDER,
        "model": MODEL,
        "api_call_attempted": False,
        "api_call_succeeded": False,
        "api_call_failed": True,
        "error_type": reason,
        "response_text": "",
        "usage": {"input_chars": 0, "output_chars": 0, "estimated_cost_krw": None, "provider_usage": {}},
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def build_phase36d_prompt_envelope() -> dict[str, Any]:
    return {
        "envelope_type": "actual_one_shot_llm_draft_prompt",
        "version": VERSION,
        "agent_route_candidate": "kasumi",
        "allowed_sources": ["operation"],
        "evidence_citations": [CITATION],
        "full_content_included": False,
        "messages_preview": [
            {
                "role": "system",
                "content": (
                    "You are Kasumi for an internal STOXL operation review draft. "
                    "Use review-only wording. Do not say that anything was published, "
                    "submitted, sent, uploaded, approved, confirmed, or externally delivered. "
                    "Do not include secrets, raw IDs, or approval phrases. "
                    "Discord send, public/team reply, unattended auto reply, RAG, embeddings, "
                    "and external execution are disabled. "
                    "Preferred safety wording: This is a review-only draft. No external action has been taken."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Create a concise review-only operational draft for internal review. "
                    f"Use only source group operation and cite {CITATION}. "
                    "Separate confirmed checks from uncertainty and next human review steps."
                ),
            },
        ],
    }


def _llm_config(env: dict[str, Any] | None) -> dict[str, Any]:
    source = _env(env)
    return {
        "config_type": "phase36d_llm_client_config",
        "provider": PROVIDER,
        "model": MODEL,
        "api_key_present": bool(_key_value(env)),
        "api_key_value_logged": False,
        "_api_key": _key_value(env),
        "base_url_configured": bool(str(source.get("HERMES_LLM_BASE_URL", "") or "").strip()),
        "_base_url": str(source.get("HERMES_LLM_BASE_URL", "") or "").strip(),
        "timeout_seconds": 30,
        "temperature": 0.2,
        "api_call_enabled": True,
        "dry_call_mode": "private_test_only",
        "discord_send_enabled": False,
        "discord_runtime_send_messages": False,
        "rag_enabled": False,
        "external_execution": False,
        "llm_enabled": True,
        "private_test_only": True,
        "cost_guard_enabled": True,
        "max_output_chars": 1200,
    }


def _output_safety(response_text: str) -> dict[str, Any]:
    policy = build_llm_safety_policy({})
    policy["max_output_chars"] = 1200
    result = check_llm_output_allowed(response_text, policy)
    reasons = list(result.get("blocked_reasons", []))
    lowered = response_text.lower()
    if CITATION.lower() not in lowered:
        reasons.append("missing_evidence_citation")
    if "operations" in lowered:
        reasons.append("forbidden_operations_source")
    if PUBLIC_TEAM_SEND_RE.search(response_text):
        reasons.append("public_team_send_instruction")
    allowed = not reasons
    return {
        "allowed": allowed,
        "blocked": not allowed,
        "blocked_reasons": reasons,
        "safe_disclaimer_detected": bool(result.get("safe_disclaimer_detected")),
        "safe_disclaimer_reasons": result.get("safe_disclaimer_reasons", []),
        "reason": "review_only_output_allowed" if allowed else "output_safety_blocked",
    }


def _response_packet(result: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    preview = redact_text(str(result.get("response_text", "") or ""), 500)
    return {
        "packet_type": "actual_one_shot_llm_draft_response_packet",
        "version": VERSION,
        "created_at": utc_now(),
        "agent_route_candidate": "kasumi",
        "allowed_sources": ["operation"],
        "evidence_citations": [CITATION],
        "provider": result.get("provider", PROVIDER),
        "model": result.get("model", MODEL),
        "response_preview": preview,
        "response_preview_chars": len(preview),
        "full_content_included": False,
        "review_only": True,
        "output_safety_allowed": bool(output.get("allowed")),
        "output_safety_blocked": bool(output.get("blocked")),
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
    }


def build_actual_one_shot_llm_draft_call(
    env: dict[str, Any] | None = None,
    *,
    allow_actual_call: bool = False,
    candidate_agent: str = "kasumi",
    source: str = "operation",
    llm_caller: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    preflight = build_actual_one_shot_llm_draft_call_preflight(env=env)
    approval = _manual_approval(env)
    openrouter_key_present = bool(_key_value(env))
    blocked_reasons: list[str] = []
    if not approval["approved"]:
        blocked_reasons.append("manual_approval_not_approved")
    if not allow_actual_call:
        blocked_reasons.append("allow_flag_missing")
    if not openrouter_key_present:
        blocked_reasons.append("openrouter_api_key_missing")
    if candidate_agent != "kasumi":
        blocked_reasons.append("candidate_agent_not_allowed")
    if source != "operation":
        blocked_reasons.append("source_not_allowed")
    if source == "operations":
        blocked_reasons.append("operations_source_forbidden")
    if not preflight.get("source_phase36b_output_safety_allowed"):
        blocked_reasons.append("phase36b_output_safety_not_allowed")
    if not preflight.get("candidate_agent_allowed"):
        blocked_reasons.append("candidate_agent_not_allowed")

    ready = not blocked_reasons
    envelope = build_phase36d_prompt_envelope()
    config = _llm_config(env)
    if ready:
        result = (llm_caller or call_llm_once)(envelope, config)
        attempted = bool(result.get("api_call_attempted"))
        succeeded = bool(result.get("api_call_succeeded"))
        output = _output_safety(str(result.get("response_text", "") or "")) if succeeded else {
            "allowed": False,
            "blocked": True,
            "blocked_reasons": [str(result.get("error_type") or "llm_call_failed")],
            "safe_disclaimer_detected": False,
            "safe_disclaimer_reasons": [],
            "reason": "llm_call_failed",
        }
    else:
        result = _blocked_client_result("actual_call_gate_blocked")
        attempted = False
        succeeded = False
        output = {
            "allowed": False,
            "blocked": False,
            "blocked_reasons": [],
            "safe_disclaimer_detected": False,
            "safe_disclaimer_reasons": [],
            "reason": "not_checked_until_actual_call",
        }

    call_count = 1 if attempted else 0
    packet_created = bool(succeeded and output.get("allowed") and call_count == 1)
    packet = _response_packet(result, output) if packet_created else {}
    report = {
        "report_type": "actual_one_shot_llm_draft_call",
        "version": VERSION,
        "actual_call_available": True,
        "manual_approval_required": True,
        "manual_approval": approval,
        "allow_flag_present": bool(allow_actual_call),
        "candidate_agent": candidate_agent,
        "candidate_agent_allowed": candidate_agent == "kasumi",
        "allowed_sources": ["operation"] if source == "operation" else [source],
        "evidence_citations": [CITATION] if source == "operation" else [],
        "openrouter_api_key_present": openrouter_key_present,
        "openrouter_api_key_value_logged": False,
        "provider": PROVIDER,
        "model": MODEL,
        "ready": ready,
        "blocked": not ready,
        "blocked_reasons": blocked_reasons,
        "prompt_envelope": envelope,
        "llm_client_result": {
            key: value
            for key, value in result.items()
            if key != "response_text"
        },
        "llm_api_call_attempted": attempted,
        "llm_api_called": attempted,
        "llm_api_call_count": call_count,
        "llm_response_packet_created": packet_created,
        "llm_response_packet": packet,
        "llm_response_review_only": bool(packet_created),
        "output_safety_checked": bool(attempted),
        "output_safety_allowed": bool(output.get("allowed")),
        "output_safety_blocked": bool(output.get("blocked")),
        "output_safety": output,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "public_channel_send_called": False,
        "team_channel_send_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_discord_send": False,
        "ready_for_phase36e_closeout": bool(packet_created and output.get("allowed")),
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
            "llm_call_count": call_count,
        },
    }
    assert_actual_one_shot_llm_draft_call_safe(report)
    return report


def assert_actual_one_shot_llm_draft_call_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Actual one-shot LLM draft call report contains sensitive values.")
    for key in (
        "discord_api_send_called",
        "discord_message_sent",
        "public_channel_send_called",
        "team_channel_send_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Actual one-shot LLM draft call unsafe flag is true: {key}")
    if int(report.get("llm_api_call_count", 0) or 0) > 1:
        raise ValueError("Actual one-shot LLM draft call exceeded one call.")
    assertions = report.get("safety_assertions", {})
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
        if assertions.get(key):
            raise ValueError(f"Actual one-shot LLM draft call unsafe assertion is true: {key}")


def render_actual_one_shot_llm_draft_call_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Actual One-shot LLM Draft Call",
            "",
            f"- Ready: {str(report.get('ready')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Allow flag present: {str(report.get('allow_flag_present')).lower()}",
            f"- Manual approval approved: {str(report.get('manual_approval', {}).get('approved')).lower()}",
            f"- OpenRouter API key present: {str(report.get('openrouter_api_key_present')).lower()}",
            f"- Candidate agent: {report.get('candidate_agent')}",
            f"- Sources: {', '.join(report.get('allowed_sources', []))}",
            f"- LLM API call attempted: {str(report.get('llm_api_call_attempted')).lower()}",
            f"- LLM API call count: {report.get('llm_api_call_count')}",
            f"- LLM response packet created: {str(report.get('llm_response_packet_created')).lower()}",
            f"- Output safety allowed: {str(report.get('output_safety_allowed')).lower()}",
            "- Discord message sent: false",
            "- Ready for Discord send: false",
            f"- Ready for Phase 36E closeout: {str(report.get('ready_for_phase36e_closeout')).lower()}",
        ]
    ) + "\n"
