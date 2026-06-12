"""Manage private local Discord runtime mapping files.

This helper never reads .env, never requests a bot token, never calls Discord,
and never opens a Gateway connection.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mapping_validator import build_mapping_validation_report, find_secret_like_values


VERSION = "phase22_local_only"
DEFAULT_TEMPLATE = "apps/hermes_gateway/examples/discord_runtime_mapping.template.json"
DEFAULT_LOCAL_MAPPING = "apps/hermes_gateway/local/discord_runtime_mapping.local.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_local_dir(root: str | Path) -> Path:
    return Path(root) / "apps" / "hermes_gateway" / "local"


def get_default_template_path(root: str | Path) -> Path:
    return Path(root) / DEFAULT_TEMPLATE


def get_default_local_mapping_path(root: str | Path) -> Path:
    return Path(root) / DEFAULT_LOCAL_MAPPING


def ensure_local_dir(root: str | Path) -> Path:
    local_dir = get_local_dir(root)
    local_dir.mkdir(parents=True, exist_ok=True)
    return local_dir


def _safety_assertions() -> dict[str, Any]:
    return {
        "discord_api_called": False,
        "gateway_connected": False,
        "bot_token_required": False,
        "env_file_read": False,
        "message_sent": False,
        "external_execution_enabled": False,
        "human_only_execution_preserved": True,
    }


def _base_report(root: str | Path, local_path: str | Path | None = None, strict: bool = False) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    local_mapping = Path(local_path) if local_path else get_default_local_mapping_path(repo_root)
    if not local_mapping.is_absolute():
        local_mapping = repo_root / local_mapping
    return {
        "report_type": "local_mapping_manager",
        "version": VERSION,
        "created_at": utc_now(),
        "root": str(repo_root),
        "local_dir": str(get_local_dir(repo_root)),
        "template_path": str(get_default_template_path(repo_root)),
        "local_mapping_path": str(local_mapping),
        "local_mapping_exists": local_mapping.exists(),
        "created": False,
        "validated": False,
        "strict": strict,
        "ready_for_readonly_connection": False,
        "warnings": [],
        "blocked_reasons": [],
        "next_actions": [],
        "safety_assertions": _safety_assertions(),
    }


def copy_template_to_local(
    root: str | Path,
    template_path: str | Path | None = None,
    local_path: str | Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    ensure_local_dir(repo_root)
    source = Path(template_path) if template_path else get_default_template_path(repo_root)
    target = Path(local_path) if local_path else get_default_local_mapping_path(repo_root)
    if not source.is_absolute():
        source = repo_root / source
    if not target.is_absolute():
        target = repo_root / target

    report = _base_report(repo_root, target)
    report["template_path"] = str(source)
    if not source.exists():
        report["blocked_reasons"].append("Template mapping file does not exist.")
        report["next_actions"].append("Confirm apps/hermes_gateway/examples/discord_runtime_mapping.template.json exists.")
        return report
    if target.exists() and not force:
        report["blocked_reasons"].append("Local mapping already exists; refusing to overwrite without --force.")
        report["next_actions"].append("Run validation, edit the existing local mapping, or use --force intentionally.")
        return report

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    report["created"] = True
    report["local_mapping_exists"] = True
    report["warnings"].append("Local mapping copy contains TODO placeholders until a human fills actual Discord IDs.")
    report["next_actions"].extend(
        [
            "Fill actual Discord IDs in the local mapping file.",
            "Do not add Bot Token, API keys, passwords, or secrets.",
            "Run --validate-local-mapping --strict --json before any read-only connection phase.",
        ]
    )
    return report


def validate_local_mapping(root: str | Path, local_path: str | Path | None = None, strict: bool = False) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    target = Path(local_path) if local_path else get_default_local_mapping_path(repo_root)
    if not target.is_absolute():
        target = repo_root / target
    return build_mapping_validation_report(target, root=repo_root, strict=strict)


def build_local_mapping_manager_report(
    root: str | Path,
    local_path: str | Path | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    target = Path(local_path) if local_path else get_default_local_mapping_path(repo_root)
    if not target.is_absolute():
        target = repo_root / target
    report = _base_report(repo_root, target, strict=strict)
    if not target.exists():
        report["warnings"].append("Local runtime mapping file does not exist yet.")
        report["next_actions"].append("Run python apps\\hermes_gateway\\cli.py --init-local-mapping --json.")
        return report

    validation = validate_local_mapping(repo_root, target, strict=strict)
    report["validated"] = True
    report["ready_for_readonly_connection"] = bool(validation.get("ready_for_readonly_connection"))
    report["warnings"].extend(validation.get("warnings", []))
    report["blocked_reasons"].extend(validation.get("blocked_reasons", []))
    report["validation_summary"] = validation.get("summary", {})
    report["validation_overall_valid"] = validation.get("overall_valid")
    report["validation_manual_required_count"] = len(validation.get("manual_required", []))
    report["validation_missing_mapping_count"] = len(validation.get("missing_mappings", []))
    try:
        payload = json.loads(target.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        report["blocked_reasons"].append(f"Could not parse local mapping: {exc}")
        return report
    if find_secret_like_values(payload):
        report["blocked_reasons"].append("Local mapping contains secret-like values; remove them before continuing.")
        report["ready_for_readonly_connection"] = False
    if not report["ready_for_readonly_connection"]:
        report["next_actions"].append("Fill missing IDs and run strict validation again.")
    return report
