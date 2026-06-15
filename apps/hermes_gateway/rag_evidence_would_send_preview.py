"""Phase 34I private-test would-send preview for RAG evidence LLM output.

This module formats a preview only. It never calls Discord, LLM providers,
embeddings, vector stores, external ingest, or external execution.
"""

from __future__ import annotations

import json
import re
from typing import Any

from rag_evidence_llm_dry_call_closeout import build_rag_evidence_llm_dry_call_closeout


VERSION = "phase34i_private_test_would_send_preview_no_discord_api"
MAX_PREVIEW_CHARS = 1200
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
MENTION_RE = re.compile(r"(@everyone|@here|<@!?\d+>|<@&\d+>)", re.IGNORECASE)


def _sanitize_mentions(text: str) -> tuple[str, bool]:
    blocked = False

    def replace(match: re.Match[str]) -> str:
        nonlocal blocked
        blocked = True
        value = match.group(0).lower()
        if value in {"@everyone", "@here"}:
            return "[blocked_group_mention]"
        return "[blocked_discord_mention]"

    return MENTION_RE.sub(replace, text), blocked


def _paths_are_relative(paths: list[str]) -> bool:
    return bool(paths) and all(path.startswith("knowledge/") and ":" not in path and not path.startswith(("/", "\\")) for path in paths)


def _message(paths: list[str], extra_text: str = "") -> tuple[str, bool, bool]:
    path_lines = "\n".join(f"- {path}" for path in paths)
    content = (
        "[REVIEW ONLY / NOT SENT]\n\n"
        "Review-only internal draft: No external action has been taken.\n"
        "This preview is scoped to the private test channel only and is not ready for Discord send.\n\n"
        "Evidence references:\n"
        f"{path_lines}\n\n"
        "Human review remains required before any live private-test send."
    )
    if extra_text:
        content += "\n" + str(extra_text)
    sanitized, mention_blocked = _sanitize_mentions(content)
    truncated = sanitized[:MAX_PREVIEW_CHARS]
    return truncated, len(sanitized) <= MAX_PREVIEW_CHARS, mention_blocked


def build_rag_evidence_would_send_preview(closeout: dict[str, Any] | None = None, extra_text: str = "") -> dict[str, Any]:
    selected_closeout = build_rag_evidence_llm_dry_call_closeout() if closeout is None else closeout
    paths = selected_closeout.get("evidence_paths", []) if isinstance(selected_closeout.get("evidence_paths"), list) else []
    source_ready = bool(selected_closeout.get("closeout_passed") and selected_closeout.get("ready_for_phase34i_private_test_would_send_preview"))
    packet_available = bool(selected_closeout.get("llm_response_packet_created"))
    output_allowed = bool(selected_closeout.get("output_safety_allowed"))
    relative_only = _paths_are_relative([str(path) for path in paths])
    if not relative_only:
        preview_text = ""
        max_enforced = True
        mention_blocked = False
    else:
        preview_text, max_enforced, mention_blocked = _message([str(path) for path in paths], extra_text=extra_text)
    created = bool(source_ready and packet_available and output_allowed and relative_only and preview_text)
    report = {
        "report_type": "rag_evidence_would_send_preview",
        "version": VERSION,
        "source_closeout_available": bool(selected_closeout),
        "llm_response_packet_available": packet_available,
        "output_safety_allowed": output_allowed,
        "private_test_channel_configured": True,
        "private_test_channel_only": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "discord_api_send_allowed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "would_send_preview_created": created,
        "would_send_channel_scope": "private_test_only",
        "would_send_message": {
            "review_only": True,
            "content_preview": preview_text,
            "content_char_count": len(preview_text),
            "max_chars_enforced": max_enforced,
            "citations": [str(path) for path in paths],
            "mention_spam_blocked_or_escaped": mention_blocked,
            "full_content_included": False,
        },
        "ready_for_phase34j_private_test_send_preflight": created,
        "ready_for_actual_discord_send": False,
        "embedding_api_called": False,
        "llm_api_called": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "llm_called": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_would_send_preview_safe(report)
    return report


def render_rag_evidence_would_send_preview_markdown(report: dict[str, Any]) -> str:
    message = report.get("would_send_message", {}) if isinstance(report.get("would_send_message"), dict) else {}
    return "\n".join(
        [
            "# STOXL RAG Evidence Would-send Preview",
            "",
            f"- Preview created: {str(report.get('would_send_preview_created')).lower()}",
            f"- Private test channel only: {str(report.get('private_test_channel_only')).lower()}",
            "- Public channel send allowed: false",
            "- Team channel send allowed: false",
            "- Discord API send allowed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            f"- Ready for Phase 34J preflight: {str(report.get('ready_for_phase34j_private_test_send_preflight')).lower()}",
            "- Ready for actual Discord send: false",
            "",
            "## Content Preview",
            str(message.get("content_preview", "")),
        ]
    ) + "\n"


def assert_rag_evidence_would_send_preview_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence would-send preview contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence would-send preview contains raw Discord-like IDs.")
    if "@everyone" in text or "@here" in text or re.search(r"<@!?\d+>|<@&\d+>", text):
        raise ValueError("RAG evidence would-send preview contains raw mention spam.")
    message = report.get("would_send_message", {}) if isinstance(report.get("would_send_message"), dict) else {}
    citations = message.get("citations", []) if isinstance(message.get("citations"), list) else []
    if not _paths_are_relative([str(path) for path in citations]):
        raise ValueError("RAG evidence would-send preview citations must be relative knowledge paths.")
    preview = str(message.get("content_preview", ""))
    if report.get("would_send_preview_created"):
        for required in ("[REVIEW ONLY / NOT SENT]", "No external action has been taken."):
            if required not in preview:
                raise ValueError(f"RAG evidence would-send preview missing marker: {required}")
        if len(preview) > MAX_PREVIEW_CHARS:
            raise ValueError("RAG evidence would-send preview exceeds max chars.")
    for key in ("public_channel_send_allowed", "team_channel_send_allowed", "discord_api_send_allowed", "discord_api_send_called", "discord_message_sent", "ready_for_actual_discord_send", "embedding_api_called", "llm_api_called", "external_execution"):
        if report.get(key):
            raise ValueError(f"RAG evidence would-send preview unsafe flag is true: {key}")
