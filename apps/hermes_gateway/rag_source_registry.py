"""Canonical local RAG source registry for Phase 33A."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any


VERSION = "phase33a_no_retrieval"
CANONICAL_RAG_SOURCES = ["marketing", "operation", "strategy", "brand", "archive"]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_canonical_rag_sources() -> list[str]:
    return list(CANONICAL_RAG_SOURCES)


def validate_rag_source_name(source_name: str) -> dict[str, Any]:
    source = str(source_name or "").strip().lower()
    if source in CANONICAL_RAG_SOURCES:
        return {
            "valid": True,
            "source": source,
            "canonical_source": source,
            "warnings": [],
        }
    if source == "operations":
        return {
            "valid": False,
            "source": source,
            "canonical_source": None,
            "warnings": ["use_operation_not_operations"],
            "suggested_source": "operation",
        }
    return {
        "valid": False,
        "source": source,
        "canonical_source": None,
        "warnings": ["unknown_rag_source"],
    }


def build_rag_source_registry_report() -> dict[str, Any]:
    validations = {source: validate_rag_source_name(source) for source in CANONICAL_RAG_SOURCES + ["operations", "unknown"]}
    report = {
        "report_type": "rag_source_registry_report",
        "version": VERSION,
        "created_at": utc_now(),
        "canonical_sources": get_canonical_rag_sources(),
        "source_validation": validations,
        "retrieval_executed": False,
        "embedding_api_called": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
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
    assert_rag_registry_safe(report)
    return report


def assert_rag_registry_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG source registry report contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG source registry report contains raw Discord-like IDs.")
