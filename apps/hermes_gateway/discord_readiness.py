"""Read-only Discord readiness checks for Phase 17.

This module never calls Discord APIs, never opens a Gateway connection, and never
requires a real bot token value.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REGISTRY_PATH = "registry/stoxl_agent_registry.example.json"
DEFAULT_MAPPING_PATH = "apps/hermes_gateway/examples/discord_runtime_mapping.template.json"
REQUIRED_ROLES = {
    "Decision Maker",
    "Lucy",
    "Marin",
    "Meiko",
    "Kasumi",
    "Reze",
    "Human Operator",
    "Read Only Bot",
}
REQUIRED_OWNER_KEYS = {"OWNER_KIM_DISCORD_ID", "OWNER_LEE_DISCORD_ID"}
REQUIRED_APPROVAL_CHANNEL = "최종-승인요청"
SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "mfa.", "Bot ", "Bearer ")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def find_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "config" / "stoxl").exists() and (candidate / "registry").exists():
            return candidate
    raise RuntimeError("Could not find STOXL repo root.")


def load_env_example_keys(root: str | Path) -> set[str]:
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


def load_registry(root: str | Path) -> dict[str, Any]:
    path = Path(root) / REGISTRY_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def load_mapping_template(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_required_discord_keys() -> list[str]:
    return [
        "DISCORD_BOT_TOKEN",
        "DISCORD_GUILD_ID",
        "OWNER_KIM_DISCORD_ID",
        "OWNER_LEE_DISCORD_ID",
        "HERMES_CONFIG_PATH",
    ]


def check_required_env_keys(env_example_keys: set[str]) -> dict[str, Any]:
    required = build_required_discord_keys()
    missing = [key for key in required if key not in env_example_keys]
    return {
        "check_id": "required_env_keys_documented",
        "status": "pass" if not missing else "manual_required",
        "message": "Required Discord env key names are documented in .env.example." if not missing else "Some required Discord env key names are missing from .env.example.",
        "details": {"required_keys": required, "missing_keys": missing},
    }


def check_channel_mapping(registry: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    registry_channels = set(registry.get("channels", {}).keys())
    mapped_channels = set(mapping.get("channels", {}).keys())
    missing = sorted(registry_channels - mapped_channels)
    approval_present = REQUIRED_APPROVAL_CHANNEL in mapped_channels
    bad_placeholders = [
        name
        for name, item in mapping.get("channels", {}).items()
        if not str(item.get("channel_id_placeholder", "")).startswith("TODO_CHANNEL_ID_")
    ]
    status = "pass" if not missing and approval_present and not bad_placeholders else "manual_required"
    return {
        "check_id": "channel_mapping_template_complete",
        "status": status,
        "message": "Mapping template covers registry channels." if status == "pass" else "Mapping template needs channel mapping review.",
        "details": {
            "registry_channel_count": len(registry_channels),
            "mapped_channel_count": len(mapped_channels),
            "missing_channels": missing,
            "approval_channel_present": approval_present,
            "bad_placeholders": bad_placeholders,
        },
    }


def check_role_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    roles = mapping.get("roles", {})
    missing = sorted(REQUIRED_ROLES - set(roles.keys()))
    bad_placeholders = [
        name
        for name, item in roles.items()
        if not str(item.get("role_id_placeholder", "")).startswith("TODO_ROLE_ID_")
    ]
    status = "pass" if not missing and not bad_placeholders else "manual_required"
    return {
        "check_id": "role_mapping_template_complete",
        "status": status,
        "message": "Required role mappings are present." if status == "pass" else "Role mapping placeholders need review.",
        "details": {"missing_roles": missing, "bad_placeholders": bad_placeholders},
    }


def check_owner_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    owners = mapping.get("owners", [])
    owner_keys = {owner.get("env_user_id_key") for owner in owners}
    missing = sorted(REQUIRED_OWNER_KEYS - owner_keys)
    placeholder_ok = all(str(owner.get("user_id_placeholder", "")).startswith("TODO_OWNER_") for owner in owners)
    status = "pass" if not missing and placeholder_ok else "manual_required"
    return {
        "check_id": "owner_mapping_placeholders_present",
        "status": status,
        "message": "Owner user id placeholders are present." if status == "pass" else "Owner mapping needs manual completion.",
        "details": {"owner_env_keys": sorted(owner_keys), "missing_owner_keys": missing, "placeholder_ok": placeholder_ok},
    }


def check_intent_readiness(mapping: dict[str, Any]) -> dict[str, Any]:
    intents = mapping.get("intents", {})
    required_fields = [
        "guilds_required",
        "guild_messages_required",
        "message_content_required",
        "reactions_required_later",
        "members_required_later",
        "slash_commands_required_later",
        "approval_buttons_required_later",
    ]
    missing = [field for field in required_fields if field not in intents]
    status = "manual_required" if intents.get("message_content_required") else "warn"
    if missing:
        status = "manual_required"
    return {
        "check_id": "discord_intents_documented",
        "status": status if status != "warn" else "pass",
        "message": "Read-only intent checklist is documented; actual enabling is deferred.",
        "details": {"missing_fields": missing, "intents": intents},
    }


def check_safety_readiness(mapping: dict[str, Any]) -> dict[str, Any]:
    safety = mapping.get("safety", {})
    expected_true = [
        "no_discord_api_call_in_phase17",
        "no_gateway_connection",
        "no_bot_token_value_required",
        "no_external_execution",
        "human_only_execution",
        "no_secret_output",
        "no_rag_source_copy",
        "no_unknown_agent_dispatch",
        "no_junior_direct_approval",
        "no_reze_direct_order",
    ]
    missing_or_false = [key for key in expected_true if safety.get(key) is not True]
    return {
        "check_id": "safety_rules_preserved",
        "status": "pass" if not missing_or_false else "fail",
        "message": "Phase 17 safety rules are preserved." if not missing_or_false else "Some safety rules are missing or false.",
        "details": {"missing_or_false": missing_or_false},
    }


def _contains_secret_like_value(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_secret_like_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_secret_like_value(item) for item in value)
    if isinstance(value, str):
        return any(marker in value for marker in SECRET_VALUE_MARKERS)
    return False


def _missing_manual_values(mapping: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    guild = mapping.get("guild", {})
    if str(guild.get("guild_id_placeholder", "")).startswith("TODO_"):
        missing.append("DISCORD_GUILD_ID")
    for owner in mapping.get("owners", []):
        if str(owner.get("user_id_placeholder", "")).startswith("TODO_"):
            missing.append(str(owner.get("env_user_id_key")))
    for name, role in mapping.get("roles", {}).items():
        if str(role.get("role_id_placeholder", "")).startswith("TODO_"):
            missing.append(f"role:{name}")
    for name, channel in mapping.get("channels", {}).items():
        if str(channel.get("channel_id_placeholder", "")).startswith("TODO_"):
            missing.append(f"channel:{name}")
    return missing


def build_readiness_report(root: str | Path, mapping_path: str | Path | None = None) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    resolved_mapping_path = Path(mapping_path) if mapping_path else repo_root / DEFAULT_MAPPING_PATH
    if not resolved_mapping_path.is_absolute():
        resolved_mapping_path = repo_root / resolved_mapping_path

    env_keys = load_env_example_keys(repo_root)
    registry = load_registry(repo_root)
    mapping = load_mapping_template(resolved_mapping_path)
    checks = [
        check_required_env_keys(env_keys),
        check_channel_mapping(registry, mapping),
        check_role_mapping(mapping),
        check_owner_mapping(mapping),
        check_intent_readiness(mapping),
        check_safety_readiness(mapping),
    ]
    missing_required_values = _missing_manual_values(mapping)
    blocked_reasons = [
        check["message"]
        for check in checks
        if check.get("status") == "fail"
    ]
    warnings = [
        "Real Discord IDs are TODO placeholders; manual mapping is required before connection.",
        "DISCORD_BOT_TOKEN is only documented as a key name; no token value is required or read.",
    ]
    if _contains_secret_like_value(mapping):
        blocked_reasons.append("Mapping contains secret-like runtime value.")

    overall_ready = not blocked_reasons and not missing_required_values
    next_actions = [
        "Fill TODO guild, owner, role, channel, and audit channel IDs in a private runtime mapping file.",
        "Keep the mapping file out of source control if it contains real Discord IDs.",
        "Do not add a real bot token until an explicitly approved later phase.",
    ]
    return {
        "report_type": "discord_readiness_check",
        "version": "phase17_readonly_preflight",
        "created_at": utc_now(),
        "root": str(repo_root),
        "mapping_path": str(resolved_mapping_path),
        "overall_ready": overall_ready,
        "checks": checks,
        "missing_required_values": missing_required_values,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "next_actions": next_actions,
        "safety_assertions": {
            "discord_api_called": False,
            "gateway_connected": False,
            "bot_token_required": False,
            "external_execution_enabled": False,
            "human_only_execution_preserved": True,
        },
    }
