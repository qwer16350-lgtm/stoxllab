"""Phase 34F local sample knowledge dry chain."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from knowledge_manifest import build_knowledge_manifest
from rag_evidence_integration import build_rag_evidence_integration_report
from rag_evidence_review_packet import build_rag_evidence_review_packet


VERSION = "phase34f_local_sample_dry_chain"
SAMPLE_FILES = [
    "knowledge/operation/stoxl_operation_tone_sample.md",
    "knowledge/operation/stoxl_private_test_workflow_sample.md",
]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def _sample_files_present(root: str | Path | None = None) -> bool:
    repo = _repo(root)
    return all((repo / path).exists() for path in SAMPLE_FILES)


def build_knowledge_dry_chain_report(
    root: str | Path | None = None,
    source: str = "operation",
    agent: str = "kasumi",
    query: str = "STOXL brand tone",
) -> dict[str, Any]:
    repo = _repo(root)
    manifest = build_knowledge_manifest(repo)
    integration = build_rag_evidence_integration_report(repo, source=source, agent=agent, query=query)
    review_packet = build_rag_evidence_review_packet(repo, source=source, agent=agent, query=query, integration_report=integration)
    rag_packet = integration.get("rag_response_packet", {})
    citation_summary = rag_packet.get("citation_summary", {}) if isinstance(rag_packet, dict) else {}
    report = {
        "report_type": "knowledge_dry_chain",
        "version": VERSION,
        "created_at": utc_now(),
        "source": source,
        "agent": agent,
        "sample_files_present": _sample_files_present(repo),
        "sample_files": list(SAMPLE_FILES),
        "manifest_available": bool(manifest),
        "evidence_packet_available": bool(integration.get("evidence_packet_available")),
        "rag_response_packet_available": bool(integration.get("rag_response_packet_created")),
        "review_packet_available": bool(review_packet),
        "citation_count": int(citation_summary.get("citation_count", integration.get("citation_count", 0)) or 0),
        "relative_paths_only": bool(citation_summary.get("relative_paths_only", integration.get("relative_paths_only", True))),
        "full_content_included": False,
        "content_preview_only": True,
        "ready_for_private_test_review": bool(review_packet.get("ready_for_private_test_review")),
        "ready_for_llm_prompt": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
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
    assert_knowledge_dry_chain_safe(report)
    return report


def render_knowledge_dry_chain_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Knowledge Dry Chain",
            "",
            f"- Source: {report.get('source', '')}",
            f"- Agent: {report.get('agent', '')}",
            f"- Sample files present: {str(report.get('sample_files_present')).lower()}",
            f"- Manifest available: {str(report.get('manifest_available')).lower()}",
            f"- Evidence packet available: {str(report.get('evidence_packet_available')).lower()}",
            f"- RAG response packet available: {str(report.get('rag_response_packet_available')).lower()}",
            f"- Review packet available: {str(report.get('review_packet_available')).lower()}",
            f"- Citation count: {report.get('citation_count', 0)}",
            f"- Relative paths only: {str(report.get('relative_paths_only')).lower()}",
            "- Full content included: false",
            "- Content preview only: true",
            f"- Ready for private test review: {str(report.get('ready_for_private_test_review')).lower()}",
            "- Ready for LLM prompt: false",
            "- Ready for Discord send: false",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_knowledge_dry_chain_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("Knowledge dry chain contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Knowledge dry chain contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in (
            "full_content_included",
            "ready_for_llm_prompt",
            "ready_for_discord_send",
            "ready_for_embedding",
            "ready_for_external_sources",
            "embedding_api_called",
            "llm_api_called",
            "discord_message_sent",
            "external_execution",
        ):
            if report.get(key):
                raise ValueError(f"Knowledge dry chain unsafe flag is true: {key}")
