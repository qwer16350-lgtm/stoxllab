"""Read-only Discord Gateway runtime boundary for Phase 29.

The runtime path may connect only when a human explicitly runs the CLI mode.
All message writes and external actions remain blocked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from connection_preflight import build_phase29_runtime_readiness_report
from discord_safety_wrapper import assert_send_disabled, block_outgoing_action
from discord_token_loader import build_token_loader_report, load_discord_runtime_env
from live_event_pipeline import process_live_event_audit_only


def build_discord_intents() -> dict[str, Any]:
    return {
        "guilds": True,
        "guild_messages": True,
        "message_content": True,
        "members": False,
        "reactions": False,
        "write_permissions_required": False,
    }


def handle_readonly_message_event(message: Any, root: str | Path | None = None) -> dict[str, Any]:
    return process_live_event_audit_only(message, root=root)


def build_readonly_client(root: str | Path | None = None) -> dict[str, Any]:
    return {
        "client_type": "discord.py Client",
        "constructed_in_report": False,
        "root": str(Path(root or Path.cwd()).resolve()),
        "intents": build_discord_intents(),
        "outbound_guard": block_outgoing_action("message_create", "Client boundary is read-only."),
    }


def build_readonly_runtime_report(root: str | Path | None = None) -> dict[str, Any]:
    token_report = build_token_loader_report(root=root)
    runtime_env = {
        "token_present": token_report["token_present"],
        **token_report.get("runtime_flags", {}),
    }
    readiness = build_phase29_runtime_readiness_report(root or Path.cwd(), runtime_env=runtime_env)
    return {
        "report_type": "discord_readonly_runtime_report",
        "version": "phase29_readonly",
        "runtime_mode": "readonly_live",
        "can_connect_gateway": True,
        "can_send_messages": False,
        "can_execute_external_actions": False,
        "llm_enabled": False,
        "rag_enabled": False,
        "token_present": token_report["token_present"],
        "token_value_logged": False,
        "runtime_readiness": readiness,
        "ready_for_phase29_readonly_runtime": readiness["ready_for_phase29_readonly_runtime"],
        "intents": build_discord_intents(),
        "client_boundary": build_readonly_client(root),
        "safety_assertions": {
            "message_sent": False,
            "discord_write_api_called": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
            "human_only_execution_preserved": True,
        },
    }


def run_readonly_discord_bot(root: str | Path | None = None, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    repo_root = Path(root or Path.cwd()).resolve()
    env = runtime_env or load_discord_runtime_env(repo_root, load_dotenv_file=True, include_token_value=True)
    readiness = build_phase29_runtime_readiness_report(repo_root, runtime_env=env)
    try:
        assert_send_disabled(env)
    except ValueError as exc:
        return {
            "started": False,
            "blocked": True,
            "reason": str(exc),
            "token_value_logged": False,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }
    if readiness.get("ready_for_phase29_readonly_runtime") is not True:
        return {
            "started": False,
            "blocked": True,
            "reason": "Phase 29 read-only runtime readiness is not ready.",
            "blocked_reasons": readiness.get("blocked_reasons", []),
            "runtime_readiness": readiness,
            "token_value_logged": False,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }
    try:
        import discord
    except ImportError:
        return {
            "started": False,
            "blocked": True,
            "reason": "discord.py dependency is not installed in the current environment.",
            "token_value_logged": False,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }

    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_message(message: Any) -> None:
        await maybe_handle_message(message, repo_root)

    async def maybe_handle_message(message: Any, event_root: Path) -> None:
        handle_readonly_message_event(message, root=event_root)

    client.run(env["_token_value"])
    return {
        "started": True,
        "blocked": False,
        "token_value_logged": False,
        "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
    }
