"""Phase 33D-safe RAG+LLM prompt envelope preview without API calls."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_context_safety import build_rag_context_safety_report
from rag_local_retrieval import run_rag_local_retrieval


VERSION = "phase33d_no_api_call"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
SYSTEM_PREVIEW = "Review-only RAG+LLM draft. Do not publish, submit, send, approve, confirm, or execute external actions. Use only the provided local read-only context."


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_rag_llm_prompt_envelope(
    root: str | None = None,
    source: str = "operation",
    query: str = "STOXL brand tone",
    agent_route_candidate: str = "marin",
) -> dict[str, Any]:
    retrieval = run_rag_local_retrieval(root=root, source=source, query=query, max_files=5, max_chars_per_file=3000)
    context_safety = build_rag_context_safety_report(retrieval, source=source)
    snippets = [
        {
            "source": item.get("source", ""),
            "path": item.get("path", ""),
            "excerpt_preview": str(item.get("excerpt", ""))[:240],
        }
        for item in retrieval.get("results", [])[:5]
    ]
    envelope = {
        "envelope_type": "rag_llm_prompt_envelope",
        "version": VERSION,
        "created_at": utc_now(),
        "agent_route_candidate": agent_route_candidate,
        "channel_scope": "private_test_only",
        "source": str(source).strip().lower(),
        "source_valid": bool(retrieval.get("source_valid")),
        "context_safety_allowed": bool(context_safety.get("allowed_for_llm_prompt")),
        "messages_preview": [
            {"role": "system", "content": SYSTEM_PREVIEW},
            {"role": "user", "content": f"Query preview: {str(query)[:240]}\nUse retrieved context previews only. Return review-only wording."},
        ],
        "retrieved_context_preview": snippets,
        "input_limits": {
            "max_context_chars": 3000,
            "max_documents": 5,
            "raw_content_included": False,
            "content_preview_only": True,
        },
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
    _assert_safe(envelope)
    return envelope


def render_rag_llm_prompt_envelope_markdown(envelope: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG+LLM Prompt Envelope",
            "",
            f"- Agent: {envelope.get('agent_route_candidate', '')}",
            f"- Channel scope: {envelope.get('channel_scope', '')}",
            f"- Source: {envelope.get('source', '')}",
            f"- Source valid: {str(envelope.get('source_valid')).lower()}",
            f"- Context safety allowed: {str(envelope.get('context_safety_allowed')).lower()}",
            "- Raw content included: false",
            "- Content preview only: true",
            "- LLM API called: false",
            "- Discord message sent: false",
        ]
    ) + "\n"


def _assert_safe(envelope: Any) -> None:
    text = json.dumps(envelope, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG+LLM prompt envelope contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG+LLM prompt envelope contains raw Discord-like IDs.")
