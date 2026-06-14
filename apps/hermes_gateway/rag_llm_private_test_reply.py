"""Phase 33D-safe RAG+LLM private test reply preflight.

This module never calls LLM providers, embeddings, Discord, or external systems.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from rag_response_packet import build_rag_response_packet_report
from rag_source_registry import validate_rag_source_name
from rag_llm_private_test_runtime import (
    build_rag_llm_private_reply_preflight,
    build_rag_llm_reply_pipeline_plan,
    build_rag_llm_reply_send_payload,
    record_rag_llm_reply_attempt,
    should_allow_rag_llm_private_reply,
)


VERSION = "phase33d_safe_scaffold_no_live_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def env_bool(env: dict[str, str] | None, key: str, default: bool = False) -> bool:
    source = env if env is not None else os.environ
    value = str(source.get(key, str(default))).strip().lower()
    return value in {"1", "true", "yes", "on"}


def env_value(env: dict[str, str] | None, key: str, default: str = "") -> str:
    source = env if env is not None else os.environ
    return str(source.get(key, default)).strip()


def build_rag_llm_private_test_reply_preflight(
    root: str | None = None,
    source: str = "operation",
    query: str = "STOXL brand tone",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    validation = validate_rag_source_name(source)
    rag_mode = env_value(env, "HERMES_RAG_MODE", "local_readonly")
    rag_enabled = env_bool(env, "HERMES_RAG_ENABLED", False)
    rag_reply_enabled = env_bool(env, "HERMES_RAG_LLM_REPLY_ENABLED", False)
    response_packet_required = env_bool(env, "HERMES_RAG_REQUIRE_RESPONSE_PACKET", True)
    llm_reply_enabled = env_bool(env, "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED", False)
    llm_send_enabled = env_bool(env, "HERMES_LLM_DISCORD_SEND_ENABLED", False)
    discord_send_enabled = env_bool(env, "HERMES_DISCORD_SEND_MESSAGES", False)
    private_test_reply = env_bool(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY", False)
    private_test_only = env_bool(env, "HERMES_RAG_PRIVATE_TEST_ONLY", True) and env_value(env, "HERMES_DISCORD_REPLY_MODE", "private_test_only") == "private_test_only"
    private_channel_configured = bool(env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", ""))
    allowed_sources = [item.strip() for item in env_value(env, "HERMES_RAG_ALLOWED_SOURCES", "marketing,operation,strategy,brand,archive").split(",") if item.strip()]
    packet = build_rag_response_packet_report(root=root, source=source, query=query)

    blocked_reasons: list[str] = []
    if not rag_reply_enabled:
        blocked_reasons.append("rag_llm_reply_disabled_by_default")
    if not validation.get("valid"):
        blocked_reasons.append("invalid_source")
    if source == "operations":
        blocked_reasons.append("operations_source_not_allowed")
    if validation.get("canonical_source") not in allowed_sources:
        blocked_reasons.append("source_not_allowed")
    if rag_mode != "local_readonly":
        blocked_reasons.append("rag_mode_not_local_readonly")
    if rag_enabled:
        blocked_reasons.append("rag_runtime_enabled_not_allowed_in_safe_scaffold")
    if not response_packet_required:
        blocked_reasons.append("rag_response_packet_not_required")
    if not packet.get("response_available"):
        blocked_reasons.append("rag_response_packet_unavailable")
    if not llm_reply_enabled:
        blocked_reasons.append("llm_private_reply_disabled")
    if not llm_send_enabled:
        blocked_reasons.append("llm_discord_send_disabled")
    if not private_test_reply:
        blocked_reasons.append("discord_private_test_reply_disabled")
    if not private_test_only:
        blocked_reasons.append("private_test_only_required")
    if not private_channel_configured:
        blocked_reasons.append("private_test_channel_id_missing")
    if not discord_send_enabled:
        blocked_reasons.append("discord_send_disabled")

    return _safe_report(
        {
            "report_type": "rag_llm_private_test_reply_preflight",
            "version": VERSION,
            "created_at": utc_now(),
            "ready": False,
            "blocked": True,
            "blocked_reasons": blocked_reasons or ["safe_scaffold_blocks_live_reply"],
            "source": str(source).strip().lower(),
            "source_valid": bool(validation.get("valid")),
            "rag_mode": rag_mode,
            "rag_enabled": rag_enabled,
            "rag_response_packet_required": response_packet_required,
            "rag_response_packet_available": bool(packet.get("response_available")),
            "llm_reply_enabled": llm_reply_enabled,
            "llm_discord_send_enabled": llm_send_enabled,
            "discord_send_enabled": discord_send_enabled,
            "private_test_reply_enabled": private_test_reply,
            "private_test_only": private_test_only,
            "private_test_channel_configured": private_channel_configured,
            "retrieval_executed": False,
            "embedding_api_called": False,
            "llm_api_called": False,
            "discord_message_sent": False,
            "external_execution": False,
            "ready_for_phase33d_live_implementation": False,
            "safety_assertions": _safe_assertions(),
        }
    )


def _safe_assertions() -> dict[str, bool]:
    return {
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "embedding_called": False,
        "llm_called": False,
        "discord_message_sent": False,
        "external_execution": False,
    }


def render_rag_llm_private_test_reply_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG+LLM Private Test Reply Preflight",
            "",
            f"- Ready: {str(report.get('ready')).lower()}",
            f"- Blocked: {str(report.get('blocked')).lower()}",
            f"- Blocked reasons: {', '.join(report.get('blocked_reasons', []))}",
            f"- Source: {report.get('source', '')}",
            f"- RAG mode: {report.get('rag_mode', '')}",
            "- Retrieval executed: false",
            "- Embedding API called: false",
            "- LLM API called: false",
            "- Discord message sent: false",
            "- External execution: false",
            "- Live implementation: not implemented",
        ]
    ) + "\n"


def _safe_report(report: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG+LLM private reply report contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG+LLM private reply report contains raw Discord-like IDs.")
    return report
