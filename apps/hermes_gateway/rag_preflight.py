"""Phase 33A RAG preflight without retrieval."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_source_registry import get_canonical_rag_sources, validate_rag_source_name


VERSION = "phase33a_no_retrieval"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_rag_preflight_report() -> dict[str, Any]:
    source_validation = {
        "operation": validate_rag_source_name("operation"),
        "operations": validate_rag_source_name("operations"),
        "unknown": validate_rag_source_name("unknown"),
    }
    report = {
        "report_type": "rag_preflight_report",
        "version": VERSION,
        "created_at": utc_now(),
        "ready_for_rag_retrieval": False,
        "rag_enabled": False,
        "retrieval_executed": False,
        "embedding_api_called": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
        "canonical_sources": get_canonical_rag_sources(),
        "source_validation": source_validation,
        "blocked_reasons": ["rag_disabled_by_phase33a"],
        "ready_for_phase33b_local_readonly_retrieval": True,
        "safety_assertions": {
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
            "rag_called": False,
            "retrieval_executed": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    assert_rag_preflight_safe(report)
    return report


def render_rag_preflight_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Preflight",
            "",
            f"- Ready for RAG retrieval: {str(report.get('ready_for_rag_retrieval')).lower()}",
            f"- Ready for Phase 33B local readonly retrieval: {str(report.get('ready_for_phase33b_local_readonly_retrieval')).lower()}",
            f"- Canonical sources: {', '.join(report.get('canonical_sources', []))}",
            "- Retrieval executed: false",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
            "",
            "## Source Validation",
            f"- operation: {str(report.get('source_validation', {}).get('operation', {}).get('valid')).lower()}",
            f"- operations: {str(report.get('source_validation', {}).get('operations', {}).get('valid')).lower()} -> operation",
        ]
    ) + "\n"


def assert_rag_preflight_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG preflight contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG preflight contains raw Discord-like IDs.")
    if isinstance(report, dict):
        safety = report.get("safety_assertions", {})
        for key in ("rag_called", "retrieval_executed", "embedding_called", "llm_called", "discord_message_sent", "external_execution"):
            if safety.get(key) or report.get(key):
                raise ValueError(f"RAG preflight unsafe flag is true: {key}")
