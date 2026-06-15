"""Phase 34A local text-only knowledge manifest."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from knowledge_ingestion_boundary import (
    ALLOWED_EXTENSIONS,
    BLOCKED_EXTENSIONS,
    DEFERRED_EXTENSIONS,
    classify_knowledge_extension,
)
from rag_source_registry import get_canonical_rag_sources


VERSION = "phase34a_local_text_only_manifest"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def _safe_relative(path: Path, repo_root: Path) -> str:
    try:
        rel = path.resolve().relative_to(repo_root)
    except ValueError:
        return "path_outside_repo_redacted"
    value = str(rel).replace("\\", "/")
    value = SECRET_RE.sub("[REDACTED_SECRET]", value)
    value = LONG_ID_RE.sub("[REDACTED_DISCORD_ID]", value)
    return value


def build_knowledge_manifest(root: str | Path | None = None, max_files_per_source: int = 100) -> dict[str, Any]:
    repo = _repo(root)
    canonical_sources = get_canonical_rag_sources()
    sources: dict[str, Any] = {}
    totals = {"allowed": 0, "deferred": 0, "blocked": 0}
    operations_source_present = (repo / "knowledge" / "operations").exists()

    for source in canonical_sources:
        base = repo / "knowledge" / source
        files: list[dict[str, Any]] = []
        counts = {"allowed": 0, "deferred": 0, "blocked": 0}
        if base.exists():
            for path in sorted(base.rglob("*")):
                if len(files) >= max_files_per_source:
                    break
                if not path.is_file():
                    continue
                if path.name == ".gitkeep":
                    continue
                classification = classify_knowledge_extension(path.name)
                status = classification["status"]
                counts[status] += 1
                totals[status] += 1
                files.append(
                    {
                        "source": source,
                        "relative_path": _safe_relative(path, repo),
                        "extension": classification["extension"],
                        "status": status,
                        "size_bytes": path.stat().st_size,
                        "content_preview_included": False,
                        "full_content_included": False,
                    }
                )
        sources[source] = {
            "folder": f"knowledge/{source}",
            "exists": base.exists(),
            "file_count": len(files),
            "counts": counts,
            "files": files,
        }

    report = {
        "report_type": "knowledge_manifest",
        "version": VERSION,
        "created_at": utc_now(),
        "knowledge_root": "knowledge",
        "canonical_sources": canonical_sources,
        "operations_source_present": operations_source_present,
        "sources": sources,
        "totals": totals,
        "allowed_extensions": ALLOWED_EXTENSIONS,
        "deferred_extensions": DEFERRED_EXTENSIONS,
        "blocked_extensions": BLOCKED_EXTENSIONS,
        "content_preview_included": False,
        "full_content_included": False,
        "ready_for_local_text_ingestion": True,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "embedding_api_called": False,
        "llm_api_called": False,
        "discord_message_sent": False,
        "external_execution": False,
        "safety_assertions": {
            "full_content_dumped": False,
            "secret_like_content_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    assert_knowledge_manifest_safe(report)
    return report


def render_knowledge_manifest_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# STOXL Knowledge Manifest",
        "",
        f"- Knowledge root: {report.get('knowledge_root', '')}",
        f"- Ready for local text ingestion: {str(report.get('ready_for_local_text_ingestion')).lower()}",
        f"- Ready for embedding: {str(report.get('ready_for_embedding')).lower()}",
        f"- Ready for external sources: {str(report.get('ready_for_external_sources')).lower()}",
        f"- Operations source present: {str(report.get('operations_source_present', False)).lower()}",
        "- Full content included: false",
        "",
        "## Sources",
    ]
    for source, detail in report.get("sources", {}).items():
        counts = detail.get("counts", {})
        lines.append(
            f"- {source}: exists={str(detail.get('exists', False)).lower()}, "
            f"allowed={counts.get('allowed', 0)}, deferred={counts.get('deferred', 0)}, blocked={counts.get('blocked', 0)}"
        )
    return "\n".join(lines) + "\n"


def assert_knowledge_manifest_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("Knowledge manifest contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Knowledge manifest contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in ("ready_for_embedding", "ready_for_external_sources", "embedding_api_called", "llm_api_called", "discord_message_sent", "external_execution", "full_content_included"):
            if report.get(key):
                raise ValueError(f"Knowledge manifest unsafe flag is true: {key}")
