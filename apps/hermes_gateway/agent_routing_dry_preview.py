"""Phase 35B agent routing dry preview."""

from __future__ import annotations

import json
import re
from typing import Any

from local_knowledge_ingestion_preview import CANONICAL_SOURCES, FORBIDDEN_SOURCES


VERSION = "phase35b_agent_routing_dry_preview_report_only"
AGENT_ROUTES = {
    "marin": ["marketing", "brand"],
    "lucy": ["marketing", "brand", "archive"],
    "kasumi": ["operation"],
    "meiko": ["operation", "archive"],
    "reze": ["strategy", "brand", "archive"],
    "decision_maker_review": ["marketing", "operation", "strategy", "brand", "archive"],
    "unrouted": [],
}
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def route_allowed(agent: str, source: str) -> dict[str, Any]:
    if source in FORBIDDEN_SOURCES:
        return {"agent": agent, "source": source, "allowed": False, "reason": "forbidden_source"}
    if source not in CANONICAL_SOURCES:
        return {"agent": agent, "source": source, "allowed": False, "reason": "unknown_source"}
    allowed = source in AGENT_ROUTES.get(agent, [])
    return {"agent": agent, "source": source, "allowed": allowed, "reason": "" if allowed else "source_not_allowed_for_agent"}


def build_agent_routing_dry_preview() -> dict[str, Any]:
    blocked_routes = [
        route_allowed("kasumi", "operations"),
        route_allowed("marin", "operation"),
    ]
    report = {
        "report_type": "agent_routing_dry_preview",
        "version": VERSION,
        "routing_preview_available": True,
        "routing_rule_only": True,
        "llm_called": False,
        "discord_message_sent": False,
        "agent_routes": AGENT_ROUTES,
        "blocked_routes": blocked_routes,
        "ready_for_unattended_auto_reply": False,
        "ready_for_llm_prompt": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "ready_for_discord_send": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "embedding_called": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
        },
    }
    assert_agent_routing_dry_preview_safe(report)
    return report


def assert_agent_routing_dry_preview_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if LONG_ID_RE.search(text):
        raise ValueError("Agent routing dry preview contains raw Discord-like IDs.")
    for key in ("llm_called", "discord_message_sent", "ready_for_unattended_auto_reply", "ready_for_llm_prompt", "ready_for_embedding", "ready_for_external_sources", "ready_for_discord_send"):
        if report.get(key):
            raise ValueError(f"Agent routing dry preview unsafe flag is true: {key}")


def render_agent_routing_dry_preview_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Agent Routing Dry Preview",
            "",
            "- Routing rule only: true",
            "- LLM called: false",
            "- Discord message sent: false",
            "- Ready for unattended auto reply: false",
            f"- Agent route count: {len(report.get('agent_routes', {}))}",
            f"- Blocked route count: {len(report.get('blocked_routes', []))}",
        ]
    ) + "\n"
