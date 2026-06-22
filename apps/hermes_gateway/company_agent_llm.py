"""Per-agent LLM response mode for STOXL company agents."""

from __future__ import annotations

import os
from typing import Any, Callable

from company_agent_prompts import agent_prompts_available, get_agent_system_prompt
from llm_client import build_llm_client_config, call_llm_once, public_llm_client_config, redact_text


SUPPORTED_LLM_MODES = ["off", "manual_command_only"]
OPENROUTER_KEY_ALIASES = ["HERMES_LLM_API_KEY", "OPENROUTER_API_KEY", "HERMES_OPENROUTER_API_KEY"]


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _env(env: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict(os.environ if env is None else env)


def _company_llm_mode(env: dict[str, Any] | None = None) -> str:
    mode = str(_env(env).get("HERMES_COMPANY_AGENT_LLM_MODE", "off") or "off").strip().lower()
    return mode if mode in SUPPORTED_LLM_MODES else "off"


def is_company_agent_llm_enabled(env: dict[str, Any] | None = None) -> bool:
    env_map = _env(env)
    return _flag(env_map.get("HERMES_COMPANY_AGENT_LLM_ENABLED", "false")) and _company_llm_mode(env_map) == "manual_command_only"


def is_manual_command(message: str, context: dict[str, Any] | None = None) -> bool:
    if context and context.get("command"):
        return True
    return str(message or "").lstrip().startswith("!")


def _api_key(env: dict[str, Any]) -> str:
    for key in OPENROUTER_KEY_ALIASES:
        value = str(env.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _llm_config(env: dict[str, Any] | None = None) -> dict[str, Any]:
    env_map = _env(env)
    merged = dict(env_map)
    if not merged.get("HERMES_LLM_PROVIDER"):
        merged["HERMES_LLM_PROVIDER"] = merged.get("HERMES_COMPANY_AGENT_LLM_PROVIDER", "openrouter")
    if not merged.get("HERMES_LLM_MODEL"):
        merged["HERMES_LLM_MODEL"] = merged.get("HERMES_COMPANY_AGENT_LLM_MODEL", "openai/gpt-5.4-mini")
    if not merged.get("HERMES_LLM_API_KEY"):
        merged["HERMES_LLM_API_KEY"] = _api_key(merged)
    merged["HERMES_LLM_ENABLED"] = "true"
    merged["HERMES_LLM_API_CALL_ENABLED"] = "true"
    merged["HERMES_LLM_PRIVATE_TEST_ONLY"] = "true"
    merged["HERMES_LLM_DRY_CALL_MODE"] = "private_test_only"
    merged["HERMES_LLM_DISCORD_SEND_ENABLED"] = "false"
    merged["HERMES_DISCORD_SEND_MESSAGES"] = "false"
    merged["HERMES_DISCORD_RAG_ENABLED"] = "false"
    merged["HERMES_DISCORD_EXTERNAL_EXECUTION"] = "false"
    return build_llm_client_config(merged)


def build_agent_llm_messages(agent_id: str, user_message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    safe_user = redact_text(user_message, 1200)
    route_context = context or {}
    return {
        "envelope_type": "company_agent_llm_prompt",
        "agent_id": agent_id,
        "manual_command": is_manual_command(user_message, route_context),
        "messages_preview": [
            {"role": "system", "content": get_agent_system_prompt(agent_id)},
            {
                "role": "user",
                "content": (
                    f"Channel: {route_context.get('source_channel', '')}\n"
                    f"Request: {safe_user}\n\n"
                    "Stay inside the assigned role. Do not perform external execution."
                ),
            },
        ],
        "rag_called": False,
        "embedding_called": False,
        "external_execution": False,
        "secret_values_logged": False,
        "raw_discord_ids_logged": False,
    }


def build_company_agent_llm_report(env: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "report_type": "company_agent_llm_report",
        "company_agent_llm_available": True,
        "default_llm_enabled": False,
        "default_llm_mode": "off",
        "current_llm_enabled": is_company_agent_llm_enabled(env),
        "current_llm_mode": _company_llm_mode(env),
        "supported_llm_modes": list(SUPPORTED_LLM_MODES),
        "agent_prompts_available": agent_prompts_available(),
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution_allowed": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_company_agent_llm_dry_run(agent_id: str, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    prompt = build_agent_llm_messages(agent_id, message, context)
    return {
        "report_type": "company_agent_llm_dry_run",
        "selected_agent": agent_id,
        "prompt_available": bool(prompt["messages_preview"][0]["content"]),
        "manual_command": bool(prompt["manual_command"]),
        "would_attempt_llm": bool(prompt["manual_command"]),
        "actual_llm_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "external_execution_performed": False,
        "fallback_available": True,
        "prompt_secret_values_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "messages_preview": prompt["messages_preview"],
    }


def generate_agent_reply(
    agent_id: str,
    user_message: str,
    context: dict[str, Any] | None = None,
    env: dict[str, Any] | None = None,
    *,
    allow_llm_call: bool | None = None,
    llm_caller: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    prompt = build_agent_llm_messages(agent_id, user_message, context)
    enabled = is_company_agent_llm_enabled(env)
    manual = bool(prompt["manual_command"])
    should_call = enabled and manual and (True if allow_llm_call is None else bool(allow_llm_call))
    if not should_call:
        return {
            "llm_attempted": False,
            "llm_succeeded": False,
            "fallback_used": "deterministic",
            "blocked_reasons": [] if manual else ["not_manual_command"],
            "prompt_envelope": prompt,
            "rag_called": False,
            "embedding_called": False,
            "external_execution": False,
            "api_key_value_logged": False,
            "secret_values_logged": False,
            "raw_discord_ids_logged": False,
        }
    config = _llm_config(env)
    caller = llm_caller or call_llm_once
    try:
        result = caller(prompt, config)
    except Exception as exc:
        result = {
            "api_call_attempted": True,
            "api_call_succeeded": False,
            "api_call_failed": True,
            "error_type": exc.__class__.__name__,
        }
    text = redact_text(str(result.get("response_text", "") or ""), 1200)
    succeeded = bool(result.get("api_call_succeeded")) and bool(text)
    return {
        "llm_attempted": True,
        "llm_succeeded": succeeded,
        "llm_api_called": bool(result.get("api_call_attempted")),
        "fallback_used": None if succeeded else "deterministic",
        "response_text": text if succeeded else "",
        "client_result": {key: value for key, value in result.items() if key != "response_text"},
        "llm_config": public_llm_client_config(config),
        "prompt_envelope": prompt,
        "rag_called": False,
        "embedding_called": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "secret_values_logged": False,
        "raw_discord_ids_logged": False,
    }


def build_company_agent_llm_one_shot(
    agent_id: str,
    message: str,
    *,
    allow_company_agent_llm_call: bool = False,
    env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = generate_agent_reply(
        agent_id,
        message,
        {"command": agent_id, "source_channel": "cli_one_shot"},
        env,
        allow_llm_call=allow_company_agent_llm_call,
    )
    fallback_preview = f"{agent_id}_deterministic_template_available"
    response_preview = result.get("response_text", "") or (fallback_preview if result.get("fallback_used") == "deterministic" else "")
    return {
        "report_type": "company_agent_llm_one_shot",
        "selected_agent": agent_id,
        "allow_company_agent_llm_call": bool(allow_company_agent_llm_call),
        "llm_attempted": bool(result.get("llm_attempted")),
        "llm_succeeded": bool(result.get("llm_succeeded")),
        "fallback_used": result.get("fallback_used") or "",
        "response_preview": response_preview,
        "fallback_preview_available": bool(result.get("fallback_used") == "deterministic"),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }
