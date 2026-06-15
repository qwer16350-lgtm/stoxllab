"""Phase 34G prompt envelope preview for local RAG evidence review packets."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_evidence_integration import build_rag_evidence_integration_report
from rag_evidence_review_packet import build_rag_evidence_review_packet


VERSION = "phase34g_prompt_preview_no_api_call"
SYSTEM_INSTRUCTION = (
    "Review-only draft. No external action has been taken. "
    "Do not publish, submit, send, approve, confirm, or execute external actions. "
    "Use only the provided local evidence preview. "
    "If evidence is insufficient, say that evidence is insufficient."
)
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _preview_citations(citations: list[dict[str, Any]], max_chars: int = 240) -> list[dict[str, Any]]:
    output = []
    for item in citations:
        path = str(item.get("relative_path", ""))
        if Path(path).is_absolute() or ":" in path:
            path = "absolute_path_redacted"
        excerpt = str(item.get("excerpt_preview", ""))[:max_chars]
        output.append(
            {
                "source": item.get("source", ""),
                "relative_path": path,
                "excerpt_preview": excerpt,
                "char_count": len(excerpt),
            }
        )
    return output


def build_rag_evidence_prompt_envelope(
    root: str | Path | None = None,
    source: str = "operation",
    agent: str = "kasumi",
    query: str = "STOXL brand tone",
    review_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    integration = build_rag_evidence_integration_report(root=root, source=source, agent=agent, query=query)
    review = review_packet or build_rag_evidence_review_packet(
        root=str(root) if root is not None else None,
        source=source,
        agent=agent,
        query=query,
        integration_report=integration,
    )
    rag_packet = integration.get("rag_response_packet", {})
    evidence_packet = rag_packet.get("evidence_packet", {}) if isinstance(rag_packet, dict) else {}
    citations = _preview_citations(evidence_packet.get("citations", []) if isinstance(evidence_packet, dict) else [])
    citation_summary = review.get("citation_summary", {}) if isinstance(review.get("citation_summary"), dict) else {}
    user_content = {
        "task": "Create a concise review-only internal draft from the local evidence preview.",
        "source": source,
        "agent": agent,
        "query_preview": str(query or "")[:240],
        "citation_summary": {
            "citation_count": int(citation_summary.get("citation_count", len(citations)) or 0),
            "relative_paths_only": bool(citation_summary.get("relative_paths_only", True)),
        },
        "evidence_preview": citations,
        "constraints": [
            "Use review-only wording.",
            "Do not claim publication, submission, sending, approval, confirmation, or external execution.",
            "If evidence is insufficient, say that evidence is insufficient.",
        ],
    }
    envelope = {
        "report_type": "rag_evidence_prompt_envelope",
        "version": VERSION,
        "created_at": utc_now(),
        "source": str(source or "").strip().lower(),
        "source_valid": bool(review.get("source_valid")),
        "agent": str(agent or "").strip().lower(),
        "agent_source_allowed": bool(review.get("agent_source_allowed")),
        "review_packet_available": bool(review),
        "prompt_envelope_created": bool(review.get("ready_for_private_test_review")),
        "review_only": True,
        "human_review_required": True,
        "ready_for_prompt_preview": bool(review.get("ready_for_private_test_review")),
        "ready_for_llm_api_call": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "messages_preview": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
        ],
        "citation_summary": {
            "citation_count": int(citation_summary.get("citation_count", len(citations)) or 0),
            "relative_paths_only": bool(citation_summary.get("relative_paths_only", True)),
        },
        "full_content_included": False,
        "content_preview_only": True,
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
    assert_rag_evidence_prompt_envelope_safe(envelope)
    return envelope


def render_rag_evidence_prompt_envelope_markdown(envelope: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence Prompt Envelope",
            "",
            f"- Source: {envelope.get('source', '')}",
            f"- Source valid: {str(envelope.get('source_valid')).lower()}",
            f"- Agent: {envelope.get('agent', '')}",
            f"- Agent source allowed: {str(envelope.get('agent_source_allowed')).lower()}",
            f"- Review packet available: {str(envelope.get('review_packet_available')).lower()}",
            f"- Prompt envelope created: {str(envelope.get('prompt_envelope_created')).lower()}",
            "- Review only: true",
            "- Human review required: true",
            f"- Ready for prompt preview: {str(envelope.get('ready_for_prompt_preview')).lower()}",
            "- Ready for LLM API call: false",
            "- Ready for Discord send: false",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Full content included: false",
            "- Content preview only: true",
        ]
    ) + "\n"


def assert_rag_evidence_prompt_envelope_safe(envelope: Any) -> None:
    text = json.dumps(envelope, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence prompt envelope contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence prompt envelope contains raw Discord-like IDs.")
    if isinstance(envelope, dict):
        for key in (
            "ready_for_llm_api_call",
            "ready_for_discord_send",
            "ready_for_embedding",
            "ready_for_external_sources",
            "full_content_included",
            "embedding_api_called",
            "llm_api_called",
            "discord_message_sent",
            "external_execution",
        ):
            if envelope.get(key):
                raise ValueError(f"RAG evidence prompt envelope unsafe flag is true: {key}")
