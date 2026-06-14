"""Phase 33C RAG response packets without LLM or Discord send."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_local_retrieval import run_rag_local_retrieval


VERSION = "phase33c_no_llm_no_discord_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_rag_response_packet(retrieval_report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = retrieval_report or run_rag_local_retrieval()
    citations = [
        {
            "source": item.get("source", ""),
            "path": item.get("path", ""),
            "excerpt": item.get("excerpt", ""),
            "char_count": item.get("char_count", 0),
        }
        for item in report.get("results", [])
    ]
    source_valid = bool(report.get("source_valid"))
    packet = {
        "packet_type": "rag_response_packet",
        "version": VERSION,
        "created_at": utc_now(),
        "source_report_type": report.get("report_type", "rag_local_retrieval_report"),
        "query_preview": report.get("query_preview", ""),
        "source": report.get("source", ""),
        "source_valid": source_valid,
        "response_available": source_valid,
        "retrieval_summary": {
            "documents_found": int(report.get("documents_found", 0) or 0),
            "documents_returned": int(report.get("documents_returned", 0) or 0),
            "documents_skipped": int(report.get("documents_skipped", 0) or 0),
            "missing_source_folder_warning": bool(report.get("missing_source_folder_warning")),
        },
        "citations": citations,
        "review_notes": [
            "Phase 33C does not call LLM.",
            "Phase 33C does not send Discord messages.",
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
        },
    }
    assert_rag_response_packet_safe(packet)
    return packet


def build_rag_response_packet_report(root: str | None = None, source: str = "operation", query: str = "STOXL brand tone") -> dict[str, Any]:
    return build_rag_response_packet(run_rag_local_retrieval(root=root, source=source, query=query))


def render_rag_response_packet_markdown(packet: dict[str, Any]) -> str:
    summary = packet.get("retrieval_summary", {})
    return "\n".join(
        [
            "# STOXL RAG Response Packet",
            "",
            f"- Source: {packet.get('source', '')}",
            f"- Source valid: {str(packet.get('source_valid')).lower()}",
            f"- Response available: {str(packet.get('response_available')).lower()}",
            f"- Documents found: {summary.get('documents_found', 0)}",
            f"- Documents returned: {summary.get('documents_returned', 0)}",
            f"- Missing source folder warning: {str(summary.get('missing_source_folder_warning')).lower()}",
            "- Human review required: true",
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
