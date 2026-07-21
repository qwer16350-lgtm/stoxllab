"""Company agent runtime for STOXL Discord Agent OS v0."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from typing import Any

from company_context_store import (
    context_from_replied_message,
    detect_context_reference_terms,
    get_latest_context_by_agent_pair,
    get_latest_context_for_channel,
    get_latest_web_reference_context_for_agent,
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
from company_discord_outbound_guard import (
    classify_discord_send_failure,
    prepare_discord_outbound_messages,
    send_discord_messages_safely,
)
from company_handoff import build_handoff_post_payload, store_company_handoff_context
from company_persistent_memory import build_memory_command_response, load_recent_records
from company_rag_nas_index import build_rag_discord_command_response, parse_rag_discord_command
from company_rag_vector_index import build_rag_vector_discord_command_response
from runtime_dotenv import DISCORD_BOT_TOKEN_ALIASES
from company_webhook_sender import send_as_agent
from company_webhook_sender import send_as_agent_webhook
from company_webhook_sender import resolve_agent_webhook_name
from company_web_reference import (
    build_web_reference_bridge_failure_response,
    build_company_agent_web_reference_one_shot,
    detect_agent_command_web_intent,
    detect_web_reference_intent,
    is_web_reference_enabled,
    resolve_agent_web_scope,
)
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
    "!memory recent",
    "!memory handoffs",
    "!memory approvals",
    "!memory decisions",
    "!recall <keyword>",
    "!rag-status",
    "!rag-search <query>",
    "!docs <query>",
    "!recall-doc <query>",
    "!rag-semantic <query>",
    "!rag-hybrid <query>",
    "!rag-vector-status",
    "!web <query>",
    "!search <query>",
    "!research <query>",
    "!find <query>",
    "!검증 <query>",
]

DEFAULT_AGENT_WEB_BRIDGE_TIMEOUT_SECONDS = 45
AGENT_WEB_BRIDGE_COMMANDS = {"lucy", "marin", "meiko", "kasumi", "reze", "agent"}
KASUMI_ALIASES = {"kasumi", "kasumi_stoxl", "kasumi-stoxl", "카스미", "KASUMI", "Kasumi", "KASUMI_STOXL"}
RECENT_KASUMI_CONTEXT_TERMS = (
    "방금 kasumi가 찾은",
    "방금 kasumi가",
    "kasumi가 찾은",
    "kasumi_stoxl이 찾은",
    "방금 카스미가 찾은",
    "카스미가 찾은",
    "방금 후보",
    "위 후보",
    "이 후보",
    "이 지원사업",
    "위 지원사업",
    "최근 지원사업",
    "방금 리서치",
    "방금 검색한",
)
FRESH_WEB_REFERENCE_TERMS = ("http://", "https://", "다시 확인", "새 검색", "최신 공고", "원문 검증")


@dataclass(frozen=True)
class AgentWebBridgeDecision:
    selected: bool
    selected_agent: str
    agent_scope: str
    source_channel: str
    original_message: str
    query: str
    normalized_command: str
    web_intent_detected: bool
    web_reference_enabled: bool
    web_reference_mode: str
    reason: str = ""

    def to_trace(self) -> dict[str, Any]:
        return {
            "agent_command_detected": self.normalized_command in AGENT_WEB_BRIDGE_COMMANDS,
            "selected_agent": self.selected_agent,
            "agent_web_bridge_selected_agent": self.selected_agent,
            "agent_web_bridge_scope": self.agent_scope,
            "source_channel": self.source_channel,
            "agent_web_bridge_query_present": bool(self.query),
            "web_intent_detected": bool(self.web_intent_detected),
            "web_reference_enabled": bool(self.web_reference_enabled),
            "web_reference_mode": self.web_reference_mode,
            "agent_web_bridge_selected": bool(self.selected),
            "normal_agent_path_skipped_for_web_bridge": bool(self.selected),
            "llm_path_skipped_for_web_bridge": bool(self.selected),
            "command": self.normalized_command,
            "message_preview": self.query[:120],
            "agent_web_bridge_state_lost_after_ack": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }


def normalize_recent_agent_alias(value: Any) -> str:
    normalized = str(value or "").strip()
    folded = normalized.casefold().replace("-", "_")
    if folded in {"kasumi", "kasumi_stoxl"} or normalized == "카스미":
        return "kasumi"
    return folded


def detect_meiko_recent_kasumi_context_intent(channel_name: str, content: str) -> bool:
    route = route_company_agent_message(channel_name, content)
    if str(route.get("selected_agent") or "").strip().lower() != "meiko":
        return False
    command = str(route.get("command") or "").strip().lower()
    if command and command not in {"meiko", "agent"}:
        return False
    command_line = extract_first_command_line(content) or normalize_discord_message_content(content)
    lowered = command_line.casefold()
    if any(term in lowered for term in FRESH_WEB_REFERENCE_TERMS):
        return False
    return any(term.casefold() in lowered for term in RECENT_KASUMI_CONTEXT_TERMS)


def _context_support_text(context: dict[str, Any] | None) -> str:
    if not isinstance(context, dict):
        return ""
    return "\n".join(
        str(context.get(key) or "")
        for key in ("handoff_content", "content", "summary", "title", "status", "type", "item_type")
    )


def _is_kasumi_support_context(context: dict[str, Any] | None) -> bool:
    if not isinstance(context, dict):
        return False
    source = normalize_recent_agent_alias(context.get("source_agent") or context.get("agent"))
    text = _context_support_text(context)
    lowered = text.casefold()
    has_support = (
        "support_program_verification" in lowered
        or "web_reference_support_program_candidates" in lowered
        or "지원사업" in text
        or "후보" in text
    )
    return source == "kasumi" and has_support


def _context_from_recent_memory(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "context_type": "recent_web_reference",
        "source_agent": "kasumi",
        "target_agent": "meiko",
        "source_channel": str(record.get("source_channel") or "persistent_memory"),
        "target_channel": "meiko-검토",
        "status": str(record.get("type") or record.get("item_type") or "web_reference_support_program_candidates"),
        "request_summary": str(record.get("summary") or record.get("title") or "Kasumi support program candidates"),
        "handoff_content": str(record.get("content") or record.get("summary") or record.get("title") or ""),
        "next_action": "Meiko verification",
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def lookup_recent_kasumi_verification_context(channel_name: str) -> dict[str, Any]:
    lookup_steps: list[str] = []
    same_channel = get_latest_context_for_channel(channel_name)
    lookup_steps.append("same_channel_latest_context")
    if _is_kasumi_support_context(same_channel):
        return {
            "recent_context_lookup_succeeded": True,
            "recent_context_lookup_source": "same_channel_latest_context",
            "recent_context_lookup_steps": lookup_steps,
            "context": same_channel,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }

    web_context = get_latest_web_reference_context_for_agent("meiko")
    lookup_steps.append("recent_web_reference_context")
    if _is_kasumi_support_context(web_context):
        return {
            "recent_context_lookup_succeeded": True,
            "recent_context_lookup_source": "recent_web_reference_context",
            "recent_context_lookup_steps": lookup_steps,
            "context": web_context,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }

    lookup_steps.append("persistent_memory_recent_item")
    for record in load_recent_records("recent_item", limit=50):
        context = _context_from_recent_memory(record)
        if _is_kasumi_support_context(context):
            return {
                "recent_context_lookup_succeeded": True,
                "recent_context_lookup_source": "persistent_memory_recent_item",
                "recent_context_lookup_steps": lookup_steps,
                "context": context,
                "raw_discord_ids_logged": False,
                "secret_values_logged": False,
            }

    handoff_context = get_latest_context_by_agent_pair("kasumi", "meiko")
    lookup_steps.append("latest_kasumi_meiko_handoff")
    if _is_kasumi_support_context(handoff_context):
        return {
            "recent_context_lookup_succeeded": True,
            "recent_context_lookup_source": "latest_kasumi_meiko_handoff",
            "recent_context_lookup_steps": lookup_steps,
            "context": handoff_context,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }

    return {
        "recent_context_lookup_succeeded": False,
        "recent_context_lookup_source": "none",
        "recent_context_lookup_steps": lookup_steps,
        "context": None,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def _candidate_titles_from_context_text(text: str, limit: int = 3) -> list[str]:
    titles: list[str] = []
    for line in str(text or "").splitlines():
        stripped = line.strip().lstrip("-").strip()
        lowered = stripped.casefold()
        if "title:" in lowered:
            titles.append(stripped.split(":", 1)[1].strip())
        elif "후보명:" in stripped:
            titles.append(stripped.split(":", 1)[1].strip())
        elif stripped and "지원사업" in stripped and len(stripped) < 140:
            titles.append(stripped)
        if len(titles) >= limit:
            break
    return titles[:limit] or ["최근 Kasumi 지원사업 후보"]


def build_meiko_recent_kasumi_verification_response(context: dict[str, Any]) -> dict[str, Any]:
    text = _context_support_text(context)
    titles = _candidate_titles_from_context_text(text)
    candidate_lines: list[str] = []
    for index, title in enumerate(titles, start=1):
        candidate_lines.extend(
            [
                f"{index}. 후보명: {title}",
                "   판단: 보류",
                "   이유: Kasumi가 찾은 후보는 검토 가능하지만, 마감/자부담/제출서류 원문 재확인이 필요합니다.",
                "   확인 필요: 마감일, 지원대상, 자부담, 제출서류, 신청방법",
                "   실행 조건: STOXL 소재지/업종/중소기업 요건과 준비 일정이 맞을 때만 진행",
                "",
            ]
        )
    content = (
        "[MEIKO_STOXL] 지원사업 검토\n\n"
        "판단 요약:\n"
        "- 추천: 원문 조건과 STOXL 요건이 맞고 준비 일정이 충분한 후보\n"
        "- 보류: 마감/자부담/제출서류가 아직 확정되지 않은 후보\n"
        "- 비추천: 소재지, 업종, 기업요건, 제출 일정이 맞지 않는 후보\n\n"
        "후보별 판단:\n"
        f"{''.join(candidate_lines).strip()}\n\n"
        "최우선 액션:\n"
        "- 원문 마감/자부담/제출서류 재확인\n"
        "- STOXL 소재지/업종/중소기업 요건 확인\n"
        "- 준비 가능한 후보부터 서류 검토"
    )
    return {
        "response_type": "company_agent_response",
        "reply_text_source": "recent_kasumi_verification_context",
        "agent_id": "meiko",
        "content": content,
        "handoff_context_used": True,
        "handoff_context_source_agent": "kasumi",
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_meiko_recent_kasumi_context_not_found_response() -> dict[str, Any]:
    return {
        "response_type": "company_agent_response",
        "reply_text_source": "recent_kasumi_verification_context_not_found",
        "agent_id": "meiko",
        "content": (
            "[MEIKO_STOXL]\n"
            "방금 Kasumi가 찾은 지원사업 context를 찾지 못했습니다.\n"
            "먼저 Kasumi에게 지원사업 후보 검색을 실행한 뒤 다시 요청해 주세요.\n\n"
            "예:\n"
            "!kasumi 이번 달 한국 중소기업 디자인 개발 지원사업 후보 찾아줘"
        ),
        "web_reference_failure_reason": "recent_kasumi_verification_context_not_found",
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


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
    discord_token = next((str(env_map.get(key) or "") for key in DISCORD_BOT_TOKEN_ALIASES if env_map.get(key)), "")
    return {
        "discord_token_present": bool(discord_token),
        "_discord_token": discord_token,
        "llm_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_LLM_ENABLED", "false")),
        "reply_mode": str(env_map.get("HERMES_COMPANY_AGENT_REPLY_MODE", "deterministic_fallback") or "deterministic_fallback"),
        "handoff_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_HANDOFF_ENABLED", "false")),
        "webhook_persona_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED", "false")),
        "webhook_create_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_WEBHOOK_CREATE_ENABLED", "true"), default=True),
        "real_bots_enabled": _flag(env_map.get("HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED", "false")),
        "sender_mode": str(env_map.get("HERMES_COMPANY_AGENT_SENDER_MODE", "bot_fallback") or "bot_fallback").strip().lower(),
        "web_reference_enabled": is_web_reference_enabled(env_map),
        "web_reference_mode": str(env_map.get("HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE", "off") or "off").strip().lower(),
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


def _outbound_guard_preview(content: str, agent_id: str = "") -> dict[str, Any]:
    prepared = prepare_discord_outbound_messages(content, agent_id or "hermes")
    return {
        "outbound_guard_applied": True,
        "outbound_original_length": prepared.get("outbound_original_length", 0),
        "outbound_chunking_used": bool(prepared.get("outbound_chunking_used")),
        "outbound_chunk_count": int(prepared.get("outbound_chunk_count") or 0),
        "outbound_truncated_for_discord": bool(prepared.get("outbound_truncated_for_discord")),
        "outbound_compacted_for_discord": bool(prepared.get("outbound_compacted_for_discord")),
        "outbound_full_content_preserved_in_memory": bool(prepared.get("outbound_full_content_preserved_in_memory")),
    }


def _extract_agent_web_bridge_query(content: str, route: dict[str, Any]) -> str:
    command_line = extract_first_command_line(content) or normalize_discord_message_content(content)
    command = str(route.get("command") or "").strip().lower()
    selected_agent = str(route.get("selected_agent") or "").strip().lower()
    if command == "agent":
        parts = command_line.split(maxsplit=2)
        return parts[2].strip() if len(parts) >= 3 else ""
    if command in {"lucy", "marin", "meiko", "kasumi", "reze"}:
        prefix = f"!{command}"
        if command_line.lower().startswith(prefix):
            return command_line[len(prefix) :].strip()
    return str(route.get("command_argument") or command_line).strip()


def _parse_rag_vector_discord_command(content: str) -> dict[str, Any]:
    lines = [line.strip() for line in str(content or "").replace("\r\n", "\n").split("\n")]
    for line in lines:
        if not line.startswith("!"):
            continue
        parts = line.split(maxsplit=1)
        command = parts[0].lstrip("!").strip().lower()
        if command not in {"rag-semantic", "rag-hybrid", "rag-vector-status"}:
            continue
        return {
            "rag_runtime_command": True,
            "command": command,
            "query": parts[1].strip() if len(parts) > 1 else "",
        }
    return {"rag_runtime_command": False, "command": "", "query": ""}


def detect_agent_web_bridge_decision(channel_name: str, content: str, env: dict[str, Any] | None = None) -> AgentWebBridgeDecision:
    if detect_meiko_recent_kasumi_context_intent(channel_name, content):
        return AgentWebBridgeDecision(
            selected=False,
            selected_agent="meiko",
            agent_scope=resolve_agent_web_scope("meiko"),
            source_channel=channel_name,
            original_message=str(content or ""),
            query=_extract_agent_web_bridge_query(str(content or ""), route_company_agent_message(channel_name, content)),
            normalized_command="meiko",
            web_intent_detected=False,
            web_reference_enabled=is_web_reference_enabled(dict(os.environ if env is None else env)),
            web_reference_mode=str((dict(os.environ if env is None else env)).get("HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE", "off") or "off").strip().lower(),
            reason="recent_kasumi_context_priority",
        )
    route = route_company_agent_message(channel_name, content)
    selected_agent = str(route.get("selected_agent") or "")
    routed_content = extract_first_command_line(content) or normalize_discord_message_content(content)
    env_map = dict(os.environ if env is None else env)
    command = str(route.get("command") or "").strip().lower()
    agent_command_detected = command in AGENT_WEB_BRIDGE_COMMANDS
    web_intent = detect_agent_command_web_intent(selected_agent, routed_content, route)
    enabled = is_web_reference_enabled(env_map)
    selected = bool(agent_command_detected and web_intent and enabled and selected_agent)
    return AgentWebBridgeDecision(
        selected=selected,
        selected_agent=selected_agent,
        agent_scope=resolve_agent_web_scope(selected_agent) if selected_agent else "",
        source_channel=channel_name,
        original_message=str(content or ""),
        query=_extract_agent_web_bridge_query(str(content or ""), route),
        normalized_command=command,
        web_intent_detected=bool(web_intent),
        web_reference_enabled=bool(enabled),
        web_reference_mode=str(env_map.get("HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE", "off") or "off").strip().lower(),
        reason="" if selected else "agent_web_bridge_not_selected",
    )


def build_agent_web_bridge_decision_trace(channel_name: str, content: str, env: dict[str, Any] | None = None) -> dict[str, Any]:
    return detect_agent_web_bridge_decision(channel_name, content, env).to_trace()


def build_agent_web_bridge_ack_text(agent_id: str) -> str:
    label = str(agent_id or "hermes").upper()
    return (
        f"[{label}_STOXL]\n"
        "웹 참조 작업을 시작했습니다.\n"
        "공식 출처 우선으로 후보를 확인 중입니다."
    )


def _agent_web_bridge_timeout_seconds(env: dict[str, Any] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    raw = env_map.get("HERMES_COMPANY_AGENT_WEB_BRIDGE_TIMEOUT_SECONDS", DEFAULT_AGENT_WEB_BRIDGE_TIMEOUT_SECONDS)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_AGENT_WEB_BRIDGE_TIMEOUT_SECONDS
    return min(max(value, 1), 60)


def build_agent_web_reference_timeout_response(agent_id: str) -> dict[str, Any]:
    label = str(agent_id or "hermes").upper()
    return {
        "report_type": "company_agent_web_reference_bridge_timeout",
        "response_type": "company_agent_response",
        "agent_id": agent_id,
        "reply_text_source": "web_reference_timeout",
        "content": (
            f"[{label}_STOXL]\n"
            "웹 참조 작업이 시간 초과되었습니다.\n"
            "일부 검색/원문 확인이 오래 걸려 완료하지 못했습니다.\n"
            "검색어를 줄이거나 `!web <검색어>`로 다시 시도해 주세요."
        ),
        "web_reference_bridge_failed": True,
        "web_reference_failure_reason": "web_reference_timeout",
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_agent_web_bridge_state_lost_response(agent_id: str) -> dict[str, Any]:
    label = str(agent_id or "hermes").upper()
    return {
        "report_type": "company_agent_web_reference_bridge_state_lost",
        "response_type": "company_agent_response",
        "agent_id": agent_id,
        "reply_text_source": "agent_web_bridge_state_lost_after_ack",
        "content": (
            f"[{label}_STOXL]\n"
            "웹 참조 작업 상태가 ACK 이후 유실되어 완료하지 못했습니다.\n"
            "reason: agent_web_bridge_state_lost_after_ack"
        ),
        "web_reference_bridge_failed": True,
        "web_reference_failure_reason": "agent_web_bridge_state_lost_after_ack",
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_agent_web_reference_failure_result(channel_name: str, content: str, reason: str) -> dict[str, Any]:
    route = route_company_agent_message(channel_name, content)
    selected_agent = str(route.get("selected_agent") or "hermes")
    response = (
        build_agent_web_reference_timeout_response(selected_agent)
        if reason == "web_reference_timeout"
        else build_web_reference_bridge_failure_response(selected_agent, reason)
    )
    return {
        **route,
        "reply_prepared": True,
        "response": response,
        **_outbound_guard_preview(str(response.get("content") or ""), selected_agent),
        "webhook_send_available": False,
        "bot_message_fallback_used": True,
        "send_strategy": "bot_message_fallback",
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "web_reference_attempted": True,
        "web_reference_succeeded": False,
        "web_reference_failure_reason": reason,
        "agent_scope": "",
        "web_reference_intent_detected": True,
        "agent_command_detected": True,
        "web_reference_enabled": True,
        "agent_web_bridge_selected": True,
        "normal_agent_path_skipped_for_web_bridge": True,
        "llm_path_skipped_for_web_bridge": True,
        "agent_command_web_bridge": True,
        "web_reference_bridge_attempted": True,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_agent_web_reference_failure_result_from_decision(decision: AgentWebBridgeDecision, reason: str) -> dict[str, Any]:
    if reason == "web_reference_timeout":
        response = build_agent_web_reference_timeout_response(decision.selected_agent)
    elif reason == "agent_web_bridge_state_lost_after_ack":
        response = build_agent_web_bridge_state_lost_response(decision.selected_agent)
    else:
        response = build_web_reference_bridge_failure_response(decision.selected_agent, reason)
    return {
        "report_type": "company_agent_web_bridge_completion",
        "source_channel": decision.source_channel,
        "selected_agent": decision.selected_agent,
        "agent_scope": decision.agent_scope,
        "agent_web_bridge_scope": decision.agent_scope,
        "reply_prepared": True,
        "response": response,
        **_outbound_guard_preview(str(response.get("content") or ""), decision.selected_agent),
        "webhook_send_available": False,
        "bot_message_fallback_used": True,
        "send_strategy": "bot_message_fallback",
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "web_reference_attempted": True,
        "web_reference_succeeded": False,
        "web_reference_failure_reason": reason,
        "web_reference_intent_detected": True,
        "agent_command_detected": True,
        "web_reference_enabled": decision.web_reference_enabled,
        "web_reference_mode": decision.web_reference_mode,
        "agent_web_bridge_selected": True,
        "agent_web_bridge_selected_agent": decision.selected_agent,
        "agent_web_bridge_query_present": bool(decision.query),
        "agent_web_bridge_state_lost_after_ack": reason == "agent_web_bridge_state_lost_after_ack",
        "normal_agent_path_skipped_for_web_bridge": True,
        "llm_path_skipped_for_web_bridge": True,
        "agent_command_web_bridge": True,
        "web_reference_bridge_attempted": True,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_agent_web_bridge_execution_result_from_decision(
    decision: AgentWebBridgeDecision,
    *,
    env: dict[str, Any] | None = None,
    web_search_runner: Any | None = None,
) -> dict[str, Any]:
    env_map = dict(os.environ if env is None else env)
    route = route_company_agent_message(decision.source_channel, decision.original_message)
    route["selected_agent"] = decision.selected_agent
    route["agent_scope"] = decision.agent_scope
    route["agent_web_bridge_selected"] = True
    route["agent_web_bridge_selected_agent"] = decision.selected_agent
    route["agent_web_bridge_scope"] = decision.agent_scope
    route["agent_web_bridge_query_present"] = bool(decision.query)
    route["web_reference_bridge_attempted"] = True
    try:
        web_reference = build_company_agent_web_reference_one_shot(
            decision.selected_agent,
            decision.query,
            allow_web_reference=True,
            env=env_map,
            search_runner=web_search_runner,
            context=route,
        )
    except Exception:
        return build_agent_web_reference_failure_result_from_decision(decision, "web_reference_runtime_exception")
    if web_reference.get("web_search_succeeded"):
        response = {
            "response_type": "company_agent_response",
            "agent_id": decision.selected_agent,
            "reply_text_source": "web_reference",
            "content": str(web_reference.get("reference_report") or web_reference.get("web_reference_results_block") or ""),
            "llm_api_call_attempted": False,
            "llm_api_called": False,
            "rag_called": False,
            "embedding_api_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    else:
        response = build_web_reference_bridge_failure_response(
            decision.selected_agent,
            str(web_reference.get("failure_reason") or "web_reference_runtime_exception"),
        )
    return {
        **route,
        "report_type": "company_agent_web_bridge_completion",
        "reply_prepared": True,
        "response": response,
        **_outbound_guard_preview(str(response.get("content") or ""), decision.selected_agent),
        "webhook_send_available": False,
        "bot_message_fallback_used": True,
        "send_strategy": "bot_message_fallback",
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "web_reference_attempted": bool(web_reference.get("web_search_attempted")),
        "web_reference_succeeded": bool(web_reference.get("web_search_succeeded")),
        "web_reference_failure_reason": web_reference.get("failure_reason") or "",
        "agent_scope": web_reference.get("agent_scope") or decision.agent_scope,
        "agent_web_bridge_scope": web_reference.get("agent_scope") or decision.agent_scope,
        "web_reference_intent_detected": True,
        "agent_command_detected": True,
        "web_reference_enabled": decision.web_reference_enabled,
        "web_reference_mode": decision.web_reference_mode,
        "agent_web_bridge_selected": True,
        "agent_web_bridge_selected_agent": decision.selected_agent,
        "agent_web_bridge_query_present": bool(decision.query),
        "agent_web_bridge_state_lost_after_ack": False,
        "normal_agent_path_skipped_for_web_bridge": True,
        "llm_path_skipped_for_web_bridge": True,
        "agent_command_web_bridge": True,
        "web_reference_bridge_attempted": True,
        "webhook_url_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


async def _maybe_send_agent_web_bridge_ack(message: Any, client: Any | None = None) -> dict[str, Any]:
    channel_name = str(getattr(getattr(message, "channel", None), "name", "") or "")
    content = str(getattr(message, "content", "") or "")
    decision = detect_agent_web_bridge_decision(channel_name, content)
    trace = decision.to_trace()
    if not decision.selected:
        return {**trace, "ack_attempted": False, "ack_sent": False, "ack_failure_reason": ""}
    ack_text = build_agent_web_bridge_ack_text(decision.selected_agent)
    try:
        if client is not None and decision.selected_agent:
            send_result = await _send_agent_content(client, decision.selected_agent, message.channel, ack_text)
        else:
            prepared = prepare_discord_outbound_messages(ack_text, decision.selected_agent or "hermes")
            send_result = await send_discord_messages_safely(
                message.channel.send,
                list(prepared.get("messages") or []),
                fallback_send_one=message.channel.send,
            )
    except Exception:
        return {
            **trace,
            "agent_web_bridge_decision": decision,
            "agent_web_bridge_decision_snapshot": asdict(decision),
            "agent_web_bridge_decision_preserved_after_ack": True,
            "ack_attempted": True,
            "ack_sent": False,
            "ack_failure_reason": "web_reference_send_failed",
        }
    return {
        **trace,
        "agent_web_bridge_decision": decision,
        "agent_web_bridge_decision_snapshot": asdict(decision),
        "agent_web_bridge_decision_preserved_after_ack": True,
        "ack_attempted": True,
        "ack_sent": bool(send_result.get("sent") or send_result.get("discord_message_sent")),
        "ack_failure_reason": send_result.get("discord_send_failure_reason") or "",
        "outbound_guard_applied": True,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


async def _build_company_agent_message_result_with_timeout(
    channel_name: str,
    content: str,
    replied_content: str,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    return await asyncio.wait_for(
        asyncio.to_thread(
            build_company_agent_message_result,
            channel_name,
            content,
            replied_content,
        ),
        timeout=timeout_seconds,
    )


async def _build_agent_web_bridge_execution_result_with_timeout(
    decision: AgentWebBridgeDecision,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    return await asyncio.wait_for(
        asyncio.to_thread(
            build_agent_web_bridge_execution_result_from_decision,
            decision,
        ),
        timeout=timeout_seconds,
    )


async def _complete_agent_web_bridge_after_ack(
    message: Any,
    ack_result: dict[str, Any],
    *,
    replied_content: str = "",
    client: Any | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    decision = ack_result.get("agent_web_bridge_decision")
    if not isinstance(decision, AgentWebBridgeDecision):
        snapshot = ack_result.get("agent_web_bridge_decision_snapshot")
        if isinstance(snapshot, dict):
            try:
                decision = AgentWebBridgeDecision(**snapshot)
            except TypeError:
                decision = None
    if not ack_result.get("agent_web_bridge_selected") or not isinstance(decision, AgentWebBridgeDecision):
        return {
            **ack_result,
            "agent_web_reference_execution_started": False,
            "agent_web_reference_final_reply_prepared": False,
            "agent_web_reference_final_reply_sent": False,
            "agent_web_reference_failure_fallback_sent": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    channel_name = str(getattr(getattr(message, "channel", None), "name", "") or "")
    content = str(getattr(message, "content", "") or "")
    selected_agent = decision.selected_agent or str(ack_result.get("selected_agent") or "hermes")
    timeout = timeout_seconds if timeout_seconds is not None else _agent_web_bridge_timeout_seconds()
    execution_completed = False
    execution_failed = False
    failure_reason = ""
    state_lost_after_ack = bool(ack_result.get("ack_sent") and not decision.selected)
    if state_lost_after_ack:
        execution_failed = True
        failure_reason = "agent_web_bridge_state_lost_after_ack"
        result = build_agent_web_reference_failure_result_from_decision(decision, failure_reason)
        response = result.get("response", {}) if isinstance(result.get("response"), dict) else {}
        final_prepared = bool(str(response.get("content") or "").strip())
    else:
        result = {}
        response = {}
        final_prepared = False
    try:
        if not state_lost_after_ack:
            result = await _build_agent_web_bridge_execution_result_with_timeout(
                decision,
                timeout_seconds=timeout,
            )
            execution_completed = True
    except asyncio.TimeoutError:
        execution_failed = True
        failure_reason = "web_reference_timeout"
        result = build_agent_web_reference_failure_result_from_decision(decision, failure_reason)
    except Exception:
        execution_failed = True
        failure_reason = "web_reference_runtime_exception"
        result = build_agent_web_reference_failure_result_from_decision(decision, failure_reason)

    response = result.get("response", {}) if isinstance(result.get("response"), dict) else response
    final_prepared = final_prepared or bool(result.get("reply_prepared") and str(response.get("content") or "").strip())
    if not final_prepared:
        execution_failed = True
        failure_reason = failure_reason or ("agent_web_bridge_state_lost_after_ack" if ack_result.get("ack_sent") else "agent_web_bridge_not_reached")
        result = build_agent_web_reference_failure_result_from_decision(decision, failure_reason)
        response = result.get("response", {}) if isinstance(result.get("response"), dict) else {}
        final_prepared = bool(str(response.get("content") or "").strip())

    try:
        send_result = await _send_runtime_reply(message, result, client=client)
    except Exception:
        failure_reason = "web_reference_send_failed"
        fallback_result = build_agent_web_reference_failure_result_from_decision(decision, failure_reason)
        try:
            send_result = await _send_runtime_reply(message, fallback_result, client=client)
            result = fallback_result
            response = result.get("response", {}) if isinstance(result.get("response"), dict) else {}
        except Exception:
            send_result = {
                "sent": False,
                "discord_message_sent": False,
                "message_sent_count": 0,
                "discord_send_failure_reason": failure_reason,
                "fallback_short_notice_attempted": False,
                "fallback_short_notice_sent": False,
            }

    final_sent = bool(send_result.get("sent") or send_result.get("discord_message_sent"))
    fallback_sent = str(response.get("reply_text_source") or "").startswith("web_reference_") and not result.get("web_reference_succeeded", False)
    return {
        **ack_result,
        "agent_web_bridge_ack_sent": bool(ack_result.get("ack_sent")),
        "agent_web_bridge_decision_preserved_after_ack": isinstance(decision, AgentWebBridgeDecision),
        "agent_web_bridge_selected_agent": decision.selected_agent,
        "agent_web_bridge_scope": decision.agent_scope,
        "agent_web_bridge_query_present": bool(decision.query),
        "agent_web_bridge_state_lost_after_ack": bool(state_lost_after_ack or failure_reason == "agent_web_bridge_state_lost_after_ack"),
        "agent_web_reference_execution_started": True,
        "agent_web_reference_execution_completed": bool(execution_completed),
        "agent_web_reference_execution_failed": bool(execution_failed or not result.get("web_reference_succeeded", False)),
        "agent_web_reference_final_reply_prepared": bool(final_prepared),
        "agent_web_reference_final_reply_sent": final_sent,
        "agent_web_reference_final_reply_failure_reason": send_result.get("discord_send_failure_reason") or failure_reason,
        "agent_web_reference_failure_fallback_sent": bool(fallback_sent and final_sent),
        "agent_web_reference_failure_reason": result.get("web_reference_failure_reason") or failure_reason,
        "selected_agent": selected_agent,
        "outbound_guard_applied": True,
        "fallback_short_notice_attempted": bool(send_result.get("fallback_short_notice_attempted")),
        "fallback_short_notice_sent": bool(send_result.get("fallback_short_notice_sent")),
        "message_sent_count": int(send_result.get("message_sent_count") or 0),
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


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
                "discord_token_present": bool(runtime_env["discord_token_present"]),
                "token_value_logged": False,
                "command_syntax": list(COMMAND_SYNTAX),
                "external_execution": False,
                "handoff_posting_enabled": bool(runtime_env["handoff_enabled"]),
                "webhook_persona_enabled": bool(runtime_env["webhook_persona_enabled"]),
                "webhook_create_enabled": bool(runtime_env["webhook_create_enabled"]),
                "real_bots_enabled": bool(runtime_env["real_bots_enabled"]),
                "sender_mode": runtime_env["sender_mode"],
                "web_reference_enabled": bool(runtime_env["web_reference_enabled"]),
                "web_reference_mode": runtime_env["web_reference_mode"],
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
        "web_reference_enabled": bool(runtime_env["web_reference_enabled"]),
        "web_reference_mode": runtime_env["web_reference_mode"],
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
    web_search_runner: Any | None = None,
) -> dict[str, Any]:
    rag_vector_command = _parse_rag_vector_discord_command(content)
    if rag_vector_command.get("rag_runtime_command"):
        env_map = dict(os.environ if env is None else env)
        command_response = build_rag_vector_discord_command_response(
            str(rag_vector_command.get("command") or ""),
            str(rag_vector_command.get("query") or ""),
            env=env_map,
        )
        return {
            "report_type": "company_agent_rag_discord_command",
            "source_channel": channel_name,
            "selected_agent": "hermes",
            "agent_display_name": "HERMES_STOXL",
            "reason": "rag_runtime_command",
            "command": rag_vector_command.get("command"),
            "query_present": bool(str(rag_vector_command.get("query") or "").strip()),
            "reply_prepared": True,
            "response": command_response,
            **_outbound_guard_preview(str(command_response.get("content") or ""), "hermes"),
            "webhook_send_available": False,
            "bot_message_fallback_used": True,
            "send_strategy": "bot_message_fallback",
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
            "rag_runtime_command": True,
            "rag_mode": command_response.get("mode") or "hybrid",
            "nas_write_attempted": False,
            "nas_file_modified": False,
            "nas_file_deleted": False,
            "index_write_attempted_from_runtime": False,
            "embedding_called": False,
            "external_embedding_api_called": False,
            "vector_index_created": False,
            "llm_called": False,
            "llm_api_called": False,
            "web_search_called": False,
            "vision_api_called": False,
            "ocr_called": False,
            "external_execution": False,
            "raw_nas_absolute_path_logged": False,
            "raw_index_absolute_path_logged": False,
            "raw_vector_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
            "webhook_url_value_logged": False,
        }
    rag_command = parse_rag_discord_command(content)
    if rag_command.get("rag_runtime_command"):
        env_map = dict(os.environ if env is None else env)
        rag_command_name = str(rag_command.get("command") or "")
        if rag_command_name == "rag-status":
            command_response = build_rag_vector_discord_command_response("rag-vector-status", "", env=env_map)
            command_response["command"] = "rag-status"
        elif rag_command_name in {"docs", "recall-doc"}:
            command_response = build_rag_vector_discord_command_response("rag-hybrid", str(rag_command.get("query") or ""), env=env_map)
            command_response["command"] = rag_command_name
        else:
            command_response = build_rag_discord_command_response(
                rag_command_name,
                str(rag_command.get("query") or ""),
                env=env_map,
            )
        return {
            "report_type": "company_agent_rag_discord_command",
            "source_channel": channel_name,
            "selected_agent": "hermes",
            "agent_display_name": "HERMES_STOXL",
            "reason": "rag_runtime_command",
            "command": rag_command.get("command"),
            "query_present": bool(str(rag_command.get("query") or "").strip()),
            "reply_prepared": True,
            "response": command_response,
            **_outbound_guard_preview(str(command_response.get("content") or ""), "hermes"),
            "webhook_send_available": False,
            "bot_message_fallback_used": True,
            "send_strategy": "bot_message_fallback",
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
            "rag_runtime_command": True,
            "rag_mode": "keyword_only",
            "nas_write_attempted": False,
            "nas_file_modified": False,
            "nas_file_deleted": False,
            "index_write_attempted_from_runtime": False,
            "rag_called": False,
            "embedding_called": False,
            "vector_index_created": False,
            "llm_called": False,
            "llm_api_called": False,
            "web_search_called": False,
            "vision_api_called": False,
            "ocr_called": False,
            "external_execution": False,
            "raw_nas_absolute_path_logged": False,
            "raw_index_absolute_path_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
            "webhook_url_value_logged": False,
        }
    route = route_company_agent_message(channel_name, content)
    if route.get("blocked"):
        return {
            **route,
            "reply_prepared": False,
            "send_strategy": "blocked",
            "bot_message_fallback_used": False,
        }
    command = route.get("command")
    if command in {"agents", "help", "memory", "recall"}:
        if command in {"memory", "recall"}:
            command_response = build_memory_command_response(command, str(route.get("command_argument") or ""))
        else:
            command_response = {
                "response_type": "company_agent_command_response",
                "reply_text_source": command,
                "content": _command_response_text(command),
                "llm_api_call_attempted": False,
                "rag_called": False,
                "external_execution": False,
            }
        return {
            **route,
            "reply_prepared": True,
            "response": command_response,
            **_outbound_guard_preview(str(command_response.get("content") or ""), str(route.get("selected_agent") or "hermes")),
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
    recent_context_intent = detect_meiko_recent_kasumi_context_intent(channel_name, content)
    if recent_context_intent:
        lookup = lookup_recent_kasumi_verification_context(channel_name)
        context = lookup.get("context") if isinstance(lookup.get("context"), dict) else None
        response = (
            build_meiko_recent_kasumi_verification_response(context)
            if context and lookup.get("recent_context_lookup_succeeded")
            else build_meiko_recent_kasumi_context_not_found_response()
        )
        return {
            **route,
            "reply_prepared": True,
            "response": response,
            **_outbound_guard_preview(str(response.get("content") or ""), "meiko"),
            "webhook_send_available": False,
            "bot_message_fallback_used": True,
            "send_strategy": "bot_message_fallback",
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
            "recent_context_intent_detected": True,
            "recent_source_agent": "kasumi",
            "recent_context_lookup_attempted": True,
            "recent_context_lookup_succeeded": bool(lookup.get("recent_context_lookup_succeeded")),
            "recent_context_lookup_source": lookup.get("recent_context_lookup_source") or "none",
            "web_bridge_skipped_for_recent_context": True,
            "policy_gate_skipped_for_recent_context": True,
            "blocked_by_policy": False,
            "web_reference_attempted": False,
            "web_reference_succeeded": False,
            "web_reference_bridge_attempted": False,
            "agent_command_web_bridge": False,
            "tavily_called": False,
            "llm_api_called": False,
            "rag_called": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "handoff_context_used": bool(context),
            "handoff_context_priority": "persistent_memory"
            if lookup.get("recent_context_lookup_source") in {"recent_web_reference_context", "persistent_memory_recent_item"}
            else lookup.get("recent_context_lookup_source") or "none",
            "handoff_context_source_agent": "kasumi" if context else "",
            "webhook_url_value_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    replied_context = context_from_replied_message(replied_message_content, channel_name, selected_agent)
    context_resolution = resolve_handoff_context(selected_agent, routed_content, channel_name, replied_context)
    route["context_reference_detected"] = bool(context_resolution["context_reference_detected"])
    route["handoff_context_used"] = bool(context_resolution["context_used"])
    route["handoff_context_priority"] = context_resolution["context_priority"]
    route["handoff_context_source_agent"] = context_resolution["context_source_agent"]
    if context_resolution.get("context_used"):
        route["handoff_context"] = context_resolution["context"]
    env_map = dict(os.environ if env is None else env)
    web_reference: dict[str, Any] = {}
    web_intent_detected = detect_web_reference_intent(selected_agent, routed_content, route)
    agent_command_web_bridge = detect_agent_command_web_intent(selected_agent, routed_content, route)
    web_reference_bridge_attempted = False
    web_reference_enabled = is_web_reference_enabled(env_map)
    web_reference_mode = str(env_map.get("HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE", "off") or "off").strip().lower()
    agent_command_detected = str(route.get("command") or "").strip().lower() in {"lucy", "marin", "meiko", "kasumi", "reze", "agent"}
    if selected_agent in {"lucy", "marin", "meiko", "kasumi", "reze"} and web_reference_enabled and (web_intent_detected or agent_command_web_bridge):
        web_reference_bridge_attempted = True
        try:
            web_reference = build_company_agent_web_reference_one_shot(
                selected_agent,
                routed_content,
                allow_web_reference=True,
                env=env_map,
                search_runner=web_search_runner,
                context=route,
            )
        except Exception:
            web_reference = {
                "web_search_attempted": True,
                "web_search_succeeded": False,
                "failure_reason": "web_reference_runtime_exception",
                "discord_api_send_called": False,
                "discord_message_sent": False,
                "llm_api_called": False,
                "rag_called": False,
                "embedding_called": False,
                "vector_index_created": False,
                "external_execution": False,
                "api_key_value_logged": False,
                "raw_discord_ids_logged": False,
                "secret_values_logged": False,
            }
        route["web_reference_report"] = web_reference
        route["web_reference_results_block"] = web_reference.get("web_reference_results_block", "")
        route["agent_command_web_bridge"] = bool(agent_command_web_bridge)
        route["web_reference_bridge_attempted"] = True
    if web_reference_bridge_attempted and web_reference and web_reference.get("web_search_succeeded"):
        response = {
            "response_type": "company_agent_response",
            "agent_id": selected_agent,
            "reply_text_source": "web_reference",
            "content": str(web_reference.get("reference_report") or web_reference.get("web_reference_results_block") or ""),
            "llm_api_call_attempted": False,
            "llm_api_called": False,
            "rag_called": False,
            "embedding_api_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    elif web_reference_bridge_attempted and web_reference and not web_reference.get("web_search_succeeded"):
        response = build_web_reference_bridge_failure_response(selected_agent, str(web_reference.get("failure_reason") or "web_reference_runtime_exception"))
    else:
        response = build_company_agent_response(selected_agent, routed_content, route, env_map)
    webhook_result = send_as_agent(selected_agent, channel_name, str(response.get("content", "")))
    bot_fallback = webhook_result.get("blocked") is True
    return {
        **route,
        "reply_prepared": True,
        "response": response,
        **_outbound_guard_preview(str(response.get("content") or ""), selected_agent),
        "webhook_send_available": not bot_fallback,
        "bot_message_fallback_used": bot_fallback,
        "send_strategy": "bot_message_fallback" if bot_fallback else "webhook_persona",
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "web_reference_attempted": bool(web_reference.get("web_search_attempted")),
        "web_reference_succeeded": bool(web_reference.get("web_search_succeeded")),
        "web_reference_failure_reason": web_reference.get("failure_reason") or "",
        "agent_scope": web_reference.get("agent_scope") or "",
        "web_reference_intent_detected": bool(web_intent_detected or agent_command_web_bridge),
        "agent_command_detected": bool(agent_command_detected),
        "web_reference_enabled": bool(web_reference_enabled),
        "web_reference_mode": web_reference_mode,
        "agent_web_bridge_selected": bool(agent_command_web_bridge and web_reference_bridge_attempted),
        "normal_agent_path_skipped_for_web_bridge": bool(agent_command_web_bridge and web_reference_bridge_attempted),
        "llm_path_skipped_for_web_bridge": bool(agent_command_web_bridge and web_reference_bridge_attempted),
        "agent_command_web_bridge": bool(agent_command_web_bridge),
        "web_reference_bridge_attempted": bool(web_reference_bridge_attempted),
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
        "!handoff, !review, !approve-draft, !agents, !help, !memory recent, "
        "!memory handoffs, !memory approvals, !memory decisions, !recall <keyword>, "
        "!web, !search, !research, !find, !검증"
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
    prepared = prepare_discord_outbound_messages(content, agent_id)
    messages = list(prepared.get("messages") or [])
    if not messages:
        return {**prepared, "sent": False, "send_strategy": "empty_content"}
    order = sender_order_for_mode(
        env["sender_mode"],
        real_bots_enabled=bool(env["real_bots_enabled"]),
        webhook_enabled=bool(env["webhook_persona_enabled"]),
    )
    attempts: list[str] = []
    last_failure_reason = ""
    for sender in order:
        attempts.append(sender)
        if sender == "real_bot":
            fleet = getattr(client, "_agent_bot_fleet", None)
            sent_count = 0
            blocked_result: dict[str, Any] = {}
            for chunk in messages:
                real_result = await send_as_real_agent_bot(fleet, agent_id, channel_name, chunk)
                if real_result.get("blocked"):
                    blocked_result = real_result
                    break
                sent_count += int(real_result.get("message_sent_count") or 1)
            if sent_count == len(messages):
                return {
                    **prepared,
                    **real_result,
                    "send_strategy": "real_bot",
                    "sender_attempt_order": attempts,
                    "message_sent_count": sent_count,
                }
            last_failure_reason = classify_discord_send_failure(",".join(blocked_result.get("blocked_reasons", [])))
            if sent_count > 0:
                return {
                    **prepared,
                    "sent": True,
                    "send_strategy": "real_bot",
                    "sender_attempt_order": attempts,
                    "discord_send_attempted": True,
                    "discord_message_sent": True,
                    "message_sent_count": sent_count,
                    "discord_send_failure_reason": last_failure_reason,
                    "fallback_short_notice_attempted": False,
                    "fallback_short_notice_sent": False,
                    "webhook_url_value_logged": False,
                    "raw_discord_ids_logged": False,
                    "secret_values_logged": False,
                }
        elif sender == "webhook":
            sent_count = 0
            blocked_result = {}
            for chunk in messages:
                webhook_result = await send_as_agent_webhook(
                    agent_id,
                    channel,
                    chunk,
                    create_enabled=bool(env["webhook_create_enabled"]),
                )
                if webhook_result.get("blocked"):
                    blocked_result = webhook_result
                    break
                sent_count += int(webhook_result.get("message_sent_count") or 1)
            if sent_count == len(messages):
                return {
                    **prepared,
                    **webhook_result,
                    "send_strategy": "webhook",
                    "sender_attempt_order": attempts,
                    "message_sent_count": sent_count,
                }
            last_failure_reason = classify_discord_send_failure(",".join(blocked_result.get("blocked_reasons", [])))
            if sent_count > 0:
                return {
                    **prepared,
                    "sent": True,
                    "send_strategy": "webhook",
                    "sender_attempt_order": attempts,
                    "discord_send_attempted": True,
                    "discord_message_sent": True,
                    "message_sent_count": sent_count,
                    "discord_send_failure_reason": last_failure_reason,
                    "fallback_short_notice_attempted": False,
                    "fallback_short_notice_sent": False,
                    "webhook_url_value_logged": False,
                    "raw_discord_ids_logged": False,
                    "secret_values_logged": False,
                }
        elif sender == "bot_fallback":
            send_result = await send_discord_messages_safely(channel.send, messages, fallback_send_one=channel.send)
            return {
                **prepared,
                **send_result,
                "send_strategy": "bot_fallback",
                "sender_attempt_order": attempts,
                "bot_message_fallback_used": True,
                "webhook_url_value_logged": False,
                "raw_discord_ids_logged": False,
                "secret_values_logged": False,
            }
    send_result = await send_discord_messages_safely(channel.send, messages, fallback_send_one=channel.send)
    return {
        **prepared,
        **send_result,
        "send_strategy": "bot_fallback",
        "sender_attempt_order": attempts + ["bot_fallback"],
        "bot_message_fallback_used": True,
        "discord_send_failure_reason": send_result.get("discord_send_failure_reason") or last_failure_reason,
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
    prepared = prepare_discord_outbound_messages(content, selected_agent or "hermes")
    send_result = await send_discord_messages_safely(message.channel.send, list(prepared.get("messages") or []), fallback_send_one=message.channel.send)
    return {**prepared, **send_result, "send_strategy": "bot_fallback", "bot_message_fallback_used": True}


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
            notice = (
                "[HANDOFF_BLOCKED]\n"
                f"target_channel: {target_name}\n"
                "reason: target_channel_missing\n"
                "external_execution_performed: false"
            )
            prepared = prepare_discord_outbound_messages(notice, selected_agent or "hermes")
            await send_discord_messages_safely(current_channel.send, list(prepared.get("messages") or []), fallback_send_one=current_channel.send)
        return
    if selected_agent:
        await _send_agent_content(client, selected_agent, target_channel, content)
        return
    prepared = prepare_discord_outbound_messages(content, selected_agent or "hermes")
    await send_discord_messages_safely(target_channel.send, list(prepared.get("messages") or []), fallback_send_one=target_channel.send)


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
        agent_web_bridge_ack = await _maybe_send_agent_web_bridge_ack(message, client=client)
        client._last_agent_web_bridge_ack = agent_web_bridge_ack
        replied_content = await _referenced_message_content(message)
        if agent_web_bridge_ack.get("agent_web_bridge_selected"):
            client._last_agent_web_bridge_completion = await _complete_agent_web_bridge_after_ack(
                message,
                agent_web_bridge_ack,
                replied_content=replied_content,
                client=client,
            )
            return
        result = build_company_agent_message_result(
            channel_name,
            str(getattr(message, "content", "") or ""),
            replied_content,
        )
        if result.get("reply_prepared"):
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
