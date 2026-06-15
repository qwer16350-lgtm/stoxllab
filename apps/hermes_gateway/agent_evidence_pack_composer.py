"""Phase 35C agent evidence pack composer.

Rule-only evidence pack composition from Phase 35B dry previews. No LLM,
Discord send, embedding/vector creation, full content dump, or external access.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent_routing_dry_preview import AGENT_ROUTES, route_allowed
from evidence_quality_preview import build_evidence_quality_preview
from local_knowledge_ingestion_preview import CANONICAL_SOURCES, FORBIDDEN_SOURCES, validate_knowledge_source


VERSION = "phase35c_agent_evidence_pack_composer_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def _sample_evidence_items() -> list[dict[str, Any]]:
    quality = build_evidence_quality_preview()
    items = []
    for finding in quality.get("quality_findings", []):
        items.append(
            {
                "source": finding.get("source", ""),
                "path": finding.get("path", ""),
                "citation_id": "operation:stoxl_operation_tone_sample",
                "citation_sufficient": bool(finding.get("citation_sufficient")),
                "duplicate_suspected": bool(finding.get("duplicate_suspected")),
                "stale_doc_suspected": bool(finding.get("stale_doc_suspected")),
            }
        )
    return items


def build_agent_evidence_pack_composer() -> dict[str, Any]:
    findings = _sample_evidence_items()
    packs: dict[str, Any] = {}
    for agent, allowed_sources in AGENT_ROUTES.items():
        blocked_sources = [source for source in CANONICAL_SOURCES + FORBIDDEN_SOURCES if source not in allowed_sources]
        items = [item for item in findings if item.get("source") in allowed_sources]
        packs[agent] = {
            "allowed_sources": list(allowed_sources),
            "blocked_sources": blocked_sources,
            "evidence_items": items,
        }
    report = {
        "report_type": "agent_evidence_pack_composer",
        "version": VERSION,
        "composer_available": True,
        "rule_only": True,
        "llm_called": False,
        "discord_message_sent": False,
        "ready_for_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "relative_paths_only": True,
        "full_content_included": False,
        "canonical_sources": CANONICAL_SOURCES,
        "forbidden_sources": FORBIDDEN_SOURCES,
        "agent_evidence_packs": packs,
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
    assert_agent_evidence_pack_composer_safe(report)
    return report


def validate_agent_source(agent: str, source: str) -> dict[str, Any]:
    source_check = validate_knowledge_source(source)
    if source_check["blocked"]:
        return {"agent": agent, "source": source, "allowed": False, "reason": source_check["reason"]}
    return route_allowed(agent, source)


def assert_agent_evidence_pack_composer_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text):
        raise ValueError("Agent evidence pack composer contains sensitive values.")
    for key in ("llm_called", "discord_message_sent", "ready_for_llm_call", "ready_for_discord_send", "ready_for_embedding", "ready_for_external_sources", "full_content_included"):
        if report.get(key):
            raise ValueError(f"Agent evidence pack composer unsafe flag is true: {key}")
    for pack in report.get("agent_evidence_packs", {}).values():
        for item in pack.get("evidence_items", []):
            path = str(item.get("path", ""))
            if ":" in path or path.startswith("/") or path.startswith("\\\\"):
                raise ValueError("Agent evidence pack composer requires relative paths only.")


def render_agent_evidence_pack_composer_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Agent Evidence Pack Composer",
            "",
            "- Composer available: true",
            "- Rule only: true",
            "- LLM called: false",
            "- Discord message sent: false",
            "- Ready for LLM call: false",
            "- Ready for Discord send: false",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Relative paths only: true",
            "- Full content included: false",
            f"- Agent pack count: {len(report.get('agent_evidence_packs', {}))}",
        ]
    ) + "\n"
