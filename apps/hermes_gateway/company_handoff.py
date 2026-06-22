"""Company agent handoff flow for STOXL Discord Agent OS v0."""

from __future__ import annotations

from typing import Any

from company_agent_registry import get_agent


HANDOFF_RULES = {
    "marin": {"to": "lucy", "target_channel": "lucy-검토", "status": "초안", "review_required": True},
    "lucy": {"to": "final-approval", "target_channel": "최종-승인요청", "status": "검토", "review_required": True},
    "kasumi": {"to": "meiko", "target_channel": "meiko-검토", "status": "리서치", "review_required": True},
    "meiko": {"to": "final-approval", "target_channel": "최종-승인요청", "status": "검토", "review_required": True},
    "reze": {"to": "decision-meeting", "target_channel": "대표-회의실", "status": "전략의견", "review_required": True},
}


def get_handoff_rule(agent_id: str) -> dict[str, Any] | None:
    return HANDOFF_RULES.get(str(agent_id).lower())


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
    summary = (message or "handoff requested").strip()[:300]
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
        "external_execution_allowed": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }
