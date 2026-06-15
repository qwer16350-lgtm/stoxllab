"""Phase 34H-2 closeout for the observed RAG evidence LLM dry call.

This module is fixture/parser only. It never calls OpenRouter, Discord,
embeddings, vector stores, external ingest, or external execution.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase34h2_actual_llm_dry_call_closeout_no_additional_api"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
EVIDENCE_PATH_RE = re.compile(r"\bknowledge/[a-z0-9_-]+/[a-z0-9_.-]+\b", re.IGNORECASE)

EMBEDDED_SANITIZED_DRY_CALL_FIXTURE: dict[str, Any] = {
    "report_type": "rag_evidence_llm_dry_call",
    "version": "phase34h1_actual_llm_dry_call_no_discord_send",
    "actual_llm_api_call": True,
    "api_call_attempted": True,
    "api_call_succeeded": True,
    "llm_response_packet_created": True,
    "output_safety_allowed": True,
    "ready_for_discord_send": False,
    "discord_message_sent": False,
    "discord_send_attempted": False,
    "embedding_api_called": False,
    "external_execution": False,
    "provider": "openrouter",
    "model": "openai/gpt-5.4-mini",
    "client_result": {
        "provider": "openrouter",
        "model": "openai/gpt-5.4-mini",
        "api_call_attempted": True,
        "api_call_succeeded": True,
        "response_text": (
            "This is a review-only draft. No external action has been taken. "
            "The local evidence references knowledge/operation/stoxl_operation_tone_sample.md "
            "and knowledge/operation/stoxl_private_test_workflow_sample.md. "
            "The response is for human review before any Discord or external action."
        ),
        "usage": {
            "input_chars": 335,
            "output_chars": 101,
            "estimated_cost_krw": None,
            "provider_usage": {
                "prompt_tokens": 335,
                "completion_tokens": 101,
                "total_tokens": 436,
                "cost": 0.00070575,
            },
        },
    },
    "output_safety": {
        "allowed": True,
        "blocked": False,
        "blocked_reasons": [],
        "safe_disclaimer_detected": True,
        "safe_disclaimer_reasons": ["review_only", "negated_external_action"],
    },
}


def _text_safe(value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence LLM dry call closeout contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence LLM dry call closeout contains raw Discord-like IDs.")


def _bool(report: dict[str, Any], key: str, default: bool = False) -> bool:
    return bool(report.get(key, default))


def _client_result(report: dict[str, Any]) -> dict[str, Any]:
    result = report.get("client_result", {})
    return result if isinstance(result, dict) else {}


def _usage(result: dict[str, Any]) -> dict[str, Any]:
    usage = result.get("usage", {})
    return usage if isinstance(usage, dict) else {}


def _provider_usage(result: dict[str, Any]) -> dict[str, Any]:
    usage = _usage(result)
    provider_usage = usage.get("provider_usage", {})
    return provider_usage if isinstance(provider_usage, dict) else {}


def _cost(result: dict[str, Any]) -> float | int | None:
    provider_usage = _provider_usage(result)
    for key in ("provider_cost_usd", "cost", "estimated_cost_usd"):
        value = provider_usage.get(key)
        if isinstance(value, (int, float)):
            return value
    usage = _usage(result)
    value = usage.get("provider_cost_usd")
    return value if isinstance(value, (int, float)) else None


def _evidence_paths(response_text: str) -> list[str]:
    paths = []
    for match in EVIDENCE_PATH_RE.findall(response_text or ""):
        normalized = match.replace("\\", "/")
        if normalized not in paths:
            paths.append(normalized)
    return paths


def _relative_paths_only(paths: list[str]) -> bool:
    return bool(paths) and all(not path.startswith(("/", "\\")) and ":" not in path and path.startswith("knowledge/") for path in paths)


def build_rag_evidence_llm_dry_call_closeout(report: dict[str, Any] | None = None) -> dict[str, Any]:
    source = report or EMBEDDED_SANITIZED_DRY_CALL_FIXTURE
    _text_safe(source)
    result = _client_result(source)
    usage = _usage(result)
    provider_usage = _provider_usage(result)
    output = source.get("output_safety", {}) if isinstance(source.get("output_safety"), dict) else {}
    response_text = str(result.get("response_text", "") or "")
    paths = _evidence_paths(response_text)
    prompt_tokens = int(provider_usage.get("prompt_tokens", usage.get("input_chars", 0)) or 0)
    completion_tokens = int(provider_usage.get("completion_tokens", usage.get("output_chars", 0)) or 0)
    total_tokens = int(provider_usage.get("total_tokens", prompt_tokens + completion_tokens) or 0)
    actual_observed = _bool(source, "actual_llm_api_call") and _bool(source, "api_call_attempted") and _bool(source, "api_call_succeeded")
    safe_disclaimer = bool(output.get("safe_disclaimer_detected")) or "no external action has been taken" in response_text.lower()
    review_only = "review-only" in response_text.lower() or "review only" in response_text.lower()
    output_allowed = bool(source.get("output_safety_allowed", output.get("allowed")))
    closeout_passed = bool(
        actual_observed
        and source.get("llm_response_packet_created")
        and output_allowed
        and review_only
        and safe_disclaimer
        and _relative_paths_only(paths)
        and not source.get("ready_for_discord_send")
        and not source.get("discord_message_sent")
        and not source.get("discord_send_attempted")
        and not source.get("embedding_api_called")
        and not source.get("external_execution")
    )
    closeout = {
        "report_type": "rag_evidence_llm_dry_call_closeout",
        "version": VERSION,
        "actual_dry_call_observed": bool(actual_observed),
        "provider": source.get("provider") or result.get("provider", ""),
        "model": source.get("model") or result.get("model", ""),
        "api_call_attempted_count": 1 if source.get("api_call_attempted") else 0,
        "api_call_succeeded_count": 1 if source.get("api_call_succeeded") else 0,
        "llm_response_packet_created": bool(source.get("llm_response_packet_created")),
        "output_safety_allowed": output_allowed,
        "review_only_response": review_only,
        "safe_disclaimer_detected": safe_disclaimer,
        "relative_evidence_paths_only": _relative_paths_only(paths),
        "evidence_paths": paths,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "provider_cost_usd": _cost(result),
        "ready_for_discord_send": False,
        "discord_message_sent": False,
        "discord_send_attempted": False,
        "embedding_api_called": False,
        "external_execution": False,
        "additional_llm_api_call": False,
        "closeout_passed": closeout_passed,
        "ready_for_phase34i_private_test_would_send_preview": closeout_passed,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "discord_message_sent": False,
            "external_execution": False,
            "additional_llm_api_call": False,
        },
    }
    assert_rag_evidence_llm_dry_call_closeout_safe(closeout)
    return closeout


def render_rag_evidence_llm_dry_call_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence LLM Dry Call Closeout",
            "",
            f"- Version: {report.get('version', '')}",
            f"- Actual dry call observed: {str(report.get('actual_dry_call_observed')).lower()}",
            f"- Provider: {report.get('provider', '')}",
            f"- Model: {report.get('model', '')}",
            f"- API call attempted count: {report.get('api_call_attempted_count', 0)}",
            f"- API call succeeded count: {report.get('api_call_succeeded_count', 0)}",
            f"- LLM response packet created: {str(report.get('llm_response_packet_created')).lower()}",
            f"- Output safety allowed: {str(report.get('output_safety_allowed')).lower()}",
            f"- Review-only response: {str(report.get('review_only_response')).lower()}",
            f"- Relative evidence paths only: {str(report.get('relative_evidence_paths_only')).lower()}",
            f"- Evidence paths: {', '.join(report.get('evidence_paths', []))}",
            f"- Prompt tokens: {report.get('prompt_tokens', 0)}",
            f"- Completion tokens: {report.get('completion_tokens', 0)}",
            f"- Total tokens: {report.get('total_tokens', 0)}",
            f"- Provider cost USD: {report.get('provider_cost_usd')}",
            "- Ready for Discord send: false",
            "- Discord message sent: false",
            "- Discord send attempted: false",
            "- Embedding API called: false",
            "- External execution: false",
            "- Additional LLM API call: false",
            f"- Closeout passed: {str(report.get('closeout_passed')).lower()}",
            f"- Ready for Phase 34I private-test would-send preview: {str(report.get('ready_for_phase34i_private_test_would_send_preview')).lower()}",
        ]
    ) + "\n"


def assert_rag_evidence_llm_dry_call_closeout_safe(report: dict[str, Any]) -> None:
    _text_safe(report)
    if report.get("api_call_attempted_count") != 1:
        raise ValueError("RAG evidence LLM dry call closeout expected exactly one attempted API call.")
    if report.get("api_call_succeeded_count") != 1:
        raise ValueError("RAG evidence LLM dry call closeout expected exactly one succeeded API call.")
    if not report.get("llm_response_packet_created"):
        raise ValueError("RAG evidence LLM dry call closeout missing response packet.")
    if not report.get("output_safety_allowed"):
        raise ValueError("RAG evidence LLM dry call closeout output safety is not allowed.")
    if not report.get("relative_evidence_paths_only"):
        raise ValueError("RAG evidence LLM dry call closeout evidence paths are not relative-only.")
    if not isinstance(report.get("provider_cost_usd"), (int, float)):
        raise ValueError("RAG evidence LLM dry call closeout provider cost must be numeric.")
    for key in ("ready_for_discord_send", "discord_message_sent", "discord_send_attempted", "embedding_api_called", "external_execution", "additional_llm_api_call"):
        if report.get(key):
            raise ValueError(f"RAG evidence LLM dry call closeout unsafe flag is true: {key}")
    assertions = report.get("safety_assertions", {})
    for key in ("api_key_value_logged", "token_value_logged", "raw_discord_ids_logged", "embedding_called", "discord_message_sent", "external_execution", "additional_llm_api_call"):
        if assertions.get(key):
            raise ValueError(f"RAG evidence LLM dry call closeout unsafe assertion is true: {key}")
    if not report.get("closeout_passed"):
        raise ValueError("RAG evidence LLM dry call closeout did not pass.")
