"""Phase 33D RAG context safety checks without LLM, embeddings, or Discord send."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_source_registry import validate_rag_source_name


VERSION = "phase33d_context_safety_no_llm"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
ABSOLUTE_PRIVATE_PATH_RE = re.compile(r"(?i)([a-z]:\\|\\\\[^\\]+\\|/users/|/home/)")
BLOCKED_PATH_RE = re.compile(r"(?i)(^|[\\/])(exports|logs|local|\.env)([\\/]|$)")
BINARY_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _result_text(results: list[dict[str, Any]]) -> str:
    return "\n".join(str(item.get("excerpt", "")) for item in results)


def build_rag_context_safety_report(
    retrieval_report: dict[str, Any] | None = None,
    source: str = "operation",
    max_documents: int = 5,
    max_context_chars: int = 3000,
) -> dict[str, Any]:
    report = retrieval_report or {
        "source": source,
        "source_valid": bool(validate_rag_source_name(source).get("valid")),
        "results": [],
    }
    source_name = str(report.get("source", source) or "").strip().lower()
    validation = validate_rag_source_name(source_name)
    results = list(report.get("results", []) or [])
    context_text = _result_text(results)
    blocked_reasons: list[str] = []

    if not validation.get("valid"):
        blocked_reasons.append("invalid_source")
    if source_name == "operations":
        blocked_reasons.append("operations_source_not_allowed")
    if len(results) > int(max_documents):
        blocked_reasons.append("too_many_documents")
    if len(context_text) > int(max_context_chars):
        blocked_reasons.append("context_too_large")

    serialized_results = json.dumps(results, ensure_ascii=False)
    if ABSOLUTE_PRIVATE_PATH_RE.search(serialized_results):
        blocked_reasons.append("absolute_private_path_detected")
    if BLOCKED_PATH_RE.search(serialized_results) or ".env" in serialized_results.lower():
        blocked_reasons.append("blocked_runtime_path_detected")
    if SECRET_RE.search(serialized_results):
        blocked_reasons.append("secret_like_value_detected")
    if LONG_ID_RE.search(serialized_results):
        blocked_reasons.append("raw_discord_id_detected")
    if BINARY_RE.search(context_text):
        blocked_reasons.append("binary_content_detected")

    allowed = bool(validation.get("valid")) and not blocked_reasons
    output = {
        "report_type": "rag_context_safety_report",
        "version": VERSION,
        "created_at": utc_now(),
        "allowed_for_llm_prompt": allowed,
        "blocked": not allowed,
        "blocked_reasons": blocked_reasons,
        "source": source_name,
        "source_valid": bool(validation.get("valid")),
        "documents_checked": len(results),
        "context_chars": len(context_text),
        "max_documents": int(max_documents),
        "max_context_chars": int(max_context_chars),
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
    assert_rag_context_safety_safe(output)
    return output


def render_rag_context_safety_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Context Safety",
            "",
            f"- Source: {report.get('source', '')}",
            f"- Allowed for LLM prompt: {str(report.get('allowed_for_llm_prompt')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Blocked reasons: {', '.join(report.get('blocked_reasons', [])) or 'none'}",
            f"- Documents checked: {report.get('documents_checked', 0)}",
            f"- Context chars: {report.get('context_chars', 0)}",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_context_safety_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG context safety output contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG context safety output contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in ("embedding_api_called", "llm_api_called", "discord_message_sent", "external_execution"):
            if report.get(key):
                raise ValueError(f"RAG context safety unsafe flag is true: {key}")
