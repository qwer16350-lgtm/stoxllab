"""Webhook persona sender boundary for company agents."""

from __future__ import annotations

from typing import Any, Callable

from company_agent_registry import AGENT_IDS, get_agent, get_channel_policy


SenderAdapter = Callable[[str, str, str], dict[str, Any]]


def resolve_agent_webhook_name(agent_id: str) -> str:
    agent = get_agent(agent_id)
    if agent:
        return str(agent.get("webhook_persona") or str(agent_id).upper())
    return str(agent_id or "unknown").upper()


def agent_webhook_names() -> dict[str, str]:
    return {agent_id: resolve_agent_webhook_name(agent_id) for agent_id in AGENT_IDS}


def build_company_agent_webhook_persona_report() -> dict[str, Any]:
    return {
        "report_type": "company_agent_webhook_persona_report",
        "webhook_persona_mode_available": True,
        "default_webhook_persona_enabled": False,
        "webhook_create_supported": True,
        "bot_message_fallback_supported": True,
        "agent_webhook_names": agent_webhook_names(),
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution_allowed": False,
    }


def build_company_agent_webhook_persona_dry_run(
    agent_id: str,
    channel_name: str,
    message: str,
    *,
    webhook_persona_enabled: bool = False,
    webhook_create_enabled: bool = True,
) -> dict[str, Any]:
    policy = get_channel_policy(channel_name)
    agent = get_agent(agent_id)
    return {
        "report_type": "company_agent_webhook_persona_dry_run",
        "selected_agent": agent_id,
        "agent_display_name": agent.get("display_name") if agent else None,
        "channel_name": channel_name,
        "known_channel": bool(policy["known_channel"]),
        "message_present": bool(str(message or "").strip()),
        "webhook_name": resolve_agent_webhook_name(agent_id),
        "webhook_persona_enabled": bool(webhook_persona_enabled),
        "webhook_create_enabled": bool(webhook_create_enabled),
        "would_use_webhook_persona": bool(agent and policy["known_channel"]),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "webhook_created": False,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution": False,
        "external_execution_allowed": False,
    }


async def get_or_create_agent_webhook(channel: Any, agent_id: str, *, create_enabled: bool = True) -> dict[str, Any]:
    webhook_name = resolve_agent_webhook_name(agent_id)
    try:
        existing_hooks = await channel.webhooks()
    except Exception:
        return _blocked("webhook_lookup_failed", agent_id, getattr(channel, "name", ""), persona=webhook_name)
    for hook in existing_hooks or []:
        if getattr(hook, "name", "") == webhook_name:
            return {
                "blocked": False,
                "webhook": hook,
                "webhook_name": webhook_name,
                "webhook_created": False,
                "webhook_reused": True,
                "webhook_url_value_logged": False,
                "raw_discord_ids_logged": False,
                "secret_values_logged": False,
            }
    if not create_enabled:
        return _blocked("webhook_missing_create_disabled", agent_id, getattr(channel, "name", ""), persona=webhook_name)
    try:
        hook = await channel.create_webhook(name=webhook_name)
    except Exception:
        return _blocked("webhook_create_failed", agent_id, getattr(channel, "name", ""), persona=webhook_name)
    return {
        "blocked": False,
        "webhook": hook,
        "webhook_name": webhook_name,
        "webhook_created": True,
        "webhook_reused": False,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


async def send_as_agent_webhook(
    agent_id: str,
    channel: Any,
    content: str,
    *,
    create_enabled: bool = True,
) -> dict[str, Any]:
    channel_name = str(getattr(channel, "name", "") or "")
    agent = get_agent(agent_id)
    policy = get_channel_policy(channel_name)
    persona = resolve_agent_webhook_name(agent_id)
    if not agent:
        return _blocked("unknown_agent", agent_id, channel_name, persona=persona)
    if not policy["known_channel"]:
        return _blocked("unknown_channel", agent_id, channel_name, persona=persona)
    hook_result = await get_or_create_agent_webhook(channel, agent_id, create_enabled=create_enabled)
    if hook_result.get("blocked"):
        return hook_result
    try:
        outbound = str(content or "")
        if len(outbound) > 1900:
            return _blocked("discord_message_too_long", agent_id, channel_name, persona=persona)
        await hook_result["webhook"].send(outbound, username=persona)
    except Exception:
        return _blocked("webhook_send_failed", agent_id, channel_name, persona=persona)
    return {
        "report_type": "company_webhook_send_result",
        "blocked": False,
        "agent_id": agent_id,
        "webhook_persona_used": True,
        "webhook_name": persona,
        "webhook_created": bool(hook_result.get("webhook_created")),
        "webhook_reused": bool(hook_result.get("webhook_reused")),
        "channel_name": channel_name,
        "discord_api_send_called": True,
        "discord_message_sent": True,
        "message_sent_count": 1,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution": False,
    }


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
        "webhook_persona_used": True,
        "webhook_name": agent["webhook_persona"],
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
        "webhook_persona_used": False,
        "webhook_name": persona,
        "channel_name": channel_name,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "external_execution": False,
    }
