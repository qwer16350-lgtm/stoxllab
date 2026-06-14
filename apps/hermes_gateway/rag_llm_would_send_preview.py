"""Phase 33D-safe RAG+LLM would-send preview without Discord send."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_context_safety import build_rag_context_safety_report
from rag_llm_prompt_envelope import build_rag_llm_prompt_envelope
from rag_local_retrieval import run_rag_local_retrieval
from rag_source_registry import validate_rag_source_name


VERSION = "phase33d_no_live_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_rag_llm_would_send_preview(
    root: str | None = None,
    source: str = "operation",
    query: str = "STOXL brand tone",
    channel_scope: str = "private_test_only",
    author_is_bot: bool = False,
    self_message: bool = False,
) -> dict[str, Any]:
    validation = validate_rag_source_name(source)
    retrieval = run_rag_local_retrieval(root=root, source=source, query=query, max_files=5, max_chars_per_file=3000)
    context_safety = build_rag_context_safety_report(retrieval, source=source)
    envelope = build_rag_llm_prompt_envelope(root=root, source=source, query=query)
    blocked_reasons: list[str] = []
    if not validation.get("valid"):
        blocked_reasons.append("invalid_source")
    if source == "operations":
        blocked_reasons.append("operations_source_not_allowed")
    if channel_scope != "private_test_only":
        blocked_reasons.append("public_or_team_channel_blocked")
    if author_is_bot or self_message:
        blocked_reasons.append("self_or_bot_message_blocked")
    if not context_safety.get("allowed_for_llm_prompt"):
        blocked_reasons.append("context_safety_not_allowed")

    preview = {
        "report_type": "rag_llm_would_send_preview",
        "version": VERSION,
        "created_at": utc_now(),
        "channel_scope": channel_scope,
        "source": str(source).strip().lower(),
        "source_valid": bool(validation.get("valid")),
        "rag_context_safety_allowed": bool(context_safety.get("allowed_for_llm_prompt")),
        "llm_output_safety_allowed": False,
        "would_call_llm": False,
        "will_send": False,
        "message_sent": False,
        "discord_send_attempted": False,
        "preview_text": "[RAG+LLM PRIVATE TEST PREVIEW ONLY] Review-only draft would be generated after live gates pass. No external action has been taken.",
        "blocked_reasons": blocked_reasons,
        "required_before_live": [
            "rag_source_valid",
            "context_safety_allowed",
            "llm_api_call_enabled",
            "output_safety_allowed",
            "response_packet_created",
            "private_test_channel_id_match",
            "cooldown_budget_circuit_breaker_clear",
        ],
        "prompt_envelope_available": bool(envelope),
        "embedding_api_called": False,
        "llm_api_called": False,
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
    _assert_safe(preview)
    return preview


def render_rag_llm_would_send_preview_markdown(preview: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG+LLM Would-send Preview",
            "",
            f"- Channel scope: {preview.get('channel_scope', '')}",
            f"- Source: {preview.get('source', '')}",
            f"- Source valid: {str(preview.get('source_valid')).lower()}",
            f"- Context safety allowed: {str(preview.get('rag_context_safety_allowed')).lower()}",
            "- Would call LLM: false",
            "- Will send: false",
            "- Message sent: false",
            "- Discord send attempted: false",
            "- External execution: false",
        ]
    ) + "\n"


def _assert_safe(preview: Any) -> None:
    text = json.dumps(preview, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG+LLM would-send preview contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG+LLM would-send preview contains raw Discord-like IDs.")
