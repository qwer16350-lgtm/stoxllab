"""Minimal Phase 32B LLM client boundary.

The default path is mock-only. A real provider call is attempted only when the
caller passes allow_api_call=True and every env gate is explicitly enabled.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


VERSION = "phase32b_private_test_dry_call"
SUPPORTED_PROVIDERS = {"openai", "openrouter"}
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def _int_value(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def redact_text(text: str | None, max_chars: int = 1200) -> str:
    if not text:
        return ""
    redacted = SECRET_RE.sub("[REDACTED_SECRET]", str(text))
    redacted = LONG_ID_RE.sub("[REDACTED_DISCORD_ID]", redacted)
    return redacted[:max(max_chars, 0)]


def build_llm_client_config(env: dict[str, Any] | None = None) -> dict[str, Any]:
    provider = _env_value(env, "HERMES_LLM_PROVIDER", "disabled").strip() or "disabled"
    model = _env_value(env, "HERMES_LLM_MODEL", "").strip()
    api_key = _env_value(env, "HERMES_LLM_API_KEY", "")
    base_url = _env_value(env, "HERMES_LLM_BASE_URL", "").strip()
    return {
        "config_type": "llm_client_config",
        "version": VERSION,
        "provider": provider,
        "model": model,
        "api_key_present": bool(api_key),
        "api_key_value_logged": False,
        "_api_key": api_key,
        "base_url_configured": bool(base_url),
        "_base_url": base_url,
        "timeout_seconds": _int_value(_env_value(env, "HERMES_LLM_TIMEOUT_SECONDS", "30"), 30),
        "temperature": _float_value(_env_value(env, "HERMES_LLM_TEMPERATURE", "0.2"), 0.2),
        "api_call_enabled": _flag(_env_value(env, "HERMES_LLM_API_CALL_ENABLED", "false")),
        "dry_call_mode": _env_value(env, "HERMES_LLM_DRY_CALL_MODE", "private_test_only"),
        "discord_send_enabled": _flag(_env_value(env, "HERMES_LLM_DISCORD_SEND_ENABLED", "false")),
        "discord_runtime_send_messages": _flag(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES", "false")),
        "rag_enabled": _flag(_env_value(env, "HERMES_DISCORD_RAG_ENABLED", "false")),
        "external_execution": _flag(_env_value(env, "HERMES_DISCORD_EXTERNAL_EXECUTION", "false")),
        "llm_enabled": _flag(_env_value(env, "HERMES_LLM_ENABLED", "false")),
        "private_test_only": _flag(_env_value(env, "HERMES_LLM_PRIVATE_TEST_ONLY", "true"), True),
        "cost_guard_enabled": _flag(_env_value(env, "HERMES_LLM_COST_GUARD_ENABLED", "true"), True),
        "max_output_chars": _int_value(_env_value(env, "HERMES_LLM_MAX_OUTPUT_CHARS", "1200"), 1200),
    }


def public_llm_client_config(config: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in config.items() if not key.startswith("_")}


def validate_llm_client_config(config: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    provider = str(config.get("provider", "disabled") or "disabled")
    if provider == "disabled":
        reasons.append("provider_disabled")
    elif provider not in SUPPORTED_PROVIDERS:
        reasons.append("unsupported_provider")
    if not config.get("llm_enabled"):
        reasons.append("llm_disabled")
    if not config.get("api_call_enabled"):
        reasons.append("api_call_disabled")
    if not config.get("model"):
        reasons.append("model_not_configured")
    if not config.get("api_key_present"):
        reasons.append("api_key_missing")
    if config.get("dry_call_mode") != "private_test_only":
        reasons.append("dry_call_mode_not_private_test_only")
    if config.get("discord_send_enabled") or config.get("discord_runtime_send_messages"):
        reasons.append("discord_send_enabled")
    if not config.get("private_test_only"):
        reasons.append("not_private_test_only")
    if not config.get("cost_guard_enabled"):
        reasons.append("cost_guard_disabled")
    if config.get("rag_enabled"):
        reasons.append("rag_enabled")
    if config.get("external_execution"):
        reasons.append("external_execution_enabled")
    if int(config.get("timeout_seconds", 0)) <= 0:
        reasons.append("invalid_timeout_seconds")
    if float(config.get("temperature", 0)) < 0:
        reasons.append("invalid_temperature")
    return {
        "validation_type": "llm_client_config_validation",
        "valid": not reasons,
        "blocked": bool(reasons),
        "blocked_reasons": reasons,
        "api_key_value_logged": False,
        "discord_message_sent": False,
        "rag_called": False,
        "external_execution": False,
    }


def _result(
    config: dict[str, Any],
    *,
    attempted: bool = False,
    succeeded: bool = False,
    failed: bool = False,
    error_type: str | None = None,
    response_text: str = "",
    input_chars: int = 0,
) -> dict[str, Any]:
    safe_response = redact_text(response_text, int(config.get("max_output_chars", 1200)))
    result = {
        "result_type": "llm_client_result",
        "version": VERSION,
        "provider": config.get("provider", ""),
        "model": config.get("model", ""),
        "api_call_attempted": attempted,
        "api_call_succeeded": succeeded,
        "api_call_failed": failed,
        "error_type": error_type,
        "response_text": safe_response,
        "usage": {
            "input_chars": input_chars,
            "output_chars": len(safe_response),
            "estimated_cost_krw": None,
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


def build_mock_llm_response(prompt_envelope: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_config = config or build_llm_client_config({})
    agent = prompt_envelope.get("agent_route_candidate", "marin")
    response = (
        f"[Mock LLM dry call] Agent {agent} can prepare a private-test review draft. "
        "Discord delivery is disabled, and external execution stays disabled."
    )
    input_chars = len(json.dumps(prompt_envelope, ensure_ascii=False))
    return _result(selected_config, response_text=response, input_chars=input_chars)


def _provider_url(config: dict[str, Any]) -> str:
    if config.get("_base_url"):
        return str(config["_base_url"]).rstrip("/")
    if config.get("provider") == "openrouter":
        return "https://openrouter.ai/api/v1/chat/completions"
    return "https://api.openai.com/v1/chat/completions"


def call_llm_once(prompt_envelope: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    validation = validate_llm_client_config(config)
    if validation["blocked"]:
        return _result(config, failed=True, error_type="client_config_blocked")

    payload = {
        "model": config.get("model", ""),
        "messages": prompt_envelope.get("messages_preview", []),
        "temperature": config.get("temperature", 0.2),
    }
    request = urllib.request.Request(
        _provider_url(config),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + str(config.get("_api_key", "")),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=int(config.get("timeout_seconds", 30))) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return _result(config, attempted=True, failed=True, error_type=f"http_error_{exc.code}")
    except urllib.error.URLError:
        return _result(config, attempted=True, failed=True, error_type="url_error")
    except TimeoutError:
        return _result(config, attempted=True, failed=True, error_type="timeout")
    except Exception:
        return _result(config, attempted=True, failed=True, error_type="provider_error")

    text = ""
    try:
        text = str(body.get("choices", [{}])[0].get("message", {}).get("content", "") or "")
    except (AttributeError, IndexError):
        text = ""
    input_chars = len(json.dumps(prompt_envelope, ensure_ascii=False))
    return _result(config, attempted=True, succeeded=True, response_text=text, input_chars=input_chars)


def assert_llm_client_result_safe(result: dict[str, Any]) -> None:
    text = json.dumps(result, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("LLM client result contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("LLM client result contains raw Discord-like IDs.")
    assertions = result.get("safety_assertions", {})
    for key in ("api_key_value_logged", "discord_message_sent", "rag_called", "external_execution", "raw_discord_ids_logged"):
        if assertions.get(key):
            raise ValueError(f"LLM client result unsafe assertion is true: {key}")
