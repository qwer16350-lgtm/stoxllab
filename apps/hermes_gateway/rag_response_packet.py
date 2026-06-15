"""Phase 33C RAG response packets without LLM or Discord send."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from knowledge_evidence_packet import build_knowledge_evidence_packet
from rag_local_retrieval import run_rag_local_retrieval


VERSION = "phase34d_evidence_packet_optional"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _relative_paths_only(items: list[dict[str, Any]]) -> bool:
    for item in items:
        path = str(item.get("relative_path") or item.get("path") or "")
        if ":" in path or path.startswith("/") or path.startswith("\\"):
            return False
    return True


def _empty_evidence_packet(source: str, agent: str = "") -> dict[str, Any]:
    return {
        "source": source,
        "agent": agent,
        "citations": [],
        "documents": [],
        "full_content_included": False,
        "content_preview_only": True,
    }


def build_rag_response_packet(retrieval_report: dict[str, Any] | None = None, evidence_packet: dict[str, Any] | None = None) -> dict[str, Any]:
    report = retrieval_report or run_rag_local_retrieval()
    evidence = evidence_packet
    if evidence is None and bool(report.get("source_valid")):
        evidence = build_knowledge_evidence_packet(
            source=str(report.get("source", "operation")),
            agent="kasumi",
            retrieval_report=report,
        )
    citations = [
        {
            "source": item.get("source", ""),
            "path": item.get("path", item.get("relative_path", "")),
            "excerpt": item.get("excerpt", item.get("excerpt_preview", "")),
            "char_count": item.get("char_count", 0),
        }
        for item in (evidence.get("citations", []) if evidence else report.get("results", []))
    ]
    source_valid = bool(report.get("source_valid"))
    evidence_ready = bool(evidence and evidence.get("ready_for_rag_response_packet", source_valid))
    response_available = source_valid and evidence_ready
    evidence_summary = {
        "source": evidence.get("source", report.get("source", "")) if evidence else report.get("source", ""),
        "agent": evidence.get("agent", "") if evidence else "",
        "citations": evidence.get("citations", []) if evidence else [],
        "documents": evidence.get("documents", []) if evidence else [],
        "full_content_included": bool(evidence.get("full_content_included")) if evidence else False,
        "content_preview_only": bool(evidence.get("content_preview_only", True)) if evidence else True,
    }
    citation_summary = {
        "citation_count": len(citations),
        "relative_paths_only": _relative_paths_only(evidence_summary["citations"] or citations),
        "blocked_secret_like_content": False,
        "raw_discord_ids_logged": False,
    }
    packet = {
        "packet_type": "rag_response_packet",
        "version": VERSION,
        "created_at": utc_now(),
        "source_report_type": report.get("report_type", "rag_local_retrieval_report"),
        "query_preview": report.get("query_preview", ""),
        "source": report.get("source", ""),
        "source_valid": source_valid,
        "response_available": response_available,
        "retrieval_summary": {
            "documents_found": int(report.get("documents_found", 0) or 0),
            "documents_returned": int(report.get("documents_returned", 0) or 0),
            "documents_skipped": int(report.get("documents_skipped", 0) or 0),
            "missing_source_folder_warning": bool(report.get("missing_source_folder_warning")),
        },
        "citations": citations,
        "evidence_packet": evidence_summary if evidence else _empty_evidence_packet(str(report.get("source", ""))),
        "citation_summary": citation_summary,
        "review_notes": [
            "Phase 34D does not call LLM.",
            "Phase 34D does not send Discord messages.",
            "Evidence packet is local preview-only.",
            "Human review is required before any use.",
        ],
        "human_review": {
            "required": True,
            "allowed_actions": ["review_only", "manual_edit"],
            "disallowed_actions": ["auto_reply", "public_publish", "external_execution", "discord_send"],
        },
        "embedding_api_called": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
            "full_content_included": False,
        },
    }
    assert_rag_response_packet_safe(packet)
    return packet


def build_rag_response_packet_report(root: str | None = None, source: str = "operation", query: str = "STOXL brand tone") -> dict[str, Any]:
    return build_rag_response_packet(run_rag_local_retrieval(root=root, source=source, query=query))


def render_rag_response_packet_markdown(packet: dict[str, Any]) -> str:
    summary = packet.get("retrieval_summary", {})
    citation_summary = packet.get("citation_summary", {})
    return "\n".join(
        [
            "# STOXL RAG Response Packet",
            "",
            f"- Source: {packet.get('source', '')}",
            f"- Source valid: {str(packet.get('source_valid')).lower()}",
            f"- Response available: {str(packet.get('response_available')).lower()}",
            f"- Documents found: {summary.get('documents_found', 0)}",
            f"- Documents returned: {summary.get('documents_returned', 0)}",
            f"- Citations: {citation_summary.get('citation_count', len(packet.get('citations', [])))}",
            f"- Relative paths only: {str(citation_summary.get('relative_paths_only', True)).lower()}",
            f"- Missing source folder warning: {str(summary.get('missing_source_folder_warning')).lower()}",
            "- Human review required: true",
            "- Ready for LLM prompt: false",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_response_packet_safe(packet: Any) -> None:
    text = json.dumps(packet, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG response packet contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG response packet contains raw Discord-like IDs.")
    if isinstance(packet, dict):
        for key in ("embedding_api_called", "llm_api_called", "discord_message_sent", "external_execution"):
            if packet.get(key):
                raise ValueError(f"RAG response packet unsafe flag is true: {key}")
        evidence = packet.get("evidence_packet", {})
        if evidence.get("full_content_included"):
            raise ValueError("RAG response packet includes full content.")
        if not packet.get("citation_summary", {}).get("relative_paths_only", True):
            raise ValueError("RAG response packet contains absolute citation paths.")
