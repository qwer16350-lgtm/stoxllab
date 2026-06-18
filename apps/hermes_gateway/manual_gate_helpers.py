"""Shared Manual Gate helpers for report-only Hermes phases.

Helpers in this module return booleans, integers, condition names, or redacted
presence summaries only. They never return secret, token, channel, or approval
phrase values.
"""

from __future__ import annotations

import os
from typing import Any, Mapping


def env_present(env: Mapping[str, str] | None, key: str) -> bool:
    selected = env if env is not None else os.environ
    return bool(selected.get(key, "").strip())


def env_true(env: Mapping[str, str] | None, key: str) -> bool:
    selected = env if env is not None else os.environ
    return selected.get(key, "").strip().lower() in {"1", "true", "yes", "on"}


def env_int(env: Mapping[str, str] | None, key: str, default: int | None = None) -> int | None:
    selected = env if env is not None else os.environ
    try:
        return int(selected.get(key, "").strip())
    except ValueError:
        return default


def redacted_presence_report(env: Mapping[str, str] | None, keys: list[str] | tuple[str, ...]) -> dict[str, bool]:
    return {f"{key.lower()}_present": env_present(env, key) for key in keys}


def approval_gate_report(
    env: Mapping[str, str] | None,
    approved_key: str,
    phrase_key: str,
    expected_phrase: str,
) -> dict[str, bool]:
    selected = env if env is not None else os.environ
    phrase = selected.get(phrase_key, "")
    return {
        "manual_approval_true": env_true(env, approved_key),
        "approval_phrase_present": bool(phrase.strip()),
        "approval_phrase_exact_match": phrase == expected_phrase,
        "approval_phrase_value_logged": False,
    }


def assert_reply_mode(env: Mapping[str, str] | None, expected_mode: str) -> bool:
    selected = env if env is not None else os.environ
    return selected.get("HERMES_DISCORD_REPLY_MODE", "") == expected_mode


def assert_disabled_flags(env: Mapping[str, str] | None, flag_keys: list[str] | tuple[str, ...]) -> bool:
    return all(not env_true(env, key) for key in flag_keys)


def build_blocked_reasons(required_conditions: Mapping[str, bool]) -> list[str]:
    return [reason for reason, passed in required_conditions.items() if not passed]


def consumed_lock_blocked_reasons(already_consumed: bool, blocked_reason: str) -> list[str]:
    return [blocked_reason] if already_consumed else []
