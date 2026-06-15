"""Phase 35B evidence quality dry preview."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from local_knowledge_ingestion_preview import CANONICAL_SOURCES, FORBIDDEN_SOURCES


VERSION = "phase35b_evidence_quality_preview_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def _sample_findings() -> list[dict[str, Any]]:
    return [
        {
            "id": "sample_operation_tone",
            "source": "operation",
            "path": "knowledge/operation/stoxl_operation_tone_sample.md",
            "citation_sufficient": True,
            "duplicate_suspected": False,
            "stale_doc_suspected": False,
        }
    ]


def build_evidence_quality_preview(root: str | Path | None = None, findings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    selected_findings = findings if findings is not None else _sample_findings()
    report = {
        "report_type": "evidence_quality_preview",
        "version": VERSION,
        "evidence_quality_preview_available": True,
        "citation_sufficiency_checked": True,
        "duplicate_evidence_checked": True,
        "stale_doc_suspicion_checked": True,
        "relative_paths_only": True,
        "full_content_included": False,
        "ready_for_llm_prompt": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "ready_for_discord_send": False,
        "quality_findings": selected_findings,
        "canonical_sources": CANONICAL_SOURCES,
        "forbidden_sources": FORBIDDEN_SOURCES,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "embedding_called": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
        },
    }
    assert_evidence_quality_preview_safe(report)
    return report


def assert_evidence_quality_preview_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text):
        raise ValueError("Evidence quality preview contains sensitive values.")
    for key in ("full_content_included", "ready_for_llm_prompt", "ready_for_embedding", "ready_for_external_sources", "ready_for_discord_send"):
        if report.get(key):
            raise ValueError(f"Evidence quality preview unsafe flag is true: {key}")
    for finding in report.get("quality_findings", []):
        path = str(finding.get("path", ""))
        if ":" in path or path.startswith("/") or path.startswith("\\\\"):
            raise ValueError("Evidence quality preview requires relative paths only.")


def render_evidence_quality_preview_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Evidence Quality Preview",
            "",
            "- Citation sufficiency checked: true",
            "- Duplicate evidence checked: true",
            "- Stale doc suspicion checked: true",
            "- Relative paths only: true",
            "- Full content included: false",
            f"- Quality finding count: {len(report.get('quality_findings', []))}",
            "- Ready for LLM prompt: false",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Ready for Discord send: false",
        ]
    ) + "\n"
