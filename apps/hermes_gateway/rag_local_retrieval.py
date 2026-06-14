"""Phase 33B local read-only RAG retrieval without embeddings."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_source_registry import validate_rag_source_name


VERSION = "phase33b_local_readonly_no_embedding"
ALLOWED_EXTENSIONS = [".txt", ".md", ".json", ".yaml", ".yml"]
EXCLUDED_PARTS = {".git", "exports", "logs", "local", "__pycache__", "node_modules"}
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def _source_root(root: str | Path | None, source: str) -> Path:
    return _repo(root) / "knowledge" / source


def _is_excluded(path: Path, repo_root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo_root)
    except ValueError:
        return True
    parts = set(rel.parts)
    if ".env" in rel.parts:
        return True
    if "apps" in rel.parts and "hermes_gateway" in rel.parts and "local" in rel.parts:
        return True
    return bool(parts & EXCLUDED_PARTS)


def _safe_excerpt(text: str, max_chars: int) -> str:
    redacted = SECRET_RE.sub("[REDACTED_SECRET]", text)
    redacted = LONG_ID_RE.sub("[REDACTED_DISCORD_ID]", redacted)
    return redacted[: max(0, max_chars)]


def _safe_relative(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root)).replace("\\", "/")


def run_rag_local_retrieval(
    root: str | Path | None = None,
    source: str = "operation",
    query: str = "STOXL brand tone",
    max_files: int = 20,
    max_chars_per_file: int = 4000,
) -> dict[str, Any]:
    repo_root = _repo(root)
    validation = validate_rag_source_name(source)
    source_name = str(source or "").strip().lower()
    results: list[dict[str, Any]] = []
    skipped = 0
    found = 0
    missing = False
    if validation.get("valid"):
        base = _source_root(repo_root, source_name)
        if not base.exists():
            missing = True
        elif not base.resolve().is_relative_to(repo_root):
            validation = {"valid": False, "source": source_name, "canonical_source": None, "warnings": ["path_traversal_blocked"]}
        else:
            query_text = str(query or "").lower()
            for path in sorted(base.rglob("*")):
                if len(results) >= max_files:
                    break
                if not path.is_file():
                    continue
                if _is_excluded(path, repo_root):
                    skipped += 1
                    continue
                if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                    skipped += 1
                    continue
                found += 1
                try:
                    content = path.read_text(encoding="utf-8-sig", errors="replace")[:max_chars_per_file]
                except Exception:
                    skipped += 1
                    continue
                haystack = (path.name + "\n" + content).lower()
                if query_text and query_text not in haystack:
                    continue
                excerpt = _safe_excerpt(content, 800)
                results.append(
                    {
                        "source": source_name,
                        "path": _safe_relative(path, repo_root),
                        "excerpt": excerpt,
                        "char_count": len(excerpt),
                    }
                )
    report = {
        "report_type": "rag_local_retrieval_report",
        "version": VERSION,
        "created_at": utc_now(),
        "query_preview": _safe_excerpt(str(query or ""), 240),
        "source": source_name,
        "source_valid": bool(validation.get("valid")),
        "source_validation": validation,
        "retrieval_executed": bool(validation.get("valid")),
        "local_read_only": True,
        "embedding_api_called": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
        "documents_found": found,
        "documents_returned": len(results),
        "documents_skipped": skipped,
        "missing_source_folder_warning": bool(missing),
        "results": results,
        "limits": {
            "max_files": max_files,
            "max_chars_per_file": max_chars_per_file,
            "allowed_extensions": ALLOWED_EXTENSIONS,
        },
        "ready_for_phase33c_rag_response_packet": True,
        "safety_assertions": {
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
            "write_performed": False,
        },
    }
    assert_rag_local_retrieval_safe(report)
    return report


def render_rag_local_retrieval_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Local Read-only Retrieval",
            "",
            f"- Source: {report.get('source', '')}",
            f"- Source valid: {str(report.get('source_valid')).lower()}",
            f"- Query: {report.get('query_preview', '')}",
            f"- Documents found: {report.get('documents_found', 0)}",
            f"- Documents returned: {report.get('documents_returned', 0)}",
            f"- Missing source folder warning: {str(report.get('missing_source_folder_warning')).lower()}",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_local_retrieval_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG local retrieval report contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG local retrieval report contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in ("embedding_api_called", "llm_api_called", "discord_message_sent", "external_execution"):
            if report.get(key):
                raise ValueError(f"RAG local retrieval unsafe flag is true: {key}")
        safety = report.get("safety_assertions", {})
        for key in ("embedding_called", "llm_called", "discord_message_sent", "external_execution", "write_performed"):
            if safety.get(key):
                raise ValueError(f"RAG local retrieval unsafe assertion is true: {key}")
