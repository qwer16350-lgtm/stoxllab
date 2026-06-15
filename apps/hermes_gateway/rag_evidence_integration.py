"""Phase 34D local evidence packet integration into RAG response packets."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from knowledge_evidence_packet import build_knowledge_evidence_packet
from rag_local_retrieval import run_rag_local_retrieval
from rag_response_packet import build_rag_response_packet


VERSION = "phase34d_local_evidence_to_rag_packet"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _relative_paths_only(citations: list[dict[str, Any]]) -> bool:
    for citation in citations:
        path = str(citation.get("relative_path") or citation.get("path") or "")
        if Path(path).is_absolute() or ":" in path or path.startswith("\\"):
            return False
    return True


def build_rag_evidence_integration_report(
    root: str | Path | None = None,
    source: str = "operation",
    agent: str = "kasumi",
    query: str = "STOXL brand tone",
    max_documents: int = 5,
    max_excerpt_chars: int = 600,
) -> dict[str, Any]:
    retrieval = run_rag_local_retrieval(root=root, source=source, query=query, max_files=max_documents)
    evidence = build_knowledge_evidence_packet(
        root=root,
        source=source,
        agent=agent,
        query=query,
        retrieval_report=retrieval,
        max_documents=max_documents,
        max_excerpt_chars=max_excerpt_chars,
    )
    rag_packet = build_rag_response_packet(retrieval, evidence_packet=evidence)
    source_valid = bool(evidence.get("source_valid"))
    agent_source_allowed = bool(evidence.get("agent_source_allowed"))
    evidence_packet_available = bool(evidence)
    rag_response_packet_created = bool(rag_packet.get("packet_type") == "rag_response_packet" and rag_packet.get("response_available"))
    citations = evidence.get("citations", [])
    report = {
        "report_type": "rag_evidence_integration",
        "version": VERSION,
        "created_at": utc_now(),
        "source": str(source or "").strip().lower(),
        "source_valid": source_valid,
        "agent": str(agent or "").strip().lower(),
        "agent_source_allowed": agent_source_allowed,
        "evidence_packet_available": evidence_packet_available,
        "rag_response_packet_created": rag_response_packet_created,
        "citations_included": isinstance(citations, list),
        "citation_count": len(citations),
        "relative_paths_only": _relative_paths_only(citations),
        "full_content_included": False,
        "content_preview_only": True,
        "ready_for_llm_prompt": False,
        "ready_for_private_test_review": source_valid and agent_source_allowed and evidence_packet_available,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "rag_response_packet": {
            "packet_type": rag_packet.get("packet_type"),
            "source": rag_packet.get("source"),
            "source_valid": rag_packet.get("source_valid"),
            "response_available": rag_packet.get("response_available"),
            "evidence_packet": rag_packet.get("evidence_packet", {}),
            "citation_summary": rag_packet.get("citation_summary", {}),
            "embedding_api_called": False,
            "llm_api_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
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
    assert_rag_evidence_integration_safe(report)
    return report


def render_rag_evidence_integration_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence Integration",
            "",
            f"- Source: {report.get('source', '')}",
            f"- Source valid: {str(report.get('source_valid')).lower()}",
            f"- Agent: {report.get('agent', '')}",
            f"- Agent source allowed: {str(report.get('agent_source_allowed')).lower()}",
            f"- Evidence packet available: {str(report.get('evidence_packet_available')).lower()}",
            f"- RAG response packet created: {str(report.get('rag_response_packet_created')).lower()}",
            f"- Citations included: {str(report.get('citations_included')).lower()}",
            f"- Citation count: {report.get('citation_count', 0)}",
            f"- Relative paths only: {str(report.get('relative_paths_only')).lower()}",
            "- Full content included: false",
            "- Content preview only: true",
            f"- Ready for private test review: {str(report.get('ready_for_private_test_review')).lower()}",
            "- Ready for LLM prompt: false",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_evidence_integration_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence integration contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence integration contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in (
            "full_content_included",
            "ready_for_llm_prompt",
            "ready_for_embedding",
            "ready_for_external_sources",
            "embedding_api_called",
            "llm_api_called",
            "discord_message_sent",
            "external_execution",
        ):
            if report.get(key):
                raise ValueError(f"RAG evidence integration unsafe flag is true: {key}")
        if not report.get("relative_paths_only", True):
            raise ValueError("RAG evidence integration contains absolute paths.")
