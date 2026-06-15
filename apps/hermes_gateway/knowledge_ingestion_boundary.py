"""Phase 34A local knowledge ingestion boundary."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_source_registry import get_canonical_rag_sources, validate_rag_source_name


VERSION = "phase34a_local_text_only"
FORBIDDEN_SOURCES = ["operations", "external", "nas", "drive", "notion", "web"]
ALLOWED_EXTENSIONS = [".txt", ".md", ".json", ".yaml", ".yml"]
DEFERRED_EXTENSIONS = [".pdf", ".docx", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg"]
BLOCKED_EXTENSIONS = [".env", ".key", ".pem", ".p12", ".sqlite", ".db", ".zip", ".7z", ".exe", ".ps1", ".bat"]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def classify_knowledge_extension(path_or_extension: str) -> dict[str, Any]:
    suffix = str(path_or_extension or "").lower()
    if not suffix.startswith("."):
        suffix = Path(suffix).suffix.lower()
    if suffix in ALLOWED_EXTENSIONS:
        status = "allowed"
    elif suffix in DEFERRED_EXTENSIONS:
        status = "deferred"
    elif suffix in BLOCKED_EXTENSIONS:
        status = "blocked"
    else:
        status = "blocked"
    return {"extension": suffix, "status": status, "allowed": status == "allowed"}


def validate_knowledge_source(source: str) -> dict[str, Any]:
    value = str(source or "").strip().lower()
    if value in FORBIDDEN_SOURCES:
        result = validate_rag_source_name(value)
        return {
            "valid": False,
            "source": value,
            "canonical_source": None,
            "warnings": result.get("warnings", ["forbidden_source"]),
            "suggested_source": result.get("suggested_source"),
        }
    return validate_rag_source_name(value)


def build_knowledge_ingestion_boundary_report(root: str | Path | None = None) -> dict[str, Any]:
    repo = _repo(root)
    canonical_sources = get_canonical_rag_sources()
    source_folders = {
        source: {
            "path": f"knowledge/{source}",
            "exists": (repo / "knowledge" / source).exists(),
        }
        for source in canonical_sources
    }
    report = {
        "report_type": "knowledge_ingestion_boundary",
        "version": VERSION,
        "created_at": utc_now(),
        "ready_for_local_text_ingestion": True,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "canonical_sources": canonical_sources,
        "forbidden_sources": FORBIDDEN_SOURCES,
        "allowed_extensions": ALLOWED_EXTENSIONS,
        "deferred_extensions": DEFERRED_EXTENSIONS,
        "blocked_extensions": BLOCKED_EXTENSIONS,
        "source_folders": source_folders,
        "sample_extension_validation": {
            ".md": classify_knowledge_extension(".md"),
            ".pdf": classify_knowledge_extension(".pdf"),
            ".env": classify_knowledge_extension(".env"),
        },
        "embedding_api_called": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
        "safety_assertions": {
            "full_content_dumped": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
            "external_source_ingested": False,
            "vector_db_created": False,
        },
    }
    assert_knowledge_boundary_safe(report)
    return report


def render_knowledge_ingestion_boundary_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Knowledge Ingestion Boundary",
            "",
            f"- Ready for local text ingestion: {str(report.get('ready_for_local_text_ingestion')).lower()}",
            f"- Ready for embedding: {str(report.get('ready_for_embedding')).lower()}",
            f"- Ready for external sources: {str(report.get('ready_for_external_sources')).lower()}",
            f"- Canonical sources: {', '.join(report.get('canonical_sources', []))}",
            "- Canonical operation source: operation",
            "- Forbidden alias: operations",
            f"- Allowed extensions: {', '.join(report.get('allowed_extensions', []))}",
            f"- Deferred extensions: {', '.join(report.get('deferred_extensions', []))}",
            f"- Blocked extensions: {', '.join(report.get('blocked_extensions', []))}",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_knowledge_boundary_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("Knowledge boundary report contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Knowledge boundary report contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in ("ready_for_embedding", "ready_for_external_sources", "embedding_api_called", "llm_api_called", "discord_message_sent", "external_execution"):
            if report.get(key):
                raise ValueError(f"Knowledge boundary unsafe flag is true: {key}")
