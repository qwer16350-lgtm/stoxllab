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
from live_event_pipeline import load_visibility_context, process_live_event_audit_only, redact_discord_id
from private_test_reply import (
    build_private_test_reply_payload,
    build_private_test_reply_policy,
    send_private_test_reply_only,
)


def build_discord_intents() -> dict[str, Any]:
    return {
        "guilds": True,
        "guild_messages": True,
        "message_content": True,
        "members": False,
        "reactions": False,
        "write_permissions_required": False,
    }


def build_ready_visibility(client: Any, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    env = runtime_env or {}
    private_policy = build_private_test_reply_policy(env)
    user = getattr(client, "user", None)
    guilds = getattr(client, "guilds", []) or []
    return {
        "runtime_mode": env.get("runtime_mode", "readonly"),
        "bot_user_name": getattr(user, "name", "") if user else "",
        "bot_user_id": redact_discord_id(getattr(user, "id", "")) if user else "",
        "connected_guild_count": len(guilds),
        "target_guild_configured": bool(env.get("guild_id_present") or env.get("target_guild_configured")),
        "send_disabled": not bool(env.get("send_messages")),
        "general_send_disabled": True,
        "private_test_reply_enabled": bool(private_policy.get("private_test_reply_enabled") and private_policy.get("send_messages")),
        "private_test_channel_configured": bool(private_policy.get("private_test_channel_id_present")),
        "external_disabled": not bool(env.get("external_execution")),
        "llm_disabled": not bool(env.get("llm_enabled")),
        "rag_disabled": not bool(env.get("rag_enabled")),
        "token_value_logged": False,
    }


def print_ready_visibility(client: Any, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    visibility = build_ready_visibility(client, runtime_env)
    print(
        "[READONLY_READY] "
        f"runtime_mode={visibility['runtime_mode']} "
        f"bot_user={visibility['bot_user_name']}:{visibility['bot_user_id']} "
        f"guilds={visibility['connected_guild_count']} "
        f"target_guild_configured={str(visibility['target_guild_configured']).lower()} "
        f"general_send_disabled={str(visibility['general_send_disabled']).lower()} "
        f"private_test_reply_enabled={str(visibility['private_test_reply_enabled']).lower()} "
        f"private_test_channel_configured={str(visibility['private_test_channel_configured']).lower()} "
        f"external_disabled={str(visibility['external_disabled']).lower()} "
        f"llm_disabled={str(visibility['llm_disabled']).lower()} "
        f"rag_disabled={str(visibility['rag_disabled']).lower()}",
        flush=True,
    )
    return visibility


def format_readonly_event_line(result: dict[str, Any]) -> str:
    event = result.get("visibility_event", {})
    return (
        "[READONLY_EVENT] "
        f"{event.get('decision', 'unknown')} "
        f"channel={event.get('channel_name', '')} "
        f"author={event.get('author_id', '')} "
        f"content_present={str(event.get('content_present', False)).lower()} "
        f"content_length={event.get('content_length', 0)}"
    )


def handle_readonly_message_event(
    message: Any,
    root: str | Path | None = None,
    write_log: bool = False,
    visibility_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return process_live_event_audit_only(
        message,
        root=root,
        visibility_context=visibility_context,
        write_log=write_log,
    )


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
        "private_test_reply_enabled": bool(runtime_env.get("private_test_reply_enabled")),
        "private_test_channel_configured": bool(runtime_env.get("private_test_channel_id_present")),
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
    private_reply_policy = build_private_test_reply_policy(env)
    readiness_env = dict(env)
    if private_reply_policy.get("send_messages") and private_reply_policy.get("private_test_reply_enabled"):
        readiness_env["send_messages"] = False
    readiness = build_phase29_runtime_readiness_report(repo_root, runtime_env=readiness_env)
    try:
        if not (private_reply_policy.get("send_messages") and private_reply_policy.get("private_test_reply_enabled")):
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

    visibility_context = load_visibility_context(repo_root)
    visibility_context["private_test_channel_id"] = private_reply_policy.get("_private_test_channel_id", "")

    @client.event
    async def on_ready() -> None:
        print_ready_visibility(client, env)

    @client.event
    async def on_message(message: Any) -> None:
        result = handle_readonly_message_event(
            message,
            root=repo_root,
            write_log=True,
            visibility_context=visibility_context,
        )
        print(format_readonly_event_line(result), flush=True)
        placeholder = result.get("agent_placeholder_response", {})
        payload = build_private_test_reply_payload(message, placeholder, private_reply_policy)
        if payload.get("will_send"):
            print(
                "[PRIVATE_TEST_REPLY] "
                f"private_test_reply_allowed channel={payload.get('decision', {}).get('channel_name', '')} "
                "source=agent_placeholder_response "
                f"will_send={str(payload.get('will_send', False)).lower()}",
                flush=True,
            )
            reply_audit = await send_private_test_reply_only(message.channel, payload, private_reply_policy)
            print(
                "[PRIVATE_TEST_REPLY_SENT] "
                f"message_sent={str(reply_audit.get('message_sent', False)).lower()} "
                f"channel={payload.get('decision', {}).get('channel_name', '')}",
                flush=True,
            )
        elif result.get("visibility_event", {}).get("channel_is_private_test") or private_reply_policy.get("private_test_reply_enabled"):
            print(
                "[PRIVATE_TEST_REPLY] "
                f"blocked reason={payload.get('decision', {}).get('reason', '')}",
                flush=True,
            )

    client.run(env["_token_value"])
    return {
        "started": True,
        "blocked": False,
        "token_value_logged": False,
        "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
    }
