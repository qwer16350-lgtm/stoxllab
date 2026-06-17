"""Phase 45A actual LLM one-shot call preflight gate."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Mapping


VERSION = "phase45_actual_llm_one_shot_preflight"
_EXPECTED_APPROVAL_PHRASE = "I_APPROVE_PHASE45A_ACTUAL_LLM_ONE_SHOT"
_SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|api[_ -]?key\s*[:=]\s*\S+|bearer\s+\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
_APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _truthy(env: Mapping[str, str], key: str) -> bool:
    return str(env.get(key, "")).strip().lower() == "true"


def _present(env: Mapping[str, str], key: str) -> bool:
    return bool(str(env.get(key, "")).strip())


def build_phase45_actual_llm_one_shot_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if env is None else env
    manual_approval_present = _present(env, "HERMES_PHASE45A_MANUAL_APPROVAL")
    manual_approval_true = _truthy(env, "HERMES_PHASE45A_MANUAL_APPROVAL")
    approval_phrase_present = _present(env, "HERMES_PHASE45A_APPROVAL_PHRASE")
    approval_phrase_match = str(env.get("HERMES_PHASE45A_APPROVAL_PHRASE", "")) == _EXPECTED_APPROVAL_PHRASE
    cost_guard_present = _truthy(env, "HERMES_PHASE45A_COST_GUARD")
    call_count_guard_present = _truthy(env, "HERMES_PHASE45A_CALL_COUNT_GUARD")
    discord_send_false = not _truthy(env, "HERMES_DISCORD_SEND_MESSAGES")
    private_test_discord_send_false = not _truthy(env, "HERMES_DISCORD_PRIVATE_TEST_SEND")
    key_present = _present(env, "HERMES_LLM_API_KEY") or _present(env, "OPENROUTER_API_KEY") or _present(env, "HERMES_OPENROUTER_API_KEY")
    provider_config_present = _present(env, "HERMES_LLM_PROVIDER") or _present(env, "OPENROUTER_PROVIDER")
    model_config_present = _present(env, "HERMES_LLM_MODEL") or _present(env, "OPENROUTER_MODEL")
    base_url_present = _present(env, "HERMES_LLM_BASE_URL")
    llm_disabled_for_bundle = not _truthy(env, "HERMES_LLM_API_CALL_ENABLED")
    rag_disabled = not _truthy(env, "HERMES_DISCORD_RAG_ENABLED") and not _truthy(env, "HERMES_LLM_RAG_ENABLED")
    embedding_disabled = not _truthy(env, "HERMES_EMBEDDING_ENABLED") and not _truthy(env, "HERMES_VECTOR_ENABLED")
    external_disabled = not _truthy(env, "HERMES_DISCORD_EXTERNAL_EXECUTION")
    checks = {
        "api_key_present": key_present,
        "provider_config_present": provider_config_present,
        "model_config_present": model_config_present,
        "base_url_present": base_url_present,
        "discord_send_disabled": discord_send_false,
        "private_test_discord_send_disabled": private_test_discord_send_false,
        "llm_actual_call_disabled_until_allow_flag": llm_disabled_for_bundle,
        "rag_disabled": rag_disabled,
        "embedding_vector_disabled": embedding_disabled,
        "external_execution_disabled": external_disabled,
    }
    readiness_checks = {
        "manual_approval_missing": manual_approval_true,
        "approval_phrase_mismatch": approval_phrase_match,
        "cost_guard_missing": cost_guard_present,
        "call_count_guard_missing": call_count_guard_present,
        "api_key_missing": key_present,
        "provider_config_missing": provider_config_present,
        "model_config_missing": model_config_present,
        "base_url_missing": base_url_present,
        "discord_send_enabled": discord_send_false,
        "private_test_discord_send_enabled": private_test_discord_send_false,
        "llm_api_call_enabled_in_safe_bundle": llm_disabled_for_bundle,
        "rag_enabled": rag_disabled,
        "embedding_or_vector_enabled": embedding_disabled,
        "external_execution_enabled": external_disabled,
    }
    gates_ready = all(readiness_checks.values())
    report = {
        "report_type": "phase45_actual_llm_one_shot_preflight",
        "version": VERSION,
        "default_blocked": True,
        "blocked": not gates_ready,
        "blocked_reasons": [key for key, value in readiness_checks.items() if not value],
        "manual_approval_required": True,
        "manual_approval_present": manual_approval_present,
        "manual_approval_true": manual_approval_true,
        "approval_phrase_required": True,
        "approval_phrase_present": approval_phrase_present,
        "approval_phrase_exact_match": approval_phrase_match,
        "ready_for_actual_llm_one_shot_manual_gate": gates_ready,
        "ready_for_actual_llm_one_shot_call": gates_ready,
        "gate_checks": checks,
        "api_key_present": key_present,
        "openrouter_api_key_present": key_present,
        "api_key_value_logged": False,
        "approval_phrase_value_logged": False,
        "provider_config_present": provider_config_present,
        "model_config_present": model_config_present,
        "base_url_present": base_url_present,
        "provider_config_value_logged": False,
        "model_config_value_logged": False,
        "base_url_value_logged": False,
        "allow_actual_llm_call_flag_present": False,
        "actual_llm_api_call": False,
        "actual_llm_api_call_attempted": False,
        "actual_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_call_count": 0,
        "discord_send_allowed": False,
        "private_test_discord_send_allowed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase45_preflight_safe(report)
    return report


def build_phase45_llm_env_diagnostics(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if env is None else env
    report = {
        "report_type": "phase45_llm_env_diagnostics",
        "api_key_present": _present(env, "HERMES_LLM_API_KEY") or _present(env, "OPENROUTER_API_KEY") or _present(env, "HERMES_OPENROUTER_API_KEY"),
        "api_key_value_logged": False,
        "provider_config_present": _present(env, "HERMES_LLM_PROVIDER") or _present(env, "OPENROUTER_PROVIDER"),
        "provider_config_value_logged": False,
        "model_config_present": _present(env, "HERMES_LLM_MODEL") or _present(env, "OPENROUTER_MODEL"),
        "model_config_value_logged": False,
        "base_url_present": _present(env, "HERMES_LLM_BASE_URL"),
        "base_url_value_logged": False,
        "discord_send_disabled": not _truthy(env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_discord_send_disabled": not _truthy(env, "HERMES_DISCORD_PRIVATE_TEST_SEND"),
        "rag_disabled": not _truthy(env, "HERMES_DISCORD_RAG_ENABLED") and not _truthy(env, "HERMES_LLM_RAG_ENABLED"),
        "embedding_vector_disabled": not _truthy(env, "HERMES_EMBEDDING_ENABLED") and not _truthy(env, "HERMES_VECTOR_ENABLED"),
        "external_execution_disabled": not _truthy(env, "HERMES_DISCORD_EXTERNAL_EXECUTION"),
        "actual_llm_api_call_attempted": False,
        "actual_llm_api_called": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
    }
    assert_phase45_preflight_safe(report)
    return report


def assert_phase45_preflight_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if _SECRET_RE.search(text) or _APPROVAL_RE.search(text):
        raise ValueError("Phase 45A preflight contains a sensitive value.")
    for key in (
        "actual_llm_api_call",
        "actual_llm_api_call_attempted",
        "actual_llm_api_called",
        "llm_api_call_attempted",
        "discord_send_allowed",
        "private_test_discord_send_allowed",
        "discord_api_send_called",
        "discord_message_sent",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "api_key_value_logged",
        "approval_phrase_value_logged",
        "provider_config_value_logged",
        "model_config_value_logged",
        "base_url_value_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 45A unsafe flag is true: {key}")


def render_phase45_llm_env_diagnostics_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 45A LLM Env Diagnostics",
            "",
            f"- API key present: {str(report.get('api_key_present')).lower()}",
            f"- Provider config present: {str(report.get('provider_config_present')).lower()}",
            f"- Model config present: {str(report.get('model_config_present')).lower()}",
            f"- Base URL present: {str(report.get('base_url_present')).lower()}",
            f"- Discord send disabled: {str(report.get('discord_send_disabled')).lower()}",
            "- Actual LLM API attempt: false",
        ]
    ) + "\n"


def render_phase45_actual_llm_one_shot_preflight_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 45A Actual LLM One-shot Preflight",
            "",
            "- Default blocked: true",
            "- Actual LLM API call: false",
            "- LLM API attempt: false",
            "- Discord send allowed: false",
            f"- Ready for actual LLM one-shot call: {str(report.get('ready_for_actual_llm_one_shot_call')).lower()}",
        ]
    ) + "\n"
