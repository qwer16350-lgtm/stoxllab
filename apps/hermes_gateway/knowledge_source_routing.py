"""Phase 34B agent-to-knowledge source routing policy."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from knowledge_ingestion_boundary import FORBIDDEN_SOURCES
from rag_source_registry import get_canonical_rag_sources, validate_rag_source_name


VERSION = "phase34b_agent_source_policy"
AGENT_SOURCE_POLICY = {
    "marin": ["marketing", "brand"],
    "lucy": ["marketing", "brand", "archive"],
    "kasumi": ["operation"],
    "meiko": ["operation", "archive"],
    "reze": ["strategy", "brand", "archive"],
    "decision_maker_review": ["marketing", "operation", "strategy", "brand", "archive"],
}
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_agent_source_route(agent: str, source: str) -> dict[str, Any]:
    agent_id = str(agent or "").strip().lower()
    source_name = str(source or "").strip().lower()
    source_validation = validate_rag_source_name(source_name)
    known_agent = agent_id in AGENT_SOURCE_POLICY
    if agent_id == "unrouted":
        known_agent = False
    source_allowed = known_agent and bool(source_validation.get("valid")) and source_name in AGENT_SOURCE_POLICY.get(agent_id, [])
    blocked_reasons: list[str] = []
    if source_name in FORBIDDEN_SOURCES or source_name == "operations":
        blocked_reasons.append("forbidden_source")
    if not known_agent:
        blocked_reasons.append("unknown_or_unrouted_agent")
    if not source_validation.get("valid"):
        blocked_reasons.append("invalid_source")
    elif known_agent and source_name not in AGENT_SOURCE_POLICY.get(agent_id, []):
        blocked_reasons.append("source_not_allowed_for_agent")
    return {
        "agent": agent_id,
        "source": source_name,
        "known_agent": known_agent,
        "source_valid": bool(source_validation.get("valid")),
        "agent_source_allowed": source_allowed,
        "review_only": True,
        "blocked": not source_allowed,
        "blocked_reasons": blocked_reasons,
        "source_validation": source_validation,
        "discord_message_sent": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "external_execution": False,
    }


def build_knowledge_source_routing_report() -> dict[str, Any]:
    report = {
        "report_type": "knowledge_source_routing",
        "version": VERSION,
        "created_at": utc_now(),
        "agent_source_policy": {key: list(value) for key, value in AGENT_SOURCE_POLICY.items()},
        "canonical_sources": get_canonical_rag_sources(),
        "forbidden_sources": ["operations"],
        "review_only": True,
        "sample_routes": {
            "kasumi_operation": validate_agent_source_route("kasumi", "operation"),
            "kasumi_marketing": validate_agent_source_route("kasumi", "marketing"),
            "unknown_operation": validate_agent_source_route("unknown", "operation"),
            "marin_operations": validate_agent_source_route("marin", "operations"),
        },
        "discord_message_sent": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "safety_assertions": {
            "review_only": True,
            "retrieval_executed": False,
            "discord_message_sent": False,
            "llm_called": False,
            "embedding_called": False,
            "external_execution": False,
            "public_or_team_reply_enabled": False,
        },
    }
    assert_knowledge_source_routing_safe(report)
    return report


def render_knowledge_source_routing_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# STOXL Knowledge Source Routing",
        "",
        "- Review only: true",
        "- Public/team channel reply enabled: false",
        "- Forbidden source alias: operations",
        "",
        "## Policy",
    ]
    for agent, sources in report.get("agent_source_policy", {}).items():
        lines.append(f"- {agent}: {', '.join(sources)}")
    lines.extend(
        [
            "",
            "- Discord message sent: false",
            "- LLM API called: false",
            "- Embedding API called: false",
            "- External execution: false",
        ]
    )
    return "\n".join(lines) + "\n"


def assert_knowledge_source_routing_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("Knowledge source routing contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Knowledge source routing contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in ("discord_message_sent", "llm_api_called", "embedding_api_called", "external_execution"):
            if report.get(key):
                raise ValueError(f"Knowledge source routing unsafe flag is true: {key}")
