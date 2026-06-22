"""Dry-run router for STOXL Discord company agents."""

from __future__ import annotations

import re
from typing import Any

from company_agent_registry import (
    AGENT_IDS,
    get_agent,
    get_channel_policy,
    get_default_agent_for_channel,
    load_company_registry,
)
from company_handoff import build_handoff_message, get_handoff_rule


COMMAND_RE = re.compile(r"^!(lucy|marin|meiko|kasumi|reze|agent|route|handoff|review|approve-draft|agents|help)(?:\s+(.+))?$", re.I)
EXTERNAL_ACTION_WORDS = (
    "publish",
    "deploy",
    "submit",
    "send email",
    "email send",
    "sns 게시",
    "게시",
    "배포",
    "제출",
    "업로드",
)


def _contains_any(text: str, words: tuple[str, ...] | list[str]) -> bool:
    lowered = text.lower()
    return any(word.lower() in lowered for word in words)


def _is_review_request(message: str) -> bool:
    return _contains_any(message, ("review", "검토", "최종", "승인", "확인"))


def _is_marketing(message: str) -> bool:
    return _contains_any(message, ("sns", "homepage", "홈페이지", "콘텐츠", "content", "marketing", "마케팅", "문구"))


def _is_operation(message: str) -> bool:
    return _contains_any(message, ("지원", "공모", "마감", "일정", "grant", "support", "deadline", "운영"))


def _is_strategy(message: str) -> bool:
    return _contains_any(message, ("전략", "브랜드", "아이디어", "product", "business", "방향", "기획"))


def _target_channel_for_agent(agent_id: str) -> str:
    agent = get_agent(agent_id)
    return str(agent.get("default_channel")) if agent else "unknown"


EXACT_CHANNEL_DEFAULTS = {
    "meiko-검토": "meiko",
    "lucy-검토": "lucy",
    "marin-초안": "marin",
    "kasumi-리서치": "kasumi",
    "reze-전략기획": "reze",
}


def _exact_channel_default(channel_name: str) -> tuple[str | None, str, str] | None:
    agent_id = EXACT_CHANNEL_DEFAULTS.get(channel_name)
    if not agent_id:
        return None
    return agent_id, _target_channel_for_agent(agent_id), "exact_channel_default"


def _handoff_command_target(target: str) -> tuple[str, str]:
    normalized = str(target or "").strip().lower()
    if normalized == "reze":
        rule = get_handoff_rule("reze") or {}
        return "reze", str(rule.get("target_channel") or _target_channel_for_agent("reze"))
    if normalized in AGENT_IDS:
        return normalized, _target_channel_for_agent(normalized)
    return get_default_agent_for_channel(target) or "", target


def _route_by_channel(channel_name: str, message: str) -> tuple[str | None, str, str]:
    if channel_name in {"marin-초안", "sns-콘텐츠", "homepage", "marketing-brief"}:
        if _is_review_request(message):
            return "lucy", "lucy-검토", "marketing_review_request"
        return "marin", "marin-초안", "sns_draft_request"
    if channel_name == "lucy-검토":
        return "lucy", "lucy-검토", "marketing_review_channel"
    if channel_name in {"kasumi-리서치", "공모전-지원사업", "operation-brief"}:
        if _is_review_request(message) or _contains_any(message, ("판단", "추천", "보류", "마감", "일정")):
            return "meiko", "meiko-검토", "operation_decision_request"
        return "kasumi", "kasumi-리서치", "operation_research_request"
    if channel_name in {"meiko-검토", "일정-마감관리"}:
        return "meiko", "meiko-검토", "operation_review_channel"
    if channel_name in {"reze-전략기획", "brand-rag", "new-business", "product-ideas"}:
        return "reze", "reze-전략기획", "strategy_request"
    if channel_name == "대표-회의실":
        if _is_marketing(message):
            return "lucy", "최종-승인요청", "decision_marketing_review"
        if _is_operation(message):
            return "meiko", "최종-승인요청", "decision_operation_review"
        return "reze", "대표-회의실", "decision_strategy_review"
    if channel_name == "최종-승인요청":
        if _is_operation(message):
            return "meiko", "최종-승인요청", "final_operation_approval_request"
        if _is_strategy(message):
            return "reze", "대표-회의실", "final_strategy_approval_request"
        return "lucy", "최종-승인요청", "final_marketing_approval_request"
    default_agent = get_default_agent_for_channel(channel_name)
    if default_agent:
        return default_agent, _target_channel_for_agent(default_agent), "channel_default_route"
    return None, channel_name, "unknown_channel"


def _route_by_message(channel_name: str, message: str) -> tuple[str | None, str, str]:
    if _is_strategy(message):
        return "reze", "reze-전략기획", "strategy_keyword_route"
    if _is_operation(message):
        if _is_review_request(message):
            return "meiko", "meiko-검토", "operation_keyword_review"
        return "kasumi", "kasumi-리서치", "operation_keyword_research"
    if _is_marketing(message):
        if _is_review_request(message):
            return "lucy", "lucy-검토", "marketing_keyword_review"
        return "marin", "marin-초안", "marketing_keyword_draft"
    return _route_by_channel(channel_name, message)


def _command_route(channel_name: str, message: str) -> dict[str, Any] | None:
    match = COMMAND_RE.match(message.strip())
    if not match:
        return None
    command = match.group(1).lower()
    rest = (match.group(2) or "").strip()
    if command in AGENT_IDS:
        route = _build_route(command, channel_name, rest, "explicit_command")
        route["command"] = command
        return route
    if command == "agent":
        parts = rest.split(maxsplit=1)
        agent_id = parts[0].lower() if parts else ""
        routed_message = parts[1] if len(parts) > 1 else ""
        route = _build_route(agent_id, channel_name, routed_message, "explicit_command")
        route["command"] = command
        route["explicit_agent_id"] = agent_id
        return route
    if command == "route":
        agent_id, target, reason = _route_by_message(channel_name, rest)
        return _build_route(agent_id or "", channel_name, rest, reason, target_channel=target)
    if command == "handoff":
        parts = rest.split(maxsplit=1)
        target = parts[0] if parts else ""
        routed_message = parts[1] if len(parts) > 1 else ""
        target_agent, target_channel = _handoff_command_target(target)
        route = _build_route(target_agent, channel_name, routed_message, "handoff_command", target_channel=target_channel)
        route["handoff_to"] = target
        route["handoff_channel"] = target_channel
        return route
    if command == "review":
        agent_id, target, reason = _route_by_channel(channel_name, "review " + rest)
        return _build_route(agent_id or "", channel_name, rest, "review_command_" + reason, target_channel=target)
    if command == "approve-draft":
        agent_id, target, reason = _route_by_channel(channel_name, "approval " + rest)
        selected_agent = agent_id or "lucy"
        if selected_agent in {"marin", "kasumi"}:
            selected_agent = "lucy" if selected_agent == "marin" else "meiko"
        return _build_route(selected_agent, channel_name, rest, "approve_draft_command_" + reason, target_channel="최종-승인요청")
    if command in {"agents", "help"}:
        agent_commands = [
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
        return {
            **_base_result(channel_name, rest),
            "command": command,
            "selected_agent": None,
            "target_channel": channel_name,
            "reason": f"{command}_command",
            "help_available": True,
            "agent_commands": agent_commands,
            "agents": ["lucy", "marin", "meiko", "kasumi", "reze"],
            "blocked": False,
        }
    return None


def _base_result(channel_name: str, message: str) -> dict[str, Any]:
    return {
        "report_type": "company_agent_router_dry_run",
        "source_channel": channel_name,
        "message_received": bool(message),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "webhook_url_value_logged": False,
    }


def _build_route(agent_id: str, channel_name: str, message: str, reason: str, target_channel: str | None = None) -> dict[str, Any]:
    agent = get_agent(agent_id)
    policy = get_channel_policy(channel_name)
    external_requested = _contains_any(message, EXTERNAL_ACTION_WORDS)
    if not agent:
        return {
            **_base_result(channel_name, message),
            "selected_agent": None,
            "target_channel": channel_name,
            "blocked": True,
            "blocked_reasons": ["unknown_agent"],
            "external_execution_allowed": False,
            "reason": "unknown_agent",
        }
    if not policy["known_channel"]:
        return {
            **_base_result(channel_name, message),
            "selected_agent": agent_id,
            "agent_display_name": agent["display_name"],
            "target_channel": target_channel or agent["default_channel"],
            "blocked": True,
            "blocked_reasons": ["unknown_channel"],
            "external_execution_allowed": False,
            "reason": "unknown_channel",
        }
    handoff_rule = get_handoff_rule(agent_id) or {}
    return {
        **_base_result(channel_name, message),
        "selected_agent": agent_id,
        "agent_display_name": agent["display_name"],
        "source_channel": channel_name,
        "target_channel": target_channel or agent["default_channel"],
        "handoff_to": handoff_rule.get("to"),
        "handoff_channel": handoff_rule.get("target_channel"),
        "requires_review": bool(agent.get("reviews") or handoff_rule.get("review_required")),
        "requires_approval": external_requested or (target_channel or "") == "최종-승인요청",
        "external_execution_allowed": False,
        "external_execution_requested": external_requested,
        "blocked": external_requested,
        "blocked_reasons": ["external_execution_request_blocked"] if external_requested else [],
        "reason": "external_execution_request_blocked" if external_requested else reason,
    }


def route_company_agent_message(channel_name: str, message: str) -> dict[str, Any]:
    command_route = _command_route(channel_name, message)
    if command_route is not None:
        return command_route
    exact_channel_default = _exact_channel_default(channel_name)
    if exact_channel_default is not None:
        selected_agent, target_channel, reason = exact_channel_default
        return _build_route(selected_agent or "", channel_name, message, reason, target_channel=target_channel)
    selected_agent, target_channel, reason = _route_by_message(channel_name, message)
    return _build_route(selected_agent or "", channel_name, message, reason, target_channel=target_channel)


def build_company_agent_org_report() -> dict[str, Any]:
    registry = load_company_registry()
    return {
        "report_type": "company_agent_org_report",
        "company_agent_layer_v0_available": True,
        "agent_count": len(registry["agents"]),
        "agents": [
            {
                "agent_id": agent["agent_id"],
                "display_name": agent["display_name"],
                "webhook_persona": agent["webhook_persona"],
                "department": agent["department"],
                "seniority": agent["seniority"],
                "handoff_target": agent["handoff_target"],
                "external_execution_allowed": False,
            }
            for agent in registry["agents"].values()
        ],
        "departments": registry["departments"],
        "channel_structure": registry["channel_structure"],
        "handoff_flow": {
            "marin": "lucy",
            "lucy": "final-approval",
            "kasumi": "meiko",
            "meiko": "final-approval",
            "reze": "decision-meeting",
        },
        "permissions": {
            "discord_reply_allowed": True,
            "sns_publish_allowed": False,
            "homepage_deploy_allowed": False,
            "email_send_allowed": False,
            "grant_submit_allowed": False,
            "external_execution_allowed": False,
        },
        "command_syntax": [
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
        ],
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "webhook_url_value_logged": False,
    }
