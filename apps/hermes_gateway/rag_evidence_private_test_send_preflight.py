"""Phase 34J-0 private-test send preflight design.

This is a design/preflight report only. It never sends Discord messages and
does not expose a live send CLI.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from rag_evidence_would_send_preview import build_rag_evidence_would_send_preview


VERSION = "phase34j0_send_preflight_no_discord_api"
APPROVAL_PHRASE = "I_APPROVE_ONE_PRIVATE_TEST_RAG_EVIDENCE_SEND"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def build_manual_approval(env: dict[str, Any] | None = None) -> dict[str, Any]:
    approved_flag = _flag(_env_value(env, "HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVED", "false"))
    phrase = _env_value(env, "HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVAL_PHRASE", "")
    exact = phrase == APPROVAL_PHRASE
    return {
        "required": True,
        "approved": bool(approved_flag and exact),
        "approval_phrase_present": bool(phrase),
        "approval_phrase_exact_match": bool(exact),
        "approval_phrase_value_logged": False,
    }


def build_rag_evidence_private_test_send_preflight(
    preview: dict[str, Any] | None = None,
    env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_preview = preview or build_rag_evidence_would_send_preview()
    manual = build_manual_approval(env)
    send_messages = _flag(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES", "false"))
    private_reply = _flag(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY", "false"))
    explicit_channel_key = env is not None and "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID" in env
    channel_present = bool(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "configured_by_prior_private_test")) if not explicit_channel_key else bool(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", ""))
    would_available = bool(selected_preview.get("would_send_preview_created"))
    blockers: list[str] = []
    if not would_available:
        blockers.append("would_send_preview_required")
    if not manual.get("approved"):
        blockers.append("manual_approval_required")
    if not send_messages:
        blockers.append("discord_send_messages_disabled")
    if not private_reply:
        blockers.append("discord_private_test_reply_disabled")
    if not channel_present:
        blockers.append("private_test_channel_id_missing")

    # Phase 34J-0 intentionally never allows actual send, even if all future gates are present.
    report = {
        "report_type": "rag_evidence_private_test_send_preflight",
        "version": VERSION,
        "would_send_preview_available": would_available,
        "manual_approval": manual,
        "manual_approval_required": True,
        "private_test_channel_configured": channel_present,
        "private_test_channel_only": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "discord_send_messages_enabled": send_messages,
        "discord_private_test_reply_enabled": private_reply,
        "discord_api_send_allowed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "ready_for_actual_private_test_send": False,
        "ready_for_phase34j1_manual_live_send": bool(would_available),
        "blocked_reasons": blockers,
        "llm_api_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "llm_called": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_private_test_send_preflight_safe(report)
    return report


def render_rag_evidence_private_test_send_preflight_markdown(report: dict[str, Any]) -> str:
    manual = report.get("manual_approval", {}) if isinstance(report.get("manual_approval"), dict) else {}
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test Send Preflight",
            "",
            f"- Would-send preview available: {str(report.get('would_send_preview_available')).lower()}",
            f"- Manual approval required: {str(manual.get('required')).lower()}",
            f"- Manual approval approved: {str(manual.get('approved')).lower()}",
            f"- Approval phrase present: {str(manual.get('approval_phrase_present')).lower()}",
            "- Approval phrase value logged: false",
            f"- Private test channel configured: {str(report.get('private_test_channel_configured')).lower()}",
            f"- Private test channel only: {str(report.get('private_test_channel_only')).lower()}",
            "- Public channel send allowed: false",
            "- Team channel send allowed: false",
            f"- Discord send messages enabled: {str(report.get('discord_send_messages_enabled')).lower()}",
            f"- Discord private test reply enabled: {str(report.get('discord_private_test_reply_enabled')).lower()}",
            "- Discord API send allowed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for actual private-test send: false",
            f"- Ready for Phase 34J-1 manual live send: {str(report.get('ready_for_phase34j1_manual_live_send')).lower()}",
        ]
    ) + "\n"


def assert_rag_evidence_private_test_send_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if APPROVAL_PHRASE.lower() in text:
        raise ValueError("RAG evidence private-test send preflight contains approval phrase value.")
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence private-test send preflight contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence private-test send preflight contains raw Discord-like IDs.")
    for key in ("public_channel_send_allowed", "team_channel_send_allowed", "discord_api_send_allowed", "discord_api_send_called", "discord_message_sent", "ready_for_actual_private_test_send", "llm_api_called", "embedding_api_called", "external_execution"):
        if report.get(key):
            raise ValueError(f"RAG evidence private-test send preflight unsafe flag is true: {key}")
    assertions = report.get("safety_assertions", {})
    for key in ("api_key_value_logged", "token_value_logged", "raw_discord_ids_logged", "approval_phrase_value_logged", "discord_api_send_called", "discord_message_sent", "llm_called", "embedding_called", "external_execution"):
        if assertions.get(key):
            raise ValueError(f"RAG evidence private-test send preflight unsafe assertion is true: {key}")
