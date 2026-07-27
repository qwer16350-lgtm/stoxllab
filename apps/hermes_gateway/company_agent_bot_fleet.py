"""Send-only real Discord bot fleet for STOXL company agents."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

from company_agent_registry import AGENT_IDS, get_channel_policy
from company_webhook_sender import resolve_agent_webhook_name


SUPPORTED_SENDER_MODES = ["bot_fallback", "webhook", "real_bot", "auto"]

AGENT_BOT_TOKEN_ENV = {
    "lucy": "HERMES_DISCORD_LUCY_BOT_TOKEN",
    "marin": "HERMES_DISCORD_MARIN_BOT_TOKEN",
    "meiko": "HERMES_DISCORD_MEIKO_BOT_TOKEN",
    "kasumi": "HERMES_DISCORD_KASUMI_BOT_TOKEN",
    "reze": "HERMES_DISCORD_REZE_BOT_TOKEN",
}


@dataclass(frozen=True)
class AgentBotClientSpec:
    agent_id: str
    bot_name: str
    token_env: str
    token_present: bool
    token_value_logged: bool = False


def resolve_agent_bot_name(agent_id: str) -> str:
    return resolve_agent_webhook_name(agent_id)


def agent_bot_names() -> dict[str, str]:
    return {agent_id: resolve_agent_bot_name(agent_id) for agent_id in AGENT_IDS}


def load_agent_bot_token_presence(env: dict[str, Any] | None = None) -> dict[str, bool]:
    env_map = dict(os.environ if env is None else env)
    return {agent_id: bool(env_map.get(token_env)) for agent_id, token_env in AGENT_BOT_TOKEN_ENV.items()}


def build_agent_bot_specs(env: dict[str, Any] | None = None) -> list[AgentBotClientSpec]:
    presence = load_agent_bot_token_presence(env)
    return [
        AgentBotClientSpec(
            agent_id=agent_id,
            bot_name=resolve_agent_bot_name(agent_id),
            token_env=AGENT_BOT_TOKEN_ENV[agent_id],
            token_present=presence[agent_id],
        )
        for agent_id in AGENT_IDS
    ]


def build_company_agent_real_bot_fleet_report(env: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "report_type": "company_agent_real_bot_fleet_report",
        "real_bot_fleet_available": True,
        "default_real_bots_enabled": False,
        "default_sender_mode": "bot_fallback",
        "supported_sender_modes": list(SUPPORTED_SENDER_MODES),
        "agent_bot_names": agent_bot_names(),
        "agent_bot_token_env_keys": dict(AGENT_BOT_TOKEN_ENV),
        "agent_bot_token_presence": load_agent_bot_token_presence(env),
        "agent_bot_clients_send_only": True,
        "agent_bot_on_message_responds": False,
        "hermes_ignores_bot_authors": True,
        "agent_bot_token_values_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution_allowed": False,
    }


def build_company_agent_real_bot_send_dry_run(agent_id: str, channel_name: str, message: str) -> dict[str, Any]:
    return {
        "report_type": "company_agent_real_bot_send_dry_run",
        "selected_agent": agent_id,
        "agent_bot_name": resolve_agent_bot_name(agent_id),
        "target_channel": channel_name,
        "message_present": bool(str(message or "").strip()),
        "would_use_real_bot": True,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "agent_bot_login_attempted": False,
        "webhook_created": False,
        "agent_bot_token_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution_performed": False,
    }


def sender_order_for_mode(mode: str, *, real_bots_enabled: bool, webhook_enabled: bool) -> list[str]:
    normalized = str(mode or "bot_fallback").strip().lower()
    if normalized not in SUPPORTED_SENDER_MODES:
        normalized = "bot_fallback"
    if normalized == "bot_fallback":
        return ["bot_fallback"]
    if normalized == "webhook":
        return ["webhook", "bot_fallback"] if webhook_enabled else ["bot_fallback"]
    if normalized == "real_bot":
        order = ["real_bot"] if real_bots_enabled else []
        if webhook_enabled:
            order.append("webhook")
        order.append("bot_fallback")
        return order
    order = []
    if real_bots_enabled:
        order.append("real_bot")
    order.append("webhook")
    order.append("bot_fallback")
    return order


class AgentBotFleet:
    """Container for send-only agent bot clients.

    The agent clients deliberately do not implement message response behavior;
    HERMES_STOXL remains the only router.
    """

    def __init__(self, clients: dict[str, Any] | None = None, tasks: dict[str, asyncio.Task] | None = None) -> None:
        self.clients = clients or {}
        self.tasks = tasks or {}
        self.agent_bot_user_ids: set[Any] = set()

    async def send_as_real_agent_bot(self, agent_id: str, channel_name: str, content: str) -> dict[str, Any]:
        client = self.clients.get(agent_id)
        if client is None:
            return _blocked_real_bot("agent_bot_client_missing", agent_id, channel_name)
        target = None
        for channel in client.get_all_channels():
            if getattr(channel, "name", "") == channel_name:
                target = channel
                break
        if target is None:
            return _blocked_real_bot("target_channel_missing", agent_id, channel_name)
        if not get_channel_policy(channel_name)["known_channel"]:
            return _blocked_real_bot("unknown_channel", agent_id, channel_name)
        try:
            outbound = str(content or "")
            if len(outbound) > 1900:
                return {
                    "blocked": True,
                    "blocked_reasons": ["discord_message_too_long"],
                    "discord_api_send_called": False,
                    "discord_message_sent": False,
                    "message_sent_count": 0,
                    "raw_discord_ids_logged": False,
                    "secret_values_logged": False,
                }
            await target.send(outbound)
        except Exception:
            return _blocked_real_bot("agent_bot_send_failed", agent_id, channel_name)
        return {
            "report_type": "company_agent_real_bot_send_result",
            "blocked": False,
            "agent_id": agent_id,
            "agent_bot_name": resolve_agent_bot_name(agent_id),
            "target_channel": channel_name,
            "real_bot_sender_used": True,
            "discord_api_send_called": True,
            "discord_message_sent": True,
            "message_sent_count": 1,
            "agent_bot_token_value_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
            "external_execution": False,
        }

    async def stop_agent_bot_clients(self) -> dict[str, Any]:
        for client in self.clients.values():
            close = getattr(client, "close", None)
            if close is not None:
                await close()
        for task in self.tasks.values():
            if not task.done():
                task.cancel()
        return {
            "agent_bot_clients_stopped": True,
            "agent_bot_token_values_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }


async def start_agent_bot_clients(env: dict[str, Any] | None = None) -> AgentBotFleet:
    env_map = dict(os.environ if env is None else env)
    try:
        import discord  # type: ignore
    except ImportError:
        return AgentBotFleet()
    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = False
    clients: dict[str, Any] = {}
    tasks: dict[str, asyncio.Task] = {}
    for spec in build_agent_bot_specs(env_map):
        token = env_map.get(spec.token_env)
        if not token:
            continue
        client = discord.Client(intents=intents)

        @client.event
        async def on_message(_message: Any) -> None:
            return None

        clients[spec.agent_id] = client
        tasks[spec.agent_id] = asyncio.create_task(client.start(token))
    return AgentBotFleet(clients, tasks)


async def stop_agent_bot_clients(fleet: AgentBotFleet | None) -> dict[str, Any]:
    if fleet is None:
        return {
            "agent_bot_clients_stopped": False,
            "agent_bot_token_values_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    return await fleet.stop_agent_bot_clients()


async def send_as_real_agent_bot(
    fleet: AgentBotFleet | None,
    agent_id: str,
    channel_name: str,
    content: str,
) -> dict[str, Any]:
    if fleet is None:
        return _blocked_real_bot("agent_bot_fleet_missing", agent_id, channel_name)
    return await fleet.send_as_real_agent_bot(agent_id, channel_name, content)


def _blocked_real_bot(reason: str, agent_id: str, channel_name: str) -> dict[str, Any]:
    return {
        "report_type": "company_agent_real_bot_send_blocked",
        "blocked": True,
        "blocked_reasons": [reason],
        "agent_id": agent_id,
        "agent_bot_name": resolve_agent_bot_name(agent_id),
        "target_channel": channel_name,
        "real_bot_sender_used": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "agent_bot_token_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution": False,
    }
