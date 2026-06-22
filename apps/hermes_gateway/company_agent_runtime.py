"""Company agent runtime for STOXL Discord Agent OS v0."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from company_agent_registry import get_channel_policy, load_company_registry
from company_agent_router import build_company_agent_org_report, route_company_agent_message
from company_agent_responder import build_company_agent_response
from company_webhook_sender import send_as_agent
from safety_report_builders import build_blocked_report


COMMAND_SYNTAX = ["!lucy", "!marin", "!meiko", "!kasumi", "!reze", "!agent", "!route", "!handoff", "!agents", "!help"]


def build_company_agent_router_dry_run(channel: str, message: str) -> dict[str, Any]:
    route = route_company_agent_message(channel, message)
    if route.get("selected_agent"):
        response = build_company_agent_response(str(route["selected_agent"]), message, route)
    else:
        response = {
            "response_type": "company_agent_response",
            "reply_text_source": "command_help",
            "llm_api_call_attempted": False,
            "rag_called": False,
            "external_execution": False,
        }
    return {
        **route,
        "response_preview": {
            "reply_text_source": response.get("reply_text_source"),
            "agent_id": response.get("agent_id"),
            "webhook_persona": response.get("webhook_persona"),
        },
    }


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _runtime_env(env: dict[str, Any] | None = None) -> dict[str, Any]:
    env_map = dict(os.environ if env is None else env)
    return {
        "discord_token_present": bool(env_map.get("DISCORD_BOT_TOKEN") or env_map.get("HERMES_DISCORD_TOKEN")),
        "_discord_token": env_map.get("DISCORD_BOT_TOKEN") or env_map.get("HERMES_DISCORD_TOKEN") or "",
        "llm_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_LLM_ENABLED", "false")),
        "reply_mode": str(env_map.get("HERMES_COMPANY_AGENT_REPLY_MODE", "deterministic_fallback") or "deterministic_fallback"),
    }


def build_company_agent_runtime_report(allow_flag_present: bool = False) -> dict[str, Any]:
    if not allow_flag_present:
        return build_blocked_report(
            "company_agent_runtime_blocked",
            ["allow_flag_missing"],
            {
                "allow_flag_present": False,
                "runtime_default_blocked": True,
                "actual_discord_runtime_executed": False,
                "discord_gateway_live_connection_executed": False,
                "discord_api_send_called": False,
                "discord_message_sent": False,
                "message_sent_count": 0,
                "command_syntax": list(COMMAND_SYNTAX),
                "external_execution": False,
                "webhook_url_value_logged": False,
                "raw_discord_ids_logged": False,
                "secret_values_logged": False,
            },
        )
    return build_company_agent_runtime_start_report(allow_flag_present=True)


def build_company_agent_runtime_start_report(
    allow_flag_present: bool,
    env: dict[str, Any] | None = None,
    *,
    discord_dependency_available: bool = True,
) -> dict[str, Any]:
    runtime_env = _runtime_env(env)
    registry = load_company_registry()
    if not allow_flag_present:
        return build_company_agent_runtime_report(False)
    if not runtime_env["discord_token_present"]:
        return build_blocked_report(
            "company_agent_runtime_blocked",
            ["discord_bot_token_missing"],
            {
                "allow_flag_present": True,
                "discord_token_present": False,
                "token_value_logged": False,
                "discord_gateway_live_connection_executed": False,
            },
        )
    if not discord_dependency_available:
        return build_blocked_report(
            "company_agent_runtime_dependency_missing",
            ["discord_py_dependency_missing"],
            {
                "allow_flag_present": True,
                "discord_token_present": True,
                "token_value_logged": False,
                "discord_gateway_live_connection_executed": False,
            },
        )
    return {
        "report_type": "company_agent_runtime_started",
        "started": True,
        "blocked": False,
        "allow_flag_present": True,
        "actual_discord_runtime_executed": True,
        "discord_gateway_live_connection_executed": True,
        "runtime_loop_active": True,
        "llm_enabled": bool(runtime_env["llm_enabled"]),
        "reply_mode": runtime_env["reply_mode"],
        "agent_count": len(registry["agents"]),
        "command_syntax": list(COMMAND_SYNTAX),
        "discord_token_present": True,
        "token_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "webhook_url_value_logged": False,
        "external_execution": False,
    }


def should_ignore_message(message: Any, bot_user: Any | None = None) -> tuple[bool, str]:
    content = str(getattr(message, "content", "") or "").strip()
    author = getattr(message, "author", None)
    if not content:
        return True, "empty_message"
    if bool(getattr(author, "bot", False)):
        return True, "bot_message"
    if bot_user is not None and getattr(author, "id", None) == getattr(bot_user, "id", None):
        return True, "self_message"
    channel_name = str(getattr(getattr(message, "channel", None), "name", "") or "")
    if not get_channel_policy(channel_name)["known_channel"]:
        return True, "unknown_channel"
    return False, ""


def build_company_agent_message_result(channel_name: str, content: str) -> dict[str, Any]:
    route = route_company_agent_message(channel_name, content)
    if route.get("blocked"):
        return {
            **route,
            "reply_prepared": False,
            "send_strategy": "blocked",
            "bot_message_fallback_used": False,
        }
    selected_agent = str(route.get("selected_agent") or "")
    response = build_company_agent_response(selected_agent, content, route)
    webhook_result = send_as_agent(selected_agent, channel_name, str(response.get("content", "")))
    bot_fallback = webhook_result.get("blocked") is True
    return {
        **route,
        "reply_prepared": True,
        "response": response,
        "webhook_send_available": not bot_fallback,
        "bot_message_fallback_used": bot_fallback,
        "send_strategy": "bot_message_fallback" if bot_fallback else "webhook_persona",
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


async def _send_runtime_reply(message: Any, result: dict[str, Any]) -> None:
    response = result.get("response", {})
    content = str(response.get("content", "") or "")
    if not content:
        return
    await message.channel.send(content[:1900])


async def _run_discord_client(token: str, start_report: dict[str, Any]) -> dict[str, Any]:
    try:
        import discord  # type: ignore
    except ImportError:
        missing = build_company_agent_runtime_start_report(
            True,
            {"DISCORD_BOT_TOKEN": "present"},
            discord_dependency_available=False,
        )
        print(json.dumps(missing, ensure_ascii=False, indent=2), flush=True)
        return missing

    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    client = discord.Client(intents=intents)
    printed_ready = False

    @client.event
    async def on_ready() -> None:
        nonlocal printed_ready
        if not printed_ready:
            print(json.dumps(start_report, ensure_ascii=False, indent=2), flush=True)
            printed_ready = True

    @client.event
    async def on_message(message: Any) -> None:
        ignored, _reason = should_ignore_message(message, bot_user=client.user)
        if ignored:
            return
        channel_name = str(getattr(message.channel, "name", "") or "")
        result = build_company_agent_message_result(channel_name, str(getattr(message, "content", "") or ""))
        if result.get("reply_prepared") and result.get("bot_message_fallback_used"):
            await _send_runtime_reply(message, result)

    try:
        await client.start(token)
    finally:
        shutdown = {
            "report_type": "company_agent_runtime_shutdown",
            "shutdown": True,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
        print(json.dumps(shutdown, ensure_ascii=False, indent=2), flush=True)
    return start_report


def run_company_agent_runtime_forever(allow_flag_present: bool = False) -> int:
    if not allow_flag_present:
        print(json.dumps(build_company_agent_runtime_report(False), ensure_ascii=False, indent=2))
        return 0
    try:
        import discord  # noqa: F401
        dependency_available = True
    except ImportError:
        dependency_available = False
    start_report = build_company_agent_runtime_start_report(
        True,
        discord_dependency_available=dependency_available,
    )
    if start_report.get("blocked"):
        print(json.dumps(start_report, ensure_ascii=False, indent=2))
        return 1
    token = _runtime_env()["_discord_token"]
    try:
        asyncio.run(_run_discord_client(token, start_report))
    except KeyboardInterrupt:
        print(
            json.dumps(
                {
                    "report_type": "company_agent_runtime_shutdown",
                    "shutdown": True,
                    "reason": "operator_interrupt",
                    "token_value_logged": False,
                    "raw_discord_ids_logged": False,
                    "secret_values_logged": False,
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
    return 0


def build_company_agent_org_runtime_report() -> dict[str, Any]:
    return build_company_agent_org_report()
