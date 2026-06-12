"""Local Discord runtime mapping validator.

This module validates mapping JSON structure only. It never calls Discord,
opens a Gateway connection, reads a bot token, or sends messages.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REGISTRY_PATH = "registry/stoxl_agent_registry.example.json"
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
REQUIRED_CHANNELS = {
    "최종-승인요청",
    "대표-회의실",
    "marin-초안",
    "lucy-검토",
    "kasumi-리서치",
    "meiko-검토",
    "reze-전략기획",
    "공모전-지원사업",
    "일정-마감관리",
    "완료된-안건",
    "보류된-안건",
    "폐기된-안건",
}
REQUIRED_INTENT_KEYS = {
    "guilds_required",
    "guild_messages_required",
    "message_content_required",
    "reactions_required_later",
    "members_required_later",
    "slash_commands_required_later",
    "approval_buttons_required_later",
}
REQUIRED_SAFETY_TRUE = {
    "no_gateway_connection",
    "no_external_execution",
    "human_only_execution",
    "no_secret_output",
    "no_rag_source_copy",
    "no_unknown_agent_dispatch",
    "no_junior_direct_approval",
    "no_reze_direct_order",
}
PLACEHOLDER_MARKERS = ("TODO", "TODO_", "PLACEHOLDER", "REPLACE_ME")
SECRET_KEY_MARKERS = (
    "token",
    "password",
    "api_key",
    "secret",
    "authorization",
    "bearer",
    "private_key",
    "access_key",
    "refresh_token",
)
SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "mfa.", "bearer ", "bot ")
DISCORD_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def find_root(start: str | Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "registry").exists() and (candidate / "apps" / "hermes_gateway").exists():
            return candidate
    return Path.cwd().resolve()


def resolve_path(path: str | Path, root: str | Path | None = None) -> Path:
    source = Path(path)
    if source.is_absolute():
        return source
    return find_root(root) / source


def load_mapping(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_registry(root: str | Path | None = None) -> dict[str, Any]:
    repo_root = find_root(root)
    return json.loads((repo_root / REGISTRY_PATH).read_text(encoding="utf-8"))


def _check(check_id: str, status: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"check_id": check_id, "status": status, "message": message, "details": details or {}}


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped:
        return True
    upper = stripped.upper()
    return any(marker in upper for marker in PLACEHOLDER_MARKERS)


def _placeholder_status(placeholders: list[str], strict: bool) -> str:
    if not placeholders:
        return "pass"
    return "fail" if strict else "manual_required"


def _manual_message(label: str, placeholders: list[str], strict: bool) -> str:
    if not placeholders:
        return f"{label} mapping is filled."
    if strict:
        return f"{label} mapping still contains placeholders."
    return f"{label} mapping contains placeholders that require manual completion."


def _collect_placeholders(payload: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            found.extend(_collect_placeholders(value, f"{path}.{key}"))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            found.extend(_collect_placeholders(value, f"{path}[{index}]"))
    elif _is_placeholder(payload):
        found.append(path)
    return found


def check_guild_mapping(mapping: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    guild = mapping.get("guild", {})
    missing = [key for key in ("guild_id_env_key", "guild_id_placeholder") if key not in guild]
    placeholders = [f"guild.{key}" for key, value in guild.items() if _is_placeholder(value)]
    if missing:
        return _check("guild_mapping", "fail", "Guild mapping is missing required fields.", {"missing": missing})
    status = _placeholder_status(placeholders, strict)
    return _check("guild_mapping", status, _manual_message("Guild", placeholders, strict), {"placeholders": placeholders})


def check_owner_mapping(mapping: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    owners = mapping.get("owners", [])
    keys = {owner.get("env_user_id_key") for owner in owners if isinstance(owner, dict)}
    missing = sorted(REQUIRED_OWNER_KEYS - keys)
    placeholders = [
        f"owners.{owner.get('env_user_id_key') or index}"
        for index, owner in enumerate(owners)
        if isinstance(owner, dict) and _is_placeholder(owner.get("user_id_placeholder"))
    ]
    if missing:
        return _check("owner_mapping", "fail", "Required owner mappings are missing.", {"missing_owner_keys": missing, "owner_keys": sorted(keys)})
    status = _placeholder_status(placeholders, strict)
    return _check("owner_mapping", status, _manual_message("Owner", placeholders, strict), {"owner_keys": sorted(keys), "placeholders": placeholders})


def check_role_mapping(mapping: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    roles = mapping.get("roles", {})
    role_names = set(roles.keys()) if isinstance(roles, dict) else set()
    missing = sorted(REQUIRED_ROLES - role_names)
    placeholders = [
        f"roles.{name}"
        for name, item in roles.items()
        if isinstance(item, dict) and _is_placeholder(item.get("role_id_placeholder") or item.get("role_id"))
    ]
    if missing:
        return _check("role_mapping", "fail", "Required role mappings are missing.", {"missing_roles": missing, "mapped_roles": sorted(role_names)})
    status = _placeholder_status(placeholders, strict)
    return _check("role_mapping", status, _manual_message("Role", placeholders, strict), {"mapped_roles": sorted(role_names), "placeholders": placeholders})


def _channel_id(item: dict[str, Any]) -> Any:
    return item.get("channel_id") if "channel_id" in item else item.get("channel_id_placeholder")


def check_channel_mapping(mapping: dict[str, Any], registry: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    channels = mapping.get("channels", {})
    mapped = set(channels.keys()) if isinstance(channels, dict) else set()
    registry_channels = set(registry.get("channels", {}).keys())
    required = sorted(registry_channels | REQUIRED_CHANNELS)
    missing = sorted(set(required) - mapped)
    unknown = sorted(mapped - set(required))
    placeholders = [
        f"channels.{name}"
        for name, item in channels.items()
        if isinstance(item, dict) and _is_placeholder(_channel_id(item))
    ]
    if missing:
        return _check(
            "channel_mapping",
            "fail",
            "Required channel mappings are missing.",
            {"required_channels": required, "missing_channels": missing, "unknown_channels": unknown, "placeholders": placeholders},
        )
    if unknown and strict:
        return _check("channel_mapping", "fail", "Unknown channel mappings are present in strict mode.", {"unknown_channels": unknown, "placeholders": placeholders})
    status = _placeholder_status(placeholders, strict)
    if status == "pass" and unknown:
        status = "warn"
    return _check(
        "channel_mapping",
        status,
        "Channel mappings cover registry channels." if status == "pass" else "Channel mapping requires review.",
        {"required_channels": required, "missing_channels": missing, "unknown_channels": unknown, "placeholders": placeholders},
    )


def check_approval_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    channels = mapping.get("channels", {})
    approval_channels = [
        name
        for name, item in channels.items()
        if name == "최종-승인요청" or (isinstance(item, dict) and item.get("workflow_role") == "final_approval")
    ]
    interactions = mapping.get("approval_interactions", {})
    external_after_approval = interactions.get("external_execution_after_approval")
    human_only = interactions.get("human_only_execution")
    missing = []
    if not approval_channels:
        missing.append("final_approval_channel")
    if external_after_approval is not False:
        missing.append("external_execution_after_approval=false")
    if human_only is not True:
        missing.append("human_only_execution=true")
    return _check(
        "approval_mapping",
        "pass" if not missing else "fail",
        "Approval mapping preserves human-only review." if not missing else "Approval mapping is incomplete or unsafe.",
        {"approval_channels": approval_channels, "missing_or_invalid": missing},
    )


def check_audit_mapping(mapping: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    audit = mapping.get("audit", {})
    audit_channel = audit.get("audit_log_channel") if "audit_log_channel" in audit else audit.get("audit_log_channel_placeholder")
    placeholders = ["audit.audit_log_channel"] if _is_placeholder(audit_channel) else []
    missing = []
    if "local_log_root" not in audit:
        missing.append("local_log_root")
    if "export_root" not in audit:
        missing.append("export_root")
    if missing:
        return _check("audit_mapping", "fail", "Audit mapping is missing required fields.", {"missing": missing, "placeholders": placeholders})
    status = _placeholder_status(placeholders, strict)
    return _check("audit_mapping", status, _manual_message("Audit", placeholders, strict), {"placeholders": placeholders})


def check_intent_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    intents = mapping.get("intents", {})
    missing = sorted(REQUIRED_INTENT_KEYS - set(intents.keys()))
    return _check(
        "intent_mapping",
        "pass" if not missing else "fail",
        "Intent checklist is documented." if not missing else "Intent checklist is incomplete.",
        {"missing_intents": missing, "documented_intents": sorted(intents.keys())},
    )


def check_safety_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    safety = mapping.get("safety", {})
    no_api_value = safety.get("no_discord_api_call_in_phase17", safety.get("no_discord_api_call"))
    missing_or_false = sorted(key for key in REQUIRED_SAFETY_TRUE if safety.get(key) is not True)
    if no_api_value is not True:
        missing_or_false.append("no_discord_api_call")
    return _check(
        "safety_mapping",
        "pass" if not missing_or_false else "fail",
        "Safety mapping preserves local-only execution." if not missing_or_false else "Safety mapping is missing required true values.",
        {"missing_or_false": missing_or_false},
    )


def _secret_value(value: Any) -> bool:
    if not isinstance(value, str) or _is_placeholder(value):
        return False
    lower = value.lower()
    return any(marker in lower for marker in SECRET_VALUE_MARKERS) or bool(DISCORD_TOKEN_RE.search(value))


def _secret_key_with_value(key: str, value: Any) -> bool:
    lower = key.lower()
    if not any(marker in lower for marker in SECRET_KEY_MARKERS):
        return False
    if isinstance(value, bool) or _is_placeholder(value):
        return False
    if isinstance(value, str) and value.upper().startswith(("DISCORD_", "OWNER_", "HERMES_")):
        return False
    return value not in (None, "", [])


def find_secret_like_values(payload: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if _secret_key_with_value(str(key), child):
                    findings.append({"path": child_path, "value": "[REDACTED]"})
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
        elif _secret_value(value):
            findings.append({"path": path, "value": "[REDACTED]"})

    walk(payload, "$")
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for finding in findings:
        if finding["path"] not in seen:
            seen.add(finding["path"])
            deduped.append(finding)
    return deduped


def _summary(mapping: dict[str, Any], registry: dict[str, Any], missing_mappings: list[str], manual_required: list[str], secret_findings: list[dict[str, str]]) -> dict[str, int]:
    channels = mapping.get("channels", {})
    roles = mapping.get("roles", {})
    required_channels = set(registry.get("channels", {}).keys()) | REQUIRED_CHANNELS
    placeholders = _collect_placeholders(mapping)
    return {
        "required_channels": len(required_channels),
        "mapped_channels": len(channels) if isinstance(channels, dict) else 0,
        "missing_channels": sum(1 for item in missing_mappings if item.startswith("channel:")),
        "required_roles": len(REQUIRED_ROLES),
        "mapped_roles": len(roles) if isinstance(roles, dict) else 0,
        "missing_roles": sum(1 for item in missing_mappings if item.startswith("role:")),
        "todo_placeholders": len(placeholders),
        "secret_like_values": len(secret_findings),
    }


def validate_mapping(mapping: dict[str, Any], registry: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    checks = [
        _check(
            "mapping_type_version",
            "pass" if mapping.get("mapping_type") and mapping.get("version") else "fail",
            "Mapping type and version are present." if mapping.get("mapping_type") and mapping.get("version") else "Mapping type or version is missing.",
            {"mapping_type": mapping.get("mapping_type"), "version": mapping.get("version")},
        ),
        check_guild_mapping(mapping, strict),
        check_owner_mapping(mapping, strict),
        check_role_mapping(mapping, strict),
        check_channel_mapping(mapping, registry, strict),
        check_approval_mapping(mapping),
        check_audit_mapping(mapping, strict),
        check_intent_mapping(mapping),
        check_safety_mapping(mapping),
    ]
    secret_findings = find_secret_like_values(mapping)
    if secret_findings:
        checks.append(_check("secret_like_values", "fail", "Secret-like values were found and redacted in this report.", {"findings": secret_findings}))
    else:
        checks.append(_check("secret_like_values", "pass", "No secret-like values found.", {"findings": []}))

    missing_mappings: list[str] = []
    manual_required: list[str] = []
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    for check in checks:
        details = check.get("details", {})
        for role in details.get("missing_roles", []):
            missing_mappings.append(f"role:{role}")
        for channel in details.get("missing_channels", []):
            missing_mappings.append(f"channel:{channel}")
        for owner in details.get("missing_owner_keys", []):
            missing_mappings.append(f"owner:{owner}")
        for item in details.get("placeholders", []):
            manual_required.append(item)
        if check["status"] == "warn":
            warnings.append(check["message"])
        if check["status"] == "fail":
            blocked_reasons.append(check["message"])
    if not strict and manual_required:
        warnings.append("TODO placeholders remain; manual runtime mapping is required before read-only connection.")

    failed = any(check["status"] == "fail" for check in checks)
    ready = not failed and not manual_required and not warnings
    return {
        "overall_valid": not failed,
        "ready_for_readonly_connection": ready,
        "checks": checks,
        "missing_mappings": sorted(set(missing_mappings)),
        "manual_required": sorted(set(manual_required)),
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "summary": _summary(mapping, registry, missing_mappings, manual_required, secret_findings),
        "safety_assertions": {
            "discord_api_called": False,
            "gateway_connected": False,
            "message_sent": False,
            "external_execution_enabled": False,
            "human_only_execution_preserved": True,
        },
    }


def build_mapping_validation_report(mapping_path: str | Path, root: str | Path | None = None, strict: bool = False) -> dict[str, Any]:
    repo_root = find_root(root)
    resolved_mapping_path = resolve_path(mapping_path, repo_root)
    mapping = load_mapping(resolved_mapping_path)
    registry = load_registry(repo_root)
    validation = validate_mapping(mapping, registry, strict=strict)
    return {
        "report_type": "discord_mapping_validation",
        "version": "phase20_local_only",
        "created_at": utc_now(),
        "root": str(repo_root),
        "mapping_path": str(resolved_mapping_path),
        "strict": strict,
        **validation,
    }
