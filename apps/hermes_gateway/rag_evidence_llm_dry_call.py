"""Phase 34H-1 approved RAG evidence LLM dry-call boundary.

Default behavior is report-only. A real provider call is attempted only when
the CLI caller passes the explicit allow flag and the manual env approval gate
is present. Discord send, embeddings, RAG ingest, and external execution stay
disabled in every report shape.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from llm_client import (
    assert_llm_client_result_safe,
    build_llm_client_config,
    call_llm_once,
    public_llm_client_config,
    validate_llm_client_config,
)
from llm_response_packet import build_llm_response_packet
from llm_safety_policy import build_llm_safety_policy, check_llm_output_allowed
from rag_evidence_prompt_envelope import build_rag_evidence_prompt_envelope


VERSION = "phase34h1_actual_llm_dry_call_no_discord_send"
APPROVAL_PHRASE = "I_APPROVE_ONE_RAG_EVIDENCE_LLM_DRY_CALL"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)

ClientRunner = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _empty_client_result(config: dict[str, Any], error_type: str = "manual_approval_required") -> dict[str, Any]:
    result = {
        "result_type": "llm_client_result",
        "version": "phase32b_private_test_dry_call",
        "provider": config.get("provider", ""),
        "model": config.get("model", ""),
        "api_call_attempted": False,
        "api_call_succeeded": False,
        "api_call_failed": True,
        "error_type": error_type,
        "provider_status_code": None,
        "provider_error_code": None,
        "provider_error_message": None,
        "provider_response_redacted": False,
        "response_text": "",
        "usage": {
            "input_chars": 0,
            "output_chars": 0,
            "estimated_cost_krw": None,
            "provider_usage": {},
        },
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }
    assert_llm_client_result_safe(result)
    return result


def build_manual_approval_report(env: dict[str, Any] | None = None) -> dict[str, Any]:
    approved_flag = _flag(_env_value(env, "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED", "false"))
    phrase_value = _env_value(env, "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE", "")
    phrase_ok = phrase_value == APPROVAL_PHRASE
    return {
        "required": True,
        "approved": bool(approved_flag and phrase_ok),
        "approval_flag_true": bool(approved_flag),
        "approval_phrase_present": bool(phrase_value),
        "approval_phrase_exact_match": bool(phrase_ok),
        "approval_phrase_value_logged": False,
    }


def _safe_output_safety(result: dict[str, Any], env: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = build_llm_safety_policy(env or {})
    return check_llm_output_allowed(str(result.get("response_text", "") or ""), policy)


def _fake_packet_report(
    envelope: dict[str, Any],
    result: dict[str, Any],
    output_safety: dict[str, Any],
    *,
    allow_api_call: bool,
    actual_llm_api_call: bool,
) -> dict[str, Any]:
    return {
        "report_type": "rag_evidence_llm_dry_call_report",
        "created_at": utc_now(),
        "request": {
            "agent_route_candidate": envelope.get("agent", "kasumi"),
            "allow_api_call": bool(allow_api_call),
            "source": envelope.get("source", "operation"),
        },
        "client_result": result,
        "output_safety": output_safety,
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "actual_llm_api_call": bool(actual_llm_api_call),
    }


def build_rag_evidence_llm_dry_call_report(
    root: str | Path | None = None,
    source: str = "operation",
    agent: str = "kasumi",
    query: str = "STOXL brand tone",
    *,
    allow_api_call: bool = False,
    env: dict[str, Any] | None = None,
    client_runner: ClientRunner | None = None,
) -> dict[str, Any]:
    envelope = build_rag_evidence_prompt_envelope(root=root, source=source, agent=agent, query=query)
    config = build_llm_client_config(env)
    if str(config.get("provider", "") or "").strip() in {"", "disabled"}:
        config["provider"] = "openrouter"
    if not str(config.get("model", "") or "").strip():
        config["model"] = "openai/gpt-5.4-mini"
    manual_approval = build_manual_approval_report(env)
    blocked_reasons: list[str] = []
    if not envelope.get("ready_for_prompt_preview"):
        blocked_reasons.append("prompt_envelope_not_ready")
    if not allow_api_call:
        blocked_reasons.append("allow_rag_evidence_llm_api_call_required")
    if not manual_approval.get("approved"):
        blocked_reasons.append("manual_approval_required")
    if not config.get("model"):
        blocked_reasons.append("model_not_configured")
    if not client_runner and not config.get("api_key_present") and allow_api_call and manual_approval.get("approved"):
        blocked_reasons.append("api_key_missing")
    if not client_runner and allow_api_call and manual_approval.get("approved") and config.get("api_key_present"):
        validation = validate_llm_client_config(config)
        if validation.get("blocked"):
            blocked_reasons.extend(
                reason for reason in validation.get("blocked_reasons", []) if reason not in blocked_reasons
            )

    ready_to_attempt = not blocked_reasons
    actual_llm_api_call = bool(ready_to_attempt and client_runner is None)
    if ready_to_attempt:
        result = client_runner(envelope, config) if client_runner else call_llm_once(envelope, config)
    else:
        result = _empty_client_result(config, blocked_reasons[0] if blocked_reasons else "blocked")

    output_safety = _safe_output_safety(result, env)
    packet: dict[str, Any] = {}
    if result.get("api_call_succeeded") and output_safety.get("allowed"):
        packet = build_llm_response_packet(
            _fake_packet_report(
                envelope,
                result,
                output_safety,
                allow_api_call=allow_api_call,
                actual_llm_api_call=actual_llm_api_call,
            )
        )
    llm_response_packet_created = bool(packet.get("packet_type") == "llm_response_packet")
    ready = bool(ready_to_attempt and result.get("api_call_succeeded") and output_safety.get("allowed") and llm_response_packet_created)
    report = {
        "report_type": "rag_evidence_llm_dry_call",
        "version": VERSION,
        "created_at": utc_now(),
        "prompt_envelope_available": bool(envelope),
        "manual_approval": manual_approval,
        "ready": ready,
        "blocked": not ready,
        "blocked_reasons": [] if ready else blocked_reasons or ["llm_output_not_ready"],
        "provider": config.get("provider", ""),
        "model": config.get("model", ""),
        "model_configured": bool(config.get("model")),
        "client_config": public_llm_client_config(config),
        "api_key_present": bool(config.get("api_key_present")),
        "api_key_value_logged": False,
        "actual_llm_api_call": actual_llm_api_call,
        "api_call_attempted": bool(result.get("api_call_attempted")),
        "api_call_succeeded": bool(result.get("api_call_succeeded")),
        "api_call_failed": bool(result.get("api_call_failed")),
        "client_result": result,
        "output_safety": {
            "allowed": bool(output_safety.get("allowed")),
            "blocked": bool(output_safety.get("blocked")),
            "blocked_reasons": output_safety.get("blocked_reasons", []),
            "safe_disclaimer_detected": bool(output_safety.get("safe_disclaimer_detected")),
            "safe_disclaimer_reasons": output_safety.get("safe_disclaimer_reasons", []),
            "reason": output_safety.get("reason", ""),
        },
        "llm_response_packet_created": llm_response_packet_created,
        "llm_response_packet": packet if llm_response_packet_created else {},
        "output_safety_allowed": bool(output_safety.get("allowed")),
        "ready_for_discord_send": False,
        "discord_message_sent": False,
        "discord_send_attempted": False,
        "embedding_api_called": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_llm_dry_call_safe(report)
    return report


def render_rag_evidence_llm_dry_call_markdown(report: dict[str, Any]) -> str:
    manual = report.get("manual_approval", {})
    return "\n".join(
        [
            "# STOXL RAG Evidence LLM Dry Call",
            "",
            f"- Version: {report.get('version', '')}",
            f"- Ready: {str(report.get('ready')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Blocked reasons: {', '.join(report.get('blocked_reasons', []))}",
            f"- Manual approval required: {str(manual.get('required')).lower()}",
            f"- Manual approval approved: {str(manual.get('approved')).lower()}",
            f"- Approval phrase present: {str(manual.get('approval_phrase_present')).lower()}",
            "- Approval phrase value logged: false",
            f"- Provider: {report.get('provider', '')}",
            f"- Model configured: {str(report.get('model_configured')).lower()}",
            f"- API key present: {str(report.get('api_key_present')).lower()}",
            "- API key value logged: false",
            f"- Actual LLM API call: {str(report.get('actual_llm_api_call')).lower()}",
            f"- API call attempted: {str(report.get('api_call_attempted')).lower()}",
            f"- API call succeeded: {str(report.get('api_call_succeeded')).lower()}",
            f"- LLM response packet created: {str(report.get('llm_response_packet_created')).lower()}",
            f"- Output safety allowed: {str(report.get('output_safety_allowed')).lower()}",
            "- Ready for Discord send: false",
            "- Discord message sent: false",
            "- Embedding API called: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_evidence_llm_dry_call_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if APPROVAL_PHRASE.lower() in text:
        raise ValueError("RAG evidence LLM dry call report contains approval phrase value.")
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence LLM dry call report contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence LLM dry call report contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in ("ready_for_discord_send", "discord_message_sent", "discord_send_attempted", "embedding_api_called", "external_execution"):
            if report.get(key):
                raise ValueError(f"RAG evidence LLM dry call unsafe flag is true: {key}")
        assertions = report.get("safety_assertions", {})
        for key in ("api_key_value_logged", "token_value_logged", "raw_discord_ids_logged", "embedding_called", "discord_message_sent", "external_execution"):
            if assertions.get(key):
                raise ValueError(f"RAG evidence LLM dry call unsafe assertion is true: {key}")
