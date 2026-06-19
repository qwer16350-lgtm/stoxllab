"""Webhook persona sender boundary for company agents.

Actual webhook delivery is intentionally narrow: callers must inject a sender
adapter and provide an explicit allow flag. Reports never include webhook URLs
or raw Discord IDs.
"""

from __future__ import annotations

from typing import Any, Callable

from company_agent_registry import get_agent, get_channel_policy


SenderAdapter = Callable[[str, str, str], dict[str, Any]]


def send_as_agent(
    agent_id: str,
    channel_name: str,
    content: str,
    *,
    allow_send: bool = False,
    sender_adapter: SenderAdapter | None = None,
) -> dict[str, Any]:
    agent = get_agent(agent_id)
    policy = get_channel_policy(channel_name)
    if not agent:
        return _blocked("unknown_agent", agent_id, channel_name)
    if not policy["known_channel"]:
        return _blocked("unknown_channel", agent_id, channel_name)
    if not allow_send or sender_adapter is None:
        return _blocked("webhook_send_not_allowed", agent_id, channel_name, persona=agent["webhook_persona"])
    result = sender_adapter(agent_id, channel_name, content)
    return {
        "report_type": "company_webhook_send_result",
        "blocked": False,
        "agent_id": agent_id,
        "webhook_persona": agent["webhook_persona"],
        "channel_name": channel_name,
        "discord_api_send_called": bool(result.get("discord_api_send_called", True)),
        "discord_message_sent": bool(result.get("discord_message_sent", True)),
        "message_sent_count": int(result.get("message_sent_count", 1) or 1),
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution": False,
    }


def _blocked(reason: str, agent_id: str, channel_name: str, persona: str | None = None) -> dict[str, Any]:
    return {
        "report_type": "company_webhook_send_blocked",
        "blocked": True,
        "blocked_reasons": [reason],
        "agent_id": agent_id,
        "webhook_persona": persona,
        "channel_name": channel_name,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution": False,
    }
