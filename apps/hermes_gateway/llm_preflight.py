"""Local-only LLM safety preflight for Phase 32A."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any


VERSION = "phase32a_no_api_call"
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+)")
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def build_llm_preflight_policy(env: dict[str, Any] | None = None) -> dict[str, Any]:
    provider = _env_value(env, "HERMES_LLM_PROVIDER", "disabled").strip() or "disabled"
    model = _env_value(env, "HERMES_LLM_MODEL", "").strip()
    api_key = _env_value(env, "HERMES_LLM_API_KEY", "")
    return {
        "policy_type": "llm_preflight_policy",
        "version": VERSION,
        "llm_enabled": _flag(_env_value(env, "HERMES_LLM_ENABLED", "false")),
        "provider": provider,
        "model_configured": bool(model),
        "api_key_present": bool(api_key),
        "dry_run_only": _flag(_env_value(env, "HERMES_LLM_DRY_RUN_ONLY", "true"), True),
        "private_test_only": _flag(_env_value(env, "HERMES_LLM_PRIVATE_TEST_ONLY", "true"), True),
        "discord_send_allowed": _flag(_env_value(env, "HERMES_LLM_ALLOW_DISCORD_SEND", "false")),
        "max_input_chars": _int_value(_env_value(env, "HERMES_LLM_MAX_INPUT_CHARS", "4000"), 4000),
        "max_output_chars": _int_value(_env_value(env, "HERMES_LLM_MAX_OUTPUT_CHARS", "1200"), 1200),
        "max_calls_per_session": _int_value(_env_value(env, "HERMES_LLM_MAX_CALLS_PER_SESSION", "3"), 3),
        "cost_guard_enabled": _flag(_env_value(env, "HERMES_LLM_COST_GUARD_ENABLED", "true"), True),
    }


def run_llm_preflight(env: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = build_llm_preflight_policy(env)
    blocked_reasons: list[str] = []
    if not policy["llm_enabled"]:
        blocked_reasons.append("llm_disabled")
    if policy["provider"] == "disabled":
        blocked_reasons.append("provider_disabled")
    if not policy["model_configured"]:
        blocked_reasons.append("model_not_configured")
    if not policy["api_key_present"]:
        blocked_reasons.append("api_key_missing")
    if policy["dry_run_only"]:
        blocked_reasons.append("dry_run_only_enabled")
    if not policy["private_test_only"]:
        blocked_reasons.append("not_private_test_only")
    if policy["discord_send_allowed"]:
        blocked_reasons.append("discord_send_allowed")
    if not policy["cost_guard_enabled"]:
        blocked_reasons.append("cost_guard_disabled")
    if policy["max_input_chars"] <= 0:
        blocked_reasons.append("invalid_max_input_chars")
    if policy["max_output_chars"] <= 0:
        blocked_reasons.append("invalid_max_output_chars")
    if policy["max_calls_per_session"] <= 0:
        blocked_reasons.append("invalid_max_calls_per_session")

    return {
        "llm_enabled": policy["llm_enabled"],
        "provider": policy["provider"],
        "model_configured": policy["model_configured"],
        "api_key_present": policy["api_key_present"],
        "dry_run_only": policy["dry_run_only"],
        "private_test_only": policy["private_test_only"],
        "discord_send_allowed": policy["discord_send_allowed"],
        "max_input_chars": policy["max_input_chars"],
        "max_output_chars": policy["max_output_chars"],
        "max_calls_per_session": policy["max_calls_per_session"],
        "cost_guard_enabled": policy["cost_guard_enabled"],
        "ready_for_llm_call": False,
        "blocked": bool(blocked_reasons),
        "blocked_reasons": blocked_reasons,
    }


def build_llm_preflight_report(env: dict[str, Any] | None = None) -> dict[str, Any]:
    result = run_llm_preflight(env)
    report = {
        "report_type": "llm_preflight_report",
        "version": VERSION,
        "created_at": utc_now(),
        **result,
        "safety_assertions": {
            "api_key_value_logged": False,
            "llm_api_called": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }
    assert_llm_preflight_safe(report)
    return report


def assert_llm_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("LLM preflight report contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("LLM preflight report contains raw Discord-like IDs.")
    assertions = report.get("safety_assertions", {})
    for key in ("api_key_value_logged", "llm_api_called", "discord_message_sent", "rag_called", "external_execution", "raw_discord_ids_logged"):
        if assertions.get(key):
            raise ValueError(f"LLM preflight unsafe assertion is true: {key}")


def render_llm_preflight_markdown(report: dict[str, Any]) -> str:
    reasons = report.get("blocked_reasons", [])
    reason_lines = [f"- {reason}" for reason in reasons] or ["- none"]
    return "\n".join(
        [
            "# LLM Safety Preflight Report",
            "",
            f"- version: {report.get('version', '')}",
            f"- llm_enabled: {str(report.get('llm_enabled')).lower()}",
            f"- provider: {report.get('provider', '')}",
            f"- model_configured: {str(report.get('model_configured')).lower()}",
            f"- api_key_present: {str(report.get('api_key_present')).lower()}",
            f"- dry_run_only: {str(report.get('dry_run_only')).lower()}",
            f"- private_test_only: {str(report.get('private_test_only')).lower()}",
            f"- discord_send_allowed: {str(report.get('discord_send_allowed')).lower()}",
            f"- ready_for_llm_call: {str(report.get('ready_for_llm_call')).lower()}",
            f"- blocked: {str(report.get('blocked')).lower()}",
            "",
            "## Blocked Reasons",
            *reason_lines,
            "",
            "## Safety",
            "- api_key_value_logged: false",
            "- llm_api_called: false",
            "- discord_message_sent: false",
            "- rag_called: false",
            "- external_execution: false",
        ]
    ) + "\n"
