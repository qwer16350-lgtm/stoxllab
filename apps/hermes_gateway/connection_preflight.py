"""Final local preflight before a future read-only Discord connection.

This module does not connect to Discord, read a bot token, inspect OS
environment values, read .env, or send messages.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from local_mapping_manager import build_local_mapping_manager_report


VERSION = "phase23_no_connection"
REQUIRED_ENV_KEYS = [
    "DISCORD_BOT_TOKEN",
    "DISCORD_GUILD_ID",
    "OWNER_KIM_DISCORD_ID",
    "OWNER_LEE_DISCORD_ID",
    "HERMES_CONFIG_PATH",
]
DISCORD_DEPENDENCY_NAMES = ("discord.py", "nextcord", "py-cord", "discord.js")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _check(check_id: str, status: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"check_id": check_id, "status": status, "message": message, "details": details or {}}


def build_dependency_plan() -> dict[str, Any]:
    return {
        "recommended_runtime": "python",
        "recommended_library": "discord.py",
        "alternatives": ["nextcord", "py-cord"],
        "install_now": False,
        "reason": "Phase 23 is planning-only. Install a Discord library only in a later approved read-only runtime phase.",
        "minimum_future_permissions": [
            "private test server only",
            "read-only channel access",
            "no send messages permission",
            "no manage channels permission",
            "no manage roles permission",
        ],
        "required_intents": {
            "guilds": True,
            "guild_messages": True,
            "message_content": "manual_review_required",
            "reactions": "later",
            "members": "later",
            "slash_commands": "later",
        },
        "phase24_rule": {
            "connect_gateway": False,
            "send_messages": False,
            "external_execution": False,
            "read_env_token": False,
            "log_token": False,
        },
    }


def _read_env_example_keys(root: str | Path) -> set[str]:
    path = Path(root) / ".env.example"
    keys: set[str] = set()
    if not path.exists():
        return keys
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.add(line.split("=", 1)[0].strip())
    return keys


def load_local_mapping_validation(root: str | Path) -> dict[str, Any]:
    report = build_local_mapping_manager_report(root, strict=True)
    summary = report.get("validation_summary", {})
    return {
        "ready_for_readonly_connection": bool(report.get("ready_for_readonly_connection")),
        "local_mapping_exists": bool(report.get("local_mapping_exists")),
        "validated": bool(report.get("validated")),
        "overall_valid": report.get("validation_overall_valid"),
        "manual_required_count": report.get("validation_manual_required_count"),
        "missing_mapping_count": report.get("validation_missing_mapping_count"),
        "todo_placeholders": summary.get("todo_placeholders"),
        "secret_like_values": summary.get("secret_like_values"),
        "blocked_reasons": list(report.get("blocked_reasons", [])),
        "warnings": list(report.get("warnings", [])),
    }


def check_env_key_names(root: str | Path) -> dict[str, Any]:
    keys = _read_env_example_keys(root)
    missing = [key for key in REQUIRED_ENV_KEYS if key not in keys]
    return _check(
        "required_env_key_names_documented",
        "pass" if not missing else "fail",
        "Required env key names are documented in .env.example." if not missing else "Required env key names are missing from .env.example.",
        {"required_env_keys": REQUIRED_ENV_KEYS, "missing_keys": missing, "env_file_read": False, "os_env_values_read": False},
    )


def _gitignore_contains(root: str | Path, text: str) -> bool:
    path = Path(root) / ".gitignore"
    if not path.exists():
        return False
    return text in path.read_text(encoding="utf-8")


def check_gitignore_protection(root: str | Path) -> dict[str, Any]:
    required_patterns = [
        "apps/hermes_gateway/local/*",
        "!apps/hermes_gateway/local/.gitkeep",
        "!apps/hermes_gateway/local/README.md",
        "logs/hermes_gateway/",
        "exports/hermes_gateway/",
    ]
    missing = [pattern for pattern in required_patterns if not _gitignore_contains(root, pattern)]
    return _check(
        "gitignore_runtime_artifact_protection",
        "pass" if not missing else "fail",
        "Local mapping, logs, and exports are protected by .gitignore." if not missing else "Some runtime artifact protection rules are missing.",
        {
            "local_mapping_gitignored": "apps/hermes_gateway/local/*" not in missing,
            "logs_gitignored": "logs/hermes_gateway/" not in missing,
            "exports_gitignored": "exports/hermes_gateway/" not in missing,
            "missing_patterns": missing,
        },
    )


def _project_dependency_mentions(root: str | Path) -> list[str]:
    repo_root = Path(root)
    candidates = [
        repo_root / "requirements.txt",
        repo_root / "pyproject.toml",
        repo_root / "package.json",
        repo_root / "apps" / "hermes_gateway" / "requirements.txt",
        repo_root / "apps" / "hermes_gateway" / "pyproject.toml",
        repo_root / "apps" / "hermes_gateway" / "package.json",
    ]
    mentions: list[str] = []
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for name in DISCORD_DEPENDENCY_NAMES:
            if name.lower() in text:
                mentions.append(f"{path.relative_to(repo_root)}:{name}")
    return mentions


def check_readonly_safety_flags(root: str | Path) -> dict[str, Any]:
    dependency_mentions = _project_dependency_mentions(root)
    safety = {
        "message_send_disabled": True,
        "external_execution_disabled": True,
        "human_only_execution_preserved": True,
        "discord_dependency_declared_now": bool(dependency_mentions),
    }
    failed = []
    if dependency_mentions:
        failed.append("discord_dependency_declared_now")
    return _check(
        "readonly_safety_flags",
        "pass" if not failed else "fail",
        "Read-only safety flags are preserved." if not failed else "Read-only preflight found unsafe project state.",
        {"failed": failed, "dependency_mentions": dependency_mentions, **safety},
    )


def _local_mapping_check(root: str | Path) -> dict[str, Any]:
    validation = load_local_mapping_validation(root)
    missing = []
    if not validation["ready_for_readonly_connection"]:
        missing.append("ready_for_readonly_connection=true")
    if validation.get("secret_like_values") != 0:
        missing.append("secret_like_values=0")
    if validation.get("todo_placeholders") != 0:
        missing.append("todo_placeholders=0")
    return _check(
        "local_mapping_strict_validation",
        "pass" if not missing else "fail",
        "Local mapping strict validation is ready for read-only connection." if not missing else "Local mapping strict validation is not ready.",
        {"missing": missing, **validation},
    )


def _manual_checks() -> list[dict[str, Any]]:
    return [
        _check("all_local_tests_passed", "manual_required", "Confirm the full local test suite passed immediately before Phase 24.", {}),
        _check("private_server_scope_confirmed", "manual_required", "Confirm the target Discord server is a private test server.", {}),
        _check("bot_role_readonly_confirmed", "manual_required", "Confirm the future bot role cannot send messages or manage server resources.", {}),
        _check("rollback_plan_reviewed", "manual_required", "Confirm rollback and token rotation procedures have been reviewed.", {}),
    ]


def build_connection_preflight_report(root: str | Path, strict: bool = True) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    dependency_plan = build_dependency_plan()
    checks = [
        _local_mapping_check(repo_root),
        check_env_key_names(repo_root),
        check_gitignore_protection(repo_root),
        check_readonly_safety_flags(repo_root),
    ]
    blocked_reasons = [check["message"] for check in checks if check["status"] == "fail"]
    warnings = [check["message"] for check in checks if check["status"] == "warn"]
    required_conditions_met = not blocked_reasons
    return {
        "report_type": "readonly_discord_connection_preflight",
        "version": VERSION,
        "created_at": utc_now(),
        "root": str(repo_root),
        "strict": strict,
        "ready_for_phase24_readonly_connection": required_conditions_met,
        "checks": checks,
        "manual_checks": _manual_checks(),
        "blocked_reasons": blocked_reasons,
        "warnings": warnings,
        "dependency_plan": dependency_plan,
        "required_env_keys": REQUIRED_ENV_KEYS,
        "safety_assertions": {
            "discord_api_called": False,
            "gateway_connected": False,
            "bot_token_value_read": False,
            "env_file_read": False,
            "message_sent": False,
            "external_execution_enabled": False,
            "human_only_execution_preserved": True,
        },
    }


def assert_ready_for_phase24(report: dict[str, Any]) -> None:
    if report.get("ready_for_phase24_readonly_connection") is not True:
        reasons = "; ".join(report.get("blocked_reasons", [])) or "preflight report is not ready"
        raise ValueError(reasons)
