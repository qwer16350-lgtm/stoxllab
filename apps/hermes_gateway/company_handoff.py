"""Company agent handoff flow for STOXL Discord Agent OS v0."""

from __future__ import annotations

from typing import Any

from company_context_store import HandoffContext, sanitize_company_context_text, store_handoff_context
from company_agent_registry import get_agent
from company_persistent_memory import append_memory_record


HANDOFF_RULES = {
    "marin": {"to": "lucy", "target_channel": "lucy-검토", "status": "초안", "review_required": True},
    "lucy": {"to": "final-approval", "target_channel": "최종-승인요청", "status": "검토", "review_required": True},
    "kasumi": {"to": "meiko", "target_channel": "meiko-검토", "status": "리서치", "review_required": True},
    "meiko": {"to": "final-approval", "target_channel": "최종-승인요청", "status": "검토", "review_required": True},
    "reze": {"to": "decision-meeting", "target_channel": "대표-회의실", "status": "전략의견", "review_required": True},
}


STATUS_LABELS = {
    "marin": "초안 생성 완료",
    "kasumi": "리서치 정리 완료",
    "reze": "전략 검토 완료",
    "lucy": "검토 완료",
    "meiko": "운영 판단 완료",
}

NEXT_ACTIONS = {
    "marin": "루시 검토 필요",
    "kasumi": "메이코 검토 필요",
    "reze": "대표 회의실 검토 필요",
    "lucy": "최종 승인 검토 필요",
    "meiko": "최종 승인 검토 필요",
}


def get_handoff_rule(agent_id: str) -> dict[str, Any] | None:
    return HANDOFF_RULES.get(str(agent_id).lower())


def _agent_label(agent_id: str) -> str:
    agent = get_agent(agent_id) or {}
    persona = agent.get("webhook_persona") or str(agent_id).upper()
    display = agent.get("display_name") or agent_id
    return f"{persona} / {display}"


def _recipient_label(agent_id: str, target_channel: str) -> str:
    rule = get_handoff_rule(agent_id) or {}
    to_agent = str(rule.get("to") or "")
    if to_agent in {"lucy", "meiko", "reze"}:
        return _agent_label(to_agent)
    if target_channel == "대표-회의실":
        return "대표-회의실"
    if target_channel == "최종-승인요청":
        return "최종-승인요청"
    return target_channel


def store_company_handoff_context(
    source_agent: str,
    target_agent: str,
    source_channel: str,
    target_channel: str,
    status: str,
    request_summary: str,
    handoff_content: str,
    next_action: str,
) -> dict[str, Any]:
    stored = store_handoff_context(
        target_channel,
        HandoffContext(
            context_type="handoff",
            source_agent=source_agent,
            target_agent=target_agent,
            source_channel=source_channel,
            target_channel=target_channel,
            status=status,
            request_summary=request_summary,
            handoff_content=handoff_content,
            next_action=next_action,
        ),
    )
    persistent = append_memory_record(
        "handoff",
        {
            "source_agent": source_agent,
            "target_agent": target_agent,
            "source_channel": source_channel,
            "target_channel": target_channel,
            "title": sanitize_company_context_text(request_summary or f"{source_agent} handoff", 120),
            "summary": sanitize_company_context_text(request_summary, 500),
            "content": sanitize_company_context_text(handoff_content, 1600),
            "next_action": sanitize_company_context_text(next_action, 300),
            "status": "open",
        },
    )
    return {
        **stored,
        "persistent_memory_written": bool(persistent.get("record_written")),
        "persistent_memory_warning": persistent.get("warning_code"),
    }


def build_handoff_post_payload(result: dict[str, Any], request_summary: str = "") -> dict[str, Any]:
    agent_id = str(result.get("selected_agent") or "").lower()
    rule = get_handoff_rule(agent_id)
    response = result.get("response", {}) if isinstance(result.get("response"), dict) else {}
    target_channel = str(result.get("handoff_channel") or result.get("target_channel") or "")
    if not rule or not target_channel:
        return {
            "handoff_supported": False,
            "handoff_message_preview_present": False,
            "blocked": True,
            "blocked_reasons": ["handoff_target_missing"],
            "discord_api_send_called": False,
            "external_execution_performed": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    summary = sanitize_company_context_text(request_summary or "handoff requested", 300).strip()
    delivery = sanitize_company_context_text(response.get("content") or "handoff content unavailable", 1200).strip()
    target_agent = str(rule.get("to") or "")
    status = STATUS_LABELS.get(agent_id, rule.get("status", "handoff ready"))
    next_action = NEXT_ACTIONS.get(agent_id, "검토 필요")
    content = (
        "[HANDOFF]\n"
        f"from_agent: {_agent_label(agent_id)}\n"
        f"to: {_recipient_label(agent_id, target_channel)}\n"
        f"target_channel: {target_channel}\n"
        f"source_channel: {result.get('source_channel')}\n"
        f"status: {status}\n"
        f"review_required: {str(bool(rule.get('review_required'))).lower()}\n\n"
        "요청 요약:\n"
        f"{summary}\n\n"
        "전달 내용:\n"
        f"{delivery}\n\n"
        "다음 액션:\n"
        f"{next_action}"
    )
    stored_context = store_company_handoff_context(
        agent_id,
        target_agent,
        str(result.get("source_channel") or ""),
        target_channel,
        str(status),
        summary,
        delivery,
        next_action,
    )
    return {
        "handoff_supported": True,
        "handoff_target_channel": target_channel,
        "handoff_message_preview_present": True,
        "handoff_message": content,
        "handoff_context_saved": True,
        "handoff_context_source_agent": stored_context.get("source_agent"),
        "handoff_context_target_agent": stored_context.get("target_agent"),
        "blocked": False,
        "blocked_reasons": [],
        "discord_api_send_called": False,
        "external_execution_performed": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_handoff_message(from_agent: str, message: str = "", source_channel: str = "") -> dict[str, Any]:
    agent_id = str(from_agent).lower()
    rule = get_handoff_rule(agent_id)
    agent = get_agent(agent_id)
    if not rule or not agent:
        return {
            "handoff_available": False,
            "blocked": True,
            "blocked_reasons": ["unknown_handoff_agent"],
            "external_execution_allowed": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    summary = sanitize_company_context_text(message or "handoff requested", 300).strip()
    stored_context = store_company_handoff_context(
        agent_id,
        str(rule["to"]),
        source_channel,
        str(rule["target_channel"]),
        str(STATUS_LABELS.get(agent_id, rule["status"])),
        summary,
        summary,
        NEXT_ACTIONS.get(agent_id, "검토 필요"),
    )
    return {
        "handoff_available": True,
        "blocked": False,
        "from": agent_id,
        "from_display_name": agent.get("display_name"),
        "to": rule["to"],
        "target_channel": rule["target_channel"],
        "source_channel": source_channel,
        "status": rule["status"],
        "review_required": rule["review_required"],
        "summary": summary,
        "message_format": "[handoff]",
        "handoff_context_saved": True,
        "handoff_context_source_agent": stored_context.get("source_agent"),
        "handoff_context_target_agent": stored_context.get("target_agent"),
        "external_execution_allowed": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }
