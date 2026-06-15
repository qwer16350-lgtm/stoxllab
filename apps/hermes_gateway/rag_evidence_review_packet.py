"""Phase 34E private-test review packet for local RAG evidence output."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_evidence_integration import build_rag_evidence_integration_report


VERSION = "phase34e_private_test_review_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_rag_evidence_review_packet(
    root: str | None = None,
    source: str = "operation",
    agent: str = "kasumi",
    query: str = "STOXL brand tone",
    integration_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    integration = integration_report or build_rag_evidence_integration_report(root=root, source=source, agent=agent, query=query)
    rag_packet = integration.get("rag_response_packet", {}) if isinstance(integration.get("rag_response_packet"), dict) else {}
    evidence = rag_packet.get("evidence_packet", {}) if isinstance(rag_packet.get("evidence_packet"), dict) else {}
    citation_summary = rag_packet.get("citation_summary", {}) if isinstance(rag_packet.get("citation_summary"), dict) else {}
    source_valid = bool(integration.get("source_valid"))
    agent_source_allowed = bool(integration.get("agent_source_allowed"))
    rag_response_packet_available = bool(integration.get("rag_response_packet_created"))
    evidence_packet_available = bool(integration.get("evidence_packet_available")) and bool(evidence)
    citation_summary_available = bool(citation_summary)
    ready_for_private_test_review = (
        source_valid
        and agent_source_allowed
        and rag_response_packet_available
        and evidence_packet_available
        and citation_summary_available
    )
    packet = {
        "report_type": "rag_evidence_review_packet",
        "version": VERSION,
        "created_at": utc_now(),
        "source": str(integration.get("source", source)),
        "source_valid": source_valid,
        "agent": str(integration.get("agent", agent)),
        "agent_source_allowed": agent_source_allowed,
        "rag_response_packet_available": rag_response_packet_available,
        "evidence_packet_available": evidence_packet_available,
        "citation_summary_available": citation_summary_available,
        "review_only": True,
        "human_review_required": True,
        "ready_for_private_test_review": ready_for_private_test_review,
        "ready_for_llm_prompt": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "full_content_included": False,
        "content_preview_only": True,
        "citation_summary": citation_summary,
        "review_items": [
            {
                "label": "source_route",
                "status": "ready" if source_valid and agent_source_allowed else "blocked",
                "notes": "Review source and agent routing before any private-test use.",
            },
            {
                "label": "evidence_packet",
                "status": "ready" if evidence_packet_available else "blocked",
                "notes": "Evidence is preview-only and uses relative citations.",
            },
        ],
        "disallowed_actions": ["discord_send", "llm_prompt", "embedding", "external_ingest", "external_execution", "public_or_team_reply"],
        "embedding_api_called": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_review_packet_safe(packet)
    return packet


def render_rag_evidence_review_packet_markdown(packet: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence Review Packet",
            "",
            f"- Source: {packet.get('source', '')}",
            f"- Source valid: {str(packet.get('source_valid')).lower()}",
            f"- Agent: {packet.get('agent', '')}",
            f"- Agent source allowed: {str(packet.get('agent_source_allowed')).lower()}",
            f"- RAG response packet available: {str(packet.get('rag_response_packet_available')).lower()}",
            f"- Evidence packet available: {str(packet.get('evidence_packet_available')).lower()}",
            f"- Citation summary available: {str(packet.get('citation_summary_available')).lower()}",
            "- Review only: true",
            "- Human review required: true",
            f"- Ready for private test review: {str(packet.get('ready_for_private_test_review')).lower()}",
            "- Ready for LLM prompt: false",
            "- Ready for Discord send: false",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Full content included: false",
            "- Content preview only: true",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_evidence_review_packet_safe(packet: Any) -> None:
    text = json.dumps(packet, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence review packet contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence review packet contains raw Discord-like IDs.")
    if isinstance(packet, dict):
        for key in (
            "ready_for_llm_prompt",
            "ready_for_discord_send",
            "ready_for_embedding",
            "ready_for_external_sources",
            "full_content_included",
            "embedding_api_called",
            "llm_api_called",
            "discord_message_sent",
            "external_execution",
        ):
            if packet.get(key):
                raise ValueError(f"RAG evidence review packet unsafe flag is true: {key}")
