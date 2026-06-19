from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "hermes_gateway"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_registry import CHANNEL_STRUCTURE, load_company_registry  # noqa: E402


REQUIRED_ROLES = [
    "STOXL-OWNER",
    "STOXL-SENIOR-AGENT",
    "STOXL-JUNIOR-AGENT",
    "STOXL-STRATEGY-AGENT",
    "STOXL-AUDIT-VIEWER",
]
WEBHOOK_PERSONAS = ["LUCY_STOXL", "MARIN_STOXL", "MEIKO_STOXL", "KASUMI_STOXL", "REZE_STOXL"]
DISCORD_API_BASE = "https://discord.com/api/v10"


def _base_report(report_type: str) -> dict[str, Any]:
    registry = load_company_registry(ROOT)
    return {
        "report_type": report_type,
        "company_agent_setup_available": True,
        "categories": [
            {"name": category, "status": "planned", "channels": [{"name": channel, "status": "planned"} for channel in channels]}
            for category, channels in CHANNEL_STRUCTURE.items()
        ],
        "roles": [{"name": role, "status": "planned"} for role in REQUIRED_ROLES],
        "webhook_personas": [{"name": persona, "status": "planned"} for persona in WEBHOOK_PERSONAS],
        "agent_count": len(registry["agents"]),
        "discord_api_called": False,
        "discord_setup_executed": False,
        "discord_token_present": False,
        "discord_token_value_logged": False,
        "discord_guild_id_present": False,
        "discord_guild_id_value_logged": False,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_dry_run_report() -> dict[str, Any]:
    return _base_report("stoxl_discord_company_setup_dry_run")


def _request(token: str, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        DISCORD_API_BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bot " + token,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        parsed = json.loads(body) if body else {}
        return int(response.status), parsed


def _status(name: str, status: str) -> dict[str, str]:
    return {"name": name, "status": status}


def build_execute_report(allow: bool) -> dict[str, Any]:
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    guild_id = os.environ.get("DISCORD_GUILD_ID", "")
    report = _base_report("stoxl_discord_company_setup_execute")
    report.update(
        {
            "allow_actual_discord_setup": bool(allow),
            "discord_token_present": bool(token),
            "discord_guild_id_present": bool(guild_id),
            "blocked": not (allow and token and guild_id),
            "blocked_reasons": [],
        }
    )
    if not allow:
        report["blocked_reasons"].append("allow_actual_discord_setup_required")
    if not token:
        report["blocked_reasons"].append("discord_bot_token_missing")
    if not guild_id:
        report["blocked_reasons"].append("discord_guild_id_missing")
    if report["blocked"]:
        return report

    report["discord_api_called"] = True
    report["discord_setup_executed"] = True
    try:
        _, channels = _request(token, "GET", f"/guilds/{guild_id}/channels")
        _, roles = _request(token, "GET", f"/guilds/{guild_id}/roles")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        report["blocked"] = True
        report["blocked_reasons"] = ["discord_api_setup_failed"]
        report["error_type"] = exc.__class__.__name__
        report["discord_setup_executed"] = False
        return report

    role_names = {item.get("name") for item in roles if isinstance(item, dict)}
    channel_by_name = {item.get("name"): item for item in channels if isinstance(item, dict)}
    role_results = []
    for role in REQUIRED_ROLES:
        if role in role_names:
            role_results.append(_status(role, "reused"))
            continue
        try:
            _request(token, "POST", f"/guilds/{guild_id}/roles", {"name": role})
            role_results.append(_status(role, "created"))
        except Exception:
            role_results.append(_status(role, "failed"))

    category_results = []
    for category, channel_names in CHANNEL_STRUCTURE.items():
        category_obj = channel_by_name.get(category)
        category_status = "reused" if category_obj else "created"
        if not category_obj:
            try:
                _, category_obj = _request(token, "POST", f"/guilds/{guild_id}/channels", {"name": category, "type": 4})
            except Exception:
                category_results.append({"name": category, "status": "failed", "channels": []})
                continue
        child_results = []
        for channel_name in channel_names:
            if channel_name in channel_by_name:
                child_results.append(_status(channel_name, "reused"))
                continue
            try:
                _request(
                    token,
                    "POST",
                    f"/guilds/{guild_id}/channels",
                    {"name": channel_name, "type": 0, "parent_id": category_obj.get("id")},
                )
                child_results.append(_status(channel_name, "created"))
            except Exception:
                child_results.append(_status(channel_name, "failed"))
        category_results.append({"name": category, "status": category_status, "channels": child_results})

    report["roles"] = role_results
    report["categories"] = category_results
    report["webhook_personas"] = [{"name": persona, "status": "prepared"} for persona in WEBHOOK_PERSONAS]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up STOXL Discord Company OS.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-actual-discord-setup", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_execute_report(args.allow_actual_discord_setup) if args.execute else build_dry_run_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["report_type"])
        print(f"- company_agent_setup_available: {report.get('company_agent_setup_available')}")
        print(f"- discord_api_called: {report.get('discord_api_called')}")
        print(f"- discord_setup_executed: {report.get('discord_setup_executed')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
