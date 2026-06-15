"""Phase 34C local citation/evidence packet."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from knowledge_source_routing import validate_agent_source_route
from rag_local_retrieval import run_rag_local_retrieval


VERSION = "phase34c_local_evidence_packet"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_excerpt(text: str, max_chars: int) -> str:
    redacted = SECRET_RE.sub("[REDACTED_SECRET]", str(text or ""))
    redacted = LONG_ID_RE.sub("[REDACTED_DISCORD_ID]", redacted)
    return redacted[: max(0, int(max_chars))]


def _relative_only(path: str) -> str:
    value = str(path or "").replace("\\", "/")
    if Path(value).is_absolute() or ":" in value:
        return "absolute_path_redacted"
    value = SECRET_RE.sub("[REDACTED_SECRET]", value)
    value = LONG_ID_RE.sub("[REDACTED_DISCORD_ID]", value)
    return value


def build_knowledge_evidence_packet(
    root: str | Path | None = None,
    source: str = "operation",
    agent: str = "kasumi",
    query: str = "STOXL brand tone",
    retrieval_report: dict[str, Any] | None = None,
    max_documents: int = 5,
    max_excerpt_chars: int = 600,
) -> dict[str, Any]:
    route = validate_agent_source_route(agent, source)
    report = retrieval_report if retrieval_report is not None else run_rag_local_retrieval(root=root, source=source, query=query, max_files=max_documents)
    source_valid = bool(report.get("source_valid")) and bool(route.get("source_valid"))
    agent_source_allowed = bool(route.get("agent_source_allowed"))
    documents: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []
    if source_valid and agent_source_allowed:
        for item in report.get("results", [])[: max(0, int(max_documents))]:
            relative_path = _relative_only(str(item.get("path", "")))
            excerpt = _safe_excerpt(str(item.get("excerpt", "")), max_excerpt_chars)
            doc = {
                "source": str(item.get("source", source)),
                "relative_path": relative_path,
                "excerpt_preview": excerpt,
                "char_count": len(excerpt),
                "full_content_included": False,
            }
            documents.append(doc)
            citations.append(
                {
                    "source": doc["source"],
                    "relative_path": relative_path,
                    "excerpt_preview": excerpt,
                    "char_count": len(excerpt),
                }
            )
    packet = {
        "report_type": "knowledge_evidence_packet",
        "version": VERSION,
        "created_at": utc_now(),
        "source": str(source or "").strip().lower(),
        "source_valid": source_valid,
        "agent": str(agent or "").strip().lower(),
        "agent_source_allowed": agent_source_allowed,
        "documents": documents,
        "citations": citations,
        "max_documents": max_documents,
        "max_excerpt_chars": max_excerpt_chars,
        "full_content_included": False,
        "content_preview_only": True,
        "ready_for_rag_response_packet": source_valid and agent_source_allowed,
        "ready_for_llm_prompt": False,
        "route_validation": route,
        "embedding_api_called": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
        "safety_assertions": {
            "absolute_paths_included": False,
            "full_content_included": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    assert_knowledge_evidence_packet_safe(packet)
    return packet


def render_knowledge_evidence_packet_markdown(packet: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Knowledge Evidence Packet",
            "",
            f"- Source: {packet.get('source', '')}",
            f"- Source valid: {str(packet.get('source_valid')).lower()}",
            f"- Agent: {packet.get('agent', '')}",
            f"- Agent source allowed: {str(packet.get('agent_source_allowed')).lower()}",
            f"- Documents: {len(packet.get('documents', []))}",
            f"- Citations: {len(packet.get('citations', []))}",
            f"- Max documents: {packet.get('max_documents', 0)}",
            f"- Max excerpt chars: {packet.get('max_excerpt_chars', 0)}",
            "- Full content included: false",
            "- Ready for RAG response packet: " + str(packet.get("ready_for_rag_response_packet", False)).lower(),
            "- Ready for LLM prompt: false",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_knowledge_evidence_packet_safe(packet: Any) -> None:
    text = json.dumps(packet, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("Knowledge evidence packet contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Knowledge evidence packet contains raw Discord-like IDs.")
    if isinstance(packet, dict):
        for key in ("full_content_included", "ready_for_llm_prompt", "embedding_api_called", "llm_api_called", "discord_message_sent", "external_execution"):
            if packet.get(key):
                raise ValueError(f"Knowledge evidence packet unsafe flag is true: {key}")
        for item in packet.get("citations", []):
            path = str(item.get("relative_path", ""))
            if Path(path).is_absolute() or ":" in path:
                raise ValueError("Knowledge evidence packet contains absolute path.")
