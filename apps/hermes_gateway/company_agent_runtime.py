"""Company agent runtime for STOXL Discord Agent OS v0."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from company_context_store import (
    context_from_replied_message,
    detect_context_reference_terms,
    get_latest_context_for_channel,
    resolve_handoff_context,
)
from company_agent_bot_fleet import (
    build_company_agent_real_bot_fleet_report,
    build_company_agent_real_bot_send_dry_run,
    resolve_agent_bot_name,
    send_as_real_agent_bot,
    sender_order_for_mode,
    start_agent_bot_clients,
    stop_agent_bot_clients,
)
from company_agent_registry import get_channel_policy, load_company_registry
from company_agent_router import (
    build_company_agent_org_report,
    extract_first_command_line,
    normalize_discord_message_content,
    route_company_agent_message,
)
from company_agent_responder import build_approval_draft, build_company_agent_response
from company_handoff import build_handoff_post_payload, store_company_handoff_context
from company_webhook_sender import send_as_agent
from company_webhook_sender import send_as_agent_webhook
from company_webhook_sender import resolve_agent_webhook_name
from safety_report_builders import build_blocked_report


COMMAND_SYNTAX = [
    "!lucy",
    "!marin",
    "!meiko",
    "!kasumi",
    "!reze",
    "!agent",
    "!route",
    "!handoff",
    "!review",
    "!approve-draft",
    "!agents",
    "!help",
]


def build_company_agent_router_dry_run(channel: str, message: str) -> dict[str, Any]:
    route = route_company_agent_message(channel, message)
    if route.get("selected_agent"):
        response = build_company_agent_response(str(route["selected_agent"]), message, route, dict(os.environ))
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
        "handoff_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_HANDOFF_ENABLED", "false")),
        "webhook_persona_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED", "false")),
        "webhook_create_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_WEBHOOK_CREATE_ENABLED", "true"), default=True),
        "real_bots_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED", "false")),
        "sender_mode": str(env_map.get("HERMES_COMPANY_AGENT_SENDER_MODE", "bot_fallback") or "bot_fallback").strip().lower(),
    }


def resolve_target_channel_by_name(channels: Any, target_name: str) -> dict[str, Any]:
    found = False
    for channel in channels or []:
        if getattr(channel, "name", "") == target_name:
            found = True
            break
    return {
        "target_channel_name": target_name,
        "target_channel_found": found,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def _find_target_channel(client: Any, target_name: str) -> Any | None:
    for channel in client.get_all_channels():
        if getattr(channel, "name", "") == target_name:
            return channel
    return None


def build_company_agent_runtime_report(allow_flag_present: bool = False) -> dict[str, Any]:
    runtime_env = _runtime_env()
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
                "handoff_posting_enabled": bool(runtime_env["handoff_enabled"]),
                "webhook_persona_enabled": bool(runtime_env["webhook_persona_enabled"]),
                "webhook_create_enabled": bool(runtime_env["webhook_create_enabled"]),
                "real_bots_enabled": bool(runtime_env["real_bots_enabled"]),
                "sender_mode": runtime_env["sender_mode"],
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
        "handoff_posting_enabled": bool(runtime_env["handoff_enabled"]),
        "webhook_persona_enabled": bool(runtime_env["webhook_persona_enabled"]),
        "webhook_create_enabled": bool(runtime_env["webhook_create_enabled"]),
        "real_bots_enabled": bool(runtime_env["real_bots_enabled"]),
        "sender_mode": runtime_env["sender_mode"],
        "sender_order": sender_order_for_mode(
            runtime_env["sender_mode"],
            real_bots_enabled=bool(runtime_env["real_bots_enabled"]),
            webhook_enabled=bool(runtime_env["webhook_persona_enabled"]),
        ),
    }


def should_ignore_message(message: Any, bot_user: Any | None = None, agent_bot_user_ids: set[Any] | None = None) -> tuple[bool, str]:
    content = str(getattr(message, "content", "") or "").strip()
    author = getattr(message, "author", None)
    if not content:
        return True, "empty_message"
    if bool(getattr(author, "bot", False)):
        return True, "bot_message"
    if bot_user is not None and getattr(author, "id", None) == getattr(bot_user, "id", None):
        return True, "self_message"
    if agent_bot_user_ids and getattr(author, "id", None) in agent_bot_user_ids:
        return True, "agent_bot_message"
    channel_name = str(getattr(getattr(message, "channel", None), "name", "") or "")
    if not get_channel_policy(channel_name)["known_channel"]:
        return True, "unknown_channel"
    return False, ""


def build_company_agent_message_result(
    channel_name: str,
    content: str,
    replied_message_content: str = "",
    env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route = route_company_agent_message(channel_name, content)
    if route.get("blocked"):
        return {
            **route,
            "reply_prepared": False,
            "send_strategy": "blocked",
            "bot_message_fallback_used": False,
        }
    command = route.get("command")
    if command in {"agents", "help"}:
        return {
            **route,
            "reply_prepared": True,
            "response": {
                "response_type": "company_agent_command_response",
                "reply_text_source": command,
                "content": _command_response_text(command),
                "llm_api_call_attempted": False,
                "rag_called": False,
                "external_execution": False,
            },
            "webhook_send_available": False,
            "bot_message_fallback_used": True,
            "send_strategy": "bot_message_fallback",
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
            "webhook_url_value_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    selected_agent = str(route.get("selected_agent") or "")
    routed_content = extract_first_command_line(content) or normalize_discord_message_content(content)
    replied_context = context_from_replied_message(replied_message_content, channel_name, selected_agent)
    context_resolution = resolve_handoff_context(selected_agent, routed_content, channel_name, replied_context)
    route["context_reference_detected"] = bool(context_resolution["context_reference_detected"])
    route["handoff_context_used"] = bool(context_resolution["context_used"])
    route["handoff_context_priority"] = context_resolution["context_priority"]
    route["handoff_context_source_agent"] = context_resolution["context_source_agent"]
    if context_resolution.get("context_used"):
        route["handoff_context"] = context_resolution["context"]
    response = build_company_agent_response(selected_agent, routed_content, route, dict(os.environ if env is None else env))
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


def build_company_agent_context_dry_run(
    channel: str,
    message: str,
    replied_message_content: str = "",
) -> dict[str, Any]:
    latest = get_latest_context_for_channel(channel)
    context_origin = "in_memory_store"
    if latest is None and detect_context_reference_terms(message):
        known_pairs = {
            "meiko-검토": ("kasumi", "meiko", "kasumi-리서치"),
            "lucy-검토": ("marin", "lucy", "marketing-brief"),
            "대표-회의실": ("reze", "reze", "reze-전략기획"),
        }
        pair = known_pairs.get(channel)
        if pair:
            store_company_handoff_context(
                pair[0],
                pair[1],
                pair[2],
                channel,
                "dry-run fixture",
                "context resolution dry-run",
                "dry-run simulated recent handoff; runtime uses only actual in-memory handoffs",
                f"{pair[1]} 검토 필요",
            )
            latest = get_latest_context_for_channel(channel)
            context_origin = "dry_run_fixture"
    safe_env = dict(os.environ)
    safe_env["HERMES_COMPANY_AGENT_LLM_ENABLED"] = "false"
    safe_env["HERMES_COMPANY_AGENT_LLM_MODE"] = "off"
    safe_env["HERMES_COMPANY_AGENT_REPLY_MODE"] = "deterministic_fallback"
    result = build_company_agent_message_result(channel, message, replied_message_content, safe_env)
    response = result.get("response", {}) if isinstance(result.get("response"), dict) else {}
    return {
        "report_type": "company_agent_context_dry_run",
        "channel": channel,
        "selected_agent": result.get("selected_agent"),
        "context_reference_detected": detect_context_reference_terms(message),
        "latest_context_available": latest is not None,
        "reply_context_available": bool(replied_message_content),
        "context_source_agent": result.get("handoff_context_source_agent"),
        "context_target_agent": (latest or {}).get("target_agent") if latest else result.get("selected_agent"),
        "context_used": bool(result.get("handoff_context_used")),
        "context_priority": result.get("handoff_context_priority", "none"),
        "context_origin": context_origin if latest else "none",
        "deterministic_response_context_used": bool(response.get("handoff_context_used")),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_company_agent_context_handoff_simulation(
    source_agent: str,
    target_agent: str,
    target_channel: str,
    content: str,
) -> dict[str, Any]:
    source_channels = {
        "marin": "marketing-brief",
        "kasumi": "kasumi-리서치",
        "reze": "reze-전략기획",
        "lucy": "lucy-검토",
        "meiko": "meiko-검토",
    }
    stored = store_company_handoff_context(
        source_agent,
        target_agent,
        source_channels.get(source_agent, "company-agent-source"),
        target_channel,
        "simulated handoff",
        content,
        content,
        f"{target_agent} 검토 필요",
    )
    latest = get_latest_context_for_channel(target_channel)
    return {
        "report_type": "company_agent_context_simulate_handoff",
        "handoff_context_saved": latest is not None,
        "target_channel": target_channel,
        "context_source_agent": stored.get("source_agent"),
        "context_target_agent": stored.get("target_agent"),
        "latest_context_available": latest is not None,
        "created_at_present": bool(stored.get("created_at_present")),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def _command_response_text(command: str) -> str:
    if command == "agents":
        return (
            "STOXL agents:\n"
            "- marin: 마케팅 주니어 -> lucy\n"
            "- lucy: 마케팅 시니어 -> 최종-승인요청\n"
            "- kasumi: 운영 주니어 -> meiko\n"
            "- meiko: 운영 시니어 -> 최종-승인요청\n"
            "- reze: 전략기획실 -> 대표-회의실"
        )
    return (
        "Commands: !lucy, !marin, !meiko, !kasumi, !reze, !agent, !route, "
        "!handoff, !review, !approve-draft, !agents, !help"
    )


def _handoff_post_for_result(result: dict[str, Any]) -> dict[str, Any]:
    response = result.get("response", {})
    target_channel = result.get("handoff_channel") or result.get("target_channel")
    selected_agent = result.get("selected_agent")
    payload = build_handoff_post_payload(result)
    return {
        "handoff_post_supported": bool(payload.get("handoff_supported")),
        "handoff_posting_enabled": _runtime_env()["handoff_enabled"],
        "handoff_target_channel": target_channel,
        "handoff_from_agent": selected_agent,
        "handoff_message_present": bool(payload.get("handoff_message") or response.get("content")),
        "handoff_message_preview_present": bool(payload.get("handoff_message_preview_present")),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_company_agent_handoff_dry_run(channel: str, message: str, env: dict[str, Any] | None = None) -> dict[str, Any]:
    result = build_company_agent_message_result(channel, message)
    routed_message = extract_first_command_line(message) or normalize_discord_message_content(message)
    payload = build_handoff_post_payload(result, routed_message)
    return {
        "report_type": "company_agent_handoff_dry_run",
        "selected_agent": result.get("selected_agent"),
        "agent_display_name": result.get("agent_display_name"),
        "agent_bot_name": resolve_agent_bot_name(str(result.get("selected_agent") or "")),
        "webhook_name": resolve_agent_webhook_name(str(result.get("selected_agent") or "")),
        "handoff_enabled": bool(_runtime_env(env)["handoff_enabled"]),
        "handoff_supported": bool(payload.get("handoff_supported")),
        "handoff_target_channel": payload.get("handoff_target_channel") or result.get("handoff_channel"),
        "handoff_message_preview_present": bool(payload.get("handoff_message_preview_present")),
        "handoff_message_preview": payload.get("handoff_message", ""),
        "blocked": bool(payload.get("blocked", False)),
        "blocked_reasons": list(payload.get("blocked_reasons", [])),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "external_execution_allowed": False,
        "external_execution_performed": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "webhook_url_value_logged": False,
    }


def build_company_agent_approval_dry_run(channel: str, message: str, env: dict[str, Any] | None = None) -> dict[str, Any]:
    result = build_company_agent_message_result(channel, message)
    selected_agent = str(result.get("selected_agent") or "lucy")
    routed_message = extract_first_command_line(message) or normalize_discord_message_content(message)
    draft = build_approval_draft(selected_agent, routed_message, result)
    return {
        "report_type": "company_agent_approval_dry_run",
        "selected_agent": result.get("selected_agent"),
        "agent_display_name": result.get("agent_display_name"),
        "agent_bot_name": resolve_agent_bot_name(str(result.get("selected_agent") or "")),
        "webhook_name": resolve_agent_webhook_name(str(result.get("selected_agent") or "")),
        "handoff_enabled": bool(_runtime_env(env)["handoff_enabled"]),
        "approval_draft_supported": True,
        "approval_target_channel": draft.get("approval_channel"),
        "approval_message_preview_present": bool(draft.get("content")),
        "approval_message_preview": draft.get("content", ""),
        "external_execution_requested": bool(draft.get("external_execution_requested")),
        "external_execution_performed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "webhook_url_value_logged": False,
    }


def build_company_agent_workflow_v01_report() -> dict[str, Any]:
    registry = load_company_registry()
    return {
        "report_type": "company_agent_workflow_v01_report",
        "workflow_v01_available": True,
        "agent_templates_upgraded": True,
        "handoff_posting_supported": True,
        "handoff_posting_default_enabled": False,
        "approval_draft_supported": True,
        "external_execution_allowed": False,
        "llm_enabled_by_default": False,
        "agent_count": len(registry["agents"]),
        "senior_junior_hierarchy": {
            "marin": "lucy",
            "kasumi": "meiko",
            "reze": "대표-회의실",
        },
        "command_syntax": list(COMMAND_SYNTAX),
        "token_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "webhook_url_value_logged": False,
    }


def build_company_agent_workflow_dry_run(channel: str, message: str, env: dict[str, Any] | None = None) -> dict[str, Any]:
    result = build_company_agent_message_result(channel, message)
    selected_agent = str(result.get("selected_agent") or "")
    approval_draft = {}
    routed_message = extract_first_command_line(message) or normalize_discord_message_content(message)
    if selected_agent in {"lucy", "meiko"} or result.get("requires_approval") or routed_message.startswith("!approve-draft"):
        approval_draft = build_approval_draft(selected_agent or "lucy", routed_message, result)
    handoff_post = _handoff_post_for_result(result) if result.get("reply_prepared") else {}
    handoff_enabled = _runtime_env(env)["handoff_enabled"]
    if handoff_post:
        handoff_post["handoff_posting_enabled"] = handoff_enabled
    return {
        "report_type": "company_agent_workflow_dry_run",
        "selected_agent": result.get("selected_agent"),
        "agent_display_name": result.get("agent_display_name"),
        "source_channel": channel,
        "target_channel": result.get("target_channel"),
        "response_preview_present": bool(result.get("response")),
        "handoff_target": result.get("handoff_channel") or result.get("handoff_to"),
        "handoff_post": handoff_post,
        "approval_draft_created": bool(approval_draft.get("approval_draft_created", False)),
        "approval_draft": approval_draft,
        "blocked": bool(result.get("blocked", False)),
        "blocked_reasons": list(result.get("blocked_reasons", [])),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "external_execution_allowed": False,
        "external_execution_requested": bool(result.get("external_execution_requested", False)),
        "external_execution_performed": False,
        "token_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "webhook_url_value_logged": False,
    }


async def _send_agent_content(client: Any, agent_id: str, channel: Any, content: str) -> dict[str, Any]:
    env = _runtime_env()
    channel_name = str(getattr(channel, "name", "") or "")
    order = sender_order_for_mode(
        env["sender_mode"],
        real_bots_enabled=bool(env["real_bots_enabled"]),
        webhook_enabled=bool(env["webhook_persona_enabled"]),
    )
    attempts: list[str] = []
    for sender in order:
        attempts.append(sender)
        if sender == "real_bot":
            fleet = getattr(client, "_agent_bot_fleet", None)
            real_result = await send_as_real_agent_bot(fleet, agent_id, channel_name, content)
            if not real_result.get("blocked"):
                return {**real_result, "send_strategy": "real_bot", "sender_attempt_order": attempts}
        elif sender == "webhook":
            webhook_result = await send_as_agent_webhook(
                agent_id,
                channel,
                content,
                create_enabled=bool(env["webhook_create_enabled"]),
            )
            if not webhook_result.get("blocked"):
                return {**webhook_result, "send_strategy": "webhook", "sender_attempt_order": attempts}
        elif sender == "bot_fallback":
            await channel.send(str(content or "")[:1900])
            return {
                "sent": True,
                "send_strategy": "bot_fallback",
                "sender_attempt_order": attempts,
                "bot_message_fallback_used": True,
                "webhook_url_value_logged": False,
                "raw_discord_ids_logged": False,
                "secret_values_logged": False,
            }
    await channel.send(str(content or "")[:1900])
    return {
        "sent": True,
        "send_strategy": "bot_fallback",
        "sender_attempt_order": attempts + ["bot_fallback"],
        "bot_message_fallback_used": True,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


async def _send_runtime_reply(message: Any, result: dict[str, Any], client: Any | None = None) -> dict[str, Any]:
    response = result.get("response", {})
    content = str(response.get("content", "") or "")
    if not content:
        return {"sent": False, "send_strategy": "empty_content"}
    selected_agent = str(result.get("selected_agent") or "")
    if client is not None and selected_agent:
        return await _send_agent_content(client, selected_agent, message.channel, content)
    await message.channel.send(content[:1900])
    return {"sent": True, "send_strategy": "bot_fallback", "bot_message_fallback_used": True}


async def _referenced_message_content(message: Any) -> str:
    referenced = getattr(message, "referenced_message", None)
    reference = getattr(message, "reference", None)
    if referenced is None and reference is not None:
        referenced = getattr(reference, "resolved", None)
    content = str(getattr(referenced, "content", "") or "")
    if content or reference is None:
        return content
    message_id = getattr(reference, "message_id", None)
    fetch_message = getattr(getattr(message, "channel", None), "fetch_message", None)
    if message_id is None or not callable(fetch_message):
        return ""
    try:
        fetched = await fetch_message(message_id)
    except Exception:
        return ""
    return str(getattr(fetched, "content", "") or "")


async def _send_handoff_post(client: Any, result: dict[str, Any]) -> None:
    if not _runtime_env()["handoff_enabled"]:
        return
    selected_agent = str(result.get("selected_agent") or "")
    command = str(result.get("command") or "")
    if selected_agent in {"lucy", "meiko"} and (command == "approve-draft" or result.get("requires_approval")):
        routed_message = str(result.get("response", {}).get("content", "") or "")
        approval = build_approval_draft(selected_agent, routed_message, result)
        target_name = str(approval.get("approval_channel") or "")
        content = str(approval.get("content") or "")
        if target_name and content:
            store_company_handoff_context(
                selected_agent,
                "final-approval",
                str(result.get("source_channel") or ""),
                target_name,
                "approval requested",
                routed_message,
                content,
                "최종 승인 검토 필요",
            )
    else:
        payload = build_handoff_post_payload(result)
        target_name = str(payload.get("handoff_target_channel") or "")
        content = str(payload.get("handoff_message") or "")
    if not target_name or not content:
        return
    target_channel = _find_target_channel(client, target_name)
    if target_channel is None:
        current_channel = getattr(client, "_current_message_channel", None)
        if current_channel is not None:
            await current_channel.send(
                "[HANDOFF_BLOCKED]\n"
                f"target_channel: {target_name}\n"
                "reason: target_channel_missing\n"
                "external_execution_performed: false"
            )
        return
    if selected_agent:
        await _send_agent_content(client, selected_agent, target_channel, content)
        return
    await target_channel.send(content[:1900])


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
    client._agent_bot_fleet = None
    if _runtime_env()["real_bots_enabled"]:
        client._agent_bot_fleet = await start_agent_bot_clients()
    printed_ready = False

    @client.event
    async def on_ready() -> None:
        nonlocal printed_ready
        if not printed_ready:
            print(json.dumps(start_report, ensure_ascii=False, indent=2), flush=True)
            printed_ready = True

    @client.event
    async def on_message(message: Any) -> None:
        fleet = getattr(client, "_agent_bot_fleet", None)
        agent_bot_user_ids = getattr(fleet, "agent_bot_user_ids", set()) if fleet is not None else set()
        ignored, _reason = should_ignore_message(message, bot_user=client.user, agent_bot_user_ids=agent_bot_user_ids)
        if ignored:
            return
        channel_name = str(getattr(message.channel, "name", "") or "")
        replied_content = await _referenced_message_content(message)
        result = build_company_agent_message_result(
            channel_name,
            str(getattr(message, "content", "") or ""),
            replied_content,
        )
        if result.get("reply_prepared") and result.get("bot_message_fallback_used"):
            await _send_runtime_reply(message, result, client=client)
            client._current_message_channel = message.channel
            await _send_handoff_post(client, result)
            client._current_message_channel = None

    try:
        await client.start(token)
    finally:
        await stop_agent_bot_clients(getattr(client, "_agent_bot_fleet", None))
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
