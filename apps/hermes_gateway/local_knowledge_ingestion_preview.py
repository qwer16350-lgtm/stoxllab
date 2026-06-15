"""Phase 35B local knowledge ingestion preview.

Report-only validation for repo-local text knowledge sources. No file watcher,
embedding, vector DB, LLM, Discord send, or external source access is performed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


VERSION = "phase35b_local_knowledge_ingestion_preview_report_only"
CANONICAL_SOURCES = ["marketing", "operation", "strategy", "brand", "archive"]
FORBIDDEN_SOURCES = ["operations"]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def validate_knowledge_source(source: str) -> dict[str, Any]:
    if source in CANONICAL_SOURCES:
        return {"source": source, "accepted": True, "blocked": False, "reason": ""}
    if source in FORBIDDEN_SOURCES:
        return {"source": source, "accepted": False, "blocked": True, "reason": "forbidden_source"}
    return {"source": source, "accepted": False, "blocked": True, "reason": "unknown_source"}


def _relative_path(path: str | Path) -> str:
    text = str(path).replace("\\", "/")
    if ":" in text or text.startswith("/") or text.startswith("//"):
        return ""
    return text


def build_local_knowledge_ingestion_preview(
    root: str | Path | None = None,
    *,
    source: str = "operation",
    candidate_paths: list[str] | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    source_check = validate_knowledge_source(source)
    for raw_path in candidate_paths or []:
        relative = _relative_path(raw_path)
        item = {
            "source": source,
            "path": relative or "[blocked_absolute_or_external_path]",
            "accepted": bool(relative and source_check["accepted"]),
            "blocked": bool(not relative or source_check["blocked"]),
            "reason": "" if relative and source_check["accepted"] else ("non_relative_path" if not relative else source_check["reason"]),
        }
        (blocked if item["blocked"] else candidates).append(item)
    if source_check["blocked"]:
        blocked.append(source_check)
    report = {
        "report_type": "local_knowledge_ingestion_preview",
        "version": VERSION,
        "ready_for_local_text_ingestion": source_check["accepted"],
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "ready_for_llm_prompt": False,
        "ready_for_discord_send": False,
        "canonical_sources": CANONICAL_SOURCES,
        "forbidden_sources": FORBIDDEN_SOURCES,
        "source_validation": source_check,
        "relative_paths_only": True,
        "full_content_included": False,
        "candidate_files": candidates,
        "blocked_candidates": blocked,
        "safety_assertions": _safety(),
    }
    assert_local_knowledge_ingestion_preview_safe(report)
    return report


def _safety() -> dict[str, Any]:
    return {
        "api_key_value_logged": False,
        "token_value_logged": False,
        "raw_discord_ids_logged": False,
        "approval_phrase_value_logged": False,
        "embedding_called": False,
        "external_execution": False,
        "llm_called": False,
        "discord_message_sent": False,
    }


def assert_local_knowledge_ingestion_preview_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Local knowledge ingestion preview contains sensitive values.")
    for key in ("ready_for_embedding", "ready_for_external_sources", "ready_for_llm_prompt", "ready_for_discord_send", "full_content_included"):
        if report.get(key):
            raise ValueError(f"Local knowledge ingestion preview unsafe flag is true: {key}")
    if "operation" not in report.get("canonical_sources", []) or "operations" not in report.get("forbidden_sources", []):
        raise ValueError("Local knowledge ingestion preview must keep operation canonical and operations forbidden.")


def render_local_knowledge_ingestion_preview_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Local Knowledge Ingestion Preview",
            "",
            f"- Ready for local text ingestion: {str(report.get('ready_for_local_text_ingestion')).lower()}",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Ready for LLM prompt: false",
            "- Ready for Discord send: false",
            f"- Canonical sources: {', '.join(report.get('canonical_sources', []))}",
            f"- Forbidden sources: {', '.join(report.get('forbidden_sources', []))}",
            "- Relative paths only: true",
            "- Full content included: false",
        ]
    ) + "\n"
