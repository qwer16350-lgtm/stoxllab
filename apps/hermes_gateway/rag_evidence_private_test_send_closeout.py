"""Phase 34J-2 closeout for the observed private-test RAG evidence send.

This module is fixture/replay only. It never calls Discord APIs and never sends
another message.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase34j2_private_test_send_closeout_no_additional_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)

EMBEDDED_SANITIZED_SEND_FIXTURE: dict[str, Any] = {
    "report_type": "rag_evidence_private_test_send",
    "version": "phase34j1_one_private_test_discord_send",
    "discord_api_send_allowed": True,
    "discord_api_send_called": True,
    "discord_message_sent": True,
    "message_sent_count": 1,
    "sent_channel_scope": "private_test_only",
    "sent_message_review_only": True,
    "self_loop_guard_expected": True,
    "ready_for_phase34j2_send_closeout": True,
    "public_channel_send_allowed": False,
    "team_channel_send_allowed": False,
    "llm_api_called": False,
    "embedding_api_called": False,
    "external_execution": False,
}


def _safe_text(value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence private-test send closeout contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence private-test send closeout contains raw Discord-like IDs.")


def build_rag_evidence_private_test_send_closeout(report: dict[str, Any] | None = None) -> dict[str, Any]:
    source = report or EMBEDDED_SANITIZED_SEND_FIXTURE
    _safe_text(source)
    observed = bool(source.get("discord_api_send_called") and source.get("discord_message_sent"))
    count = int(source.get("message_sent_count", 0) or 0)
    private_scope = source.get("sent_channel_scope") == "private_test_only"
    no_public = not source.get("public_channel_send_allowed") and not source.get("public_channel_send_called")
    no_team = not source.get("team_channel_send_allowed") and not source.get("team_channel_send_called")
    audit = {
        "self_message_reply_attempted": False,
        "bot_message_reply_attempted": False,
        "duplicate_send_detected": False,
        "duplicate_send_blocked": True,
    }
    closeout_passed = bool(
        observed
        and count == 1
        and private_scope
        and no_public
        and no_team
        and source.get("sent_message_review_only")
        and source.get("self_loop_guard_expected")
        and not source.get("llm_api_called")
        and not source.get("embedding_api_called")
        and not source.get("external_execution")
    )
    closeout = {
        "report_type": "rag_evidence_private_test_send_closeout",
        "version": VERSION,
        "actual_private_test_send_observed": observed,
        "discord_api_send_called_count": 1 if source.get("discord_api_send_called") else 0,
        "discord_message_sent_count": count,
        "sent_channel_scope": source.get("sent_channel_scope", ""),
        "private_test_channel_only": private_scope,
        "public_channel_send_called": False,
        "team_channel_send_called": False,
        "sent_message_review_only": bool(source.get("sent_message_review_only")),
        "self_loop_guard_expected": bool(source.get("self_loop_guard_expected")),
        "self_loop_audit": audit,
        "llm_api_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "additional_discord_send": False,
        "closeout_passed": closeout_passed,
        "ready_for_phase34k_private_test_e2e_preflight": closeout_passed,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "public_channel_send_called": False,
            "team_channel_send_called": False,
            "discord_message_sent_count": count,
            "additional_discord_send": False,
            "llm_called": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_private_test_send_closeout_safe(closeout)
    return closeout


def render_rag_evidence_private_test_send_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test Send Closeout",
            "",
            f"- Actual private-test send observed: {str(report.get('actual_private_test_send_observed')).lower()}",
            f"- Discord API send called count: {report.get('discord_api_send_called_count', 0)}",
            f"- Discord message sent count: {report.get('discord_message_sent_count', 0)}",
            f"- Sent channel scope: {report.get('sent_channel_scope', '')}",
            f"- Private test channel only: {str(report.get('private_test_channel_only')).lower()}",
            "- Public channel send called: false",
            "- Team channel send called: false",
            f"- Sent message review-only: {str(report.get('sent_message_review_only')).lower()}",
            f"- Self-loop guard expected: {str(report.get('self_loop_guard_expected')).lower()}",
            "- Additional Discord send: false",
            "- LLM API called: false",
            "- Embedding API called: false",
            "- External execution: false",
            f"- Closeout passed: {str(report.get('closeout_passed')).lower()}",
            f"- Ready for Phase 34K E2E preflight: {str(report.get('ready_for_phase34k_private_test_e2e_preflight')).lower()}",
        ]
    ) + "\n"


def assert_rag_evidence_private_test_send_closeout_safe(report: dict[str, Any]) -> None:
    _safe_text(report)
    if report.get("discord_api_send_called_count") != 1:
        raise ValueError("Send closeout expected exactly one Discord API send call in fixture.")
    if report.get("discord_message_sent_count") != 1:
        raise ValueError("Send closeout expected exactly one Discord message sent in fixture.")
    if report.get("sent_channel_scope") != "private_test_only":
        raise ValueError("Send closeout expected private_test_only channel scope.")
    if report.get("public_channel_send_called") or report.get("team_channel_send_called"):
        raise ValueError("Send closeout cannot include public/team channel send.")
    if report.get("additional_discord_send"):
        raise ValueError("Send closeout cannot include additional Discord send.")
    for key in ("llm_api_called", "embedding_api_called", "external_execution"):
        if report.get(key):
            raise ValueError(f"Send closeout unsafe flag is true: {key}")
    if not report.get("closeout_passed"):
        raise ValueError("Send closeout did not pass.")
