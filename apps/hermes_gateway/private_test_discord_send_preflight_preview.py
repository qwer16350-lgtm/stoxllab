"""Phase 37B private-test Discord send preflight preview.

No Discord runtime is started and no API send is allowed.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from private_test_llm_draft_review_packet import build_private_test_llm_draft_review_packet


VERSION = "phase37b_private_test_discord_send_preflight_preview_no_api_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _present(env: dict[str, Any] | None, key: str) -> bool:
    source = env if env is not None else os.environ
    return bool(str(source.get(key, "") or "").strip())


def build_private_test_discord_send_preflight_preview(env: dict[str, Any] | None = None, review_packet: dict[str, Any] | None = None) -> dict[str, Any]:
    review = review_packet or build_private_test_llm_draft_review_packet()
    report = {
        "report_type": "private_test_discord_send_preflight_preview",
        "version": VERSION,
        "send_preflight_preview_available": True,
        "report_only": True,
        "source_phase37a_review_packet_available": bool(review.get("review_packet_available")),
        "private_test_scope_only": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "discord_token_present": _present(env, "DISCORD_BOT_TOKEN"),
        "discord_token_value_logged": False,
        "private_test_channel_id_present": _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "private_test_channel_id_value_logged": False,
        "would_send_preview_created": True,
        "would_send_review_only": True,
        "would_send_preview": "Review-only private-test draft preview. No external action has been taken.",
        "would_send_external_action_claim": False,
        "would_send_full_content_included": False,
        "discord_api_send_allowed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "discord_token_value_logged": False,
            "private_test_channel_id_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "full_content_included": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "discord_message_sent": False,
            "public_channel_send_called": False,
            "team_channel_send_called": False,
        },
    }
    assert_private_test_discord_send_preflight_preview_safe(report)
    return report


def assert_private_test_discord_send_preflight_preview_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 37B send preflight preview contains sensitive values.")
    for key in (
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "would_send_external_action_claim",
        "would_send_full_content_included",
        "discord_api_send_allowed",
        "discord_api_send_called",
        "discord_message_sent",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_actual_private_test_send",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Phase 37B unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 37B message sent count must be 0.")


def render_private_test_discord_send_preflight_preview_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Private-test Discord Send Preflight Preview",
            "",
            f"- Send preflight preview available: {str(report.get('send_preflight_preview_available')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            "- Private-test scope only: true",
            f"- Discord token present: {str(report.get('discord_token_present')).lower()}",
            f"- Private-test channel ID present: {str(report.get('private_test_channel_id_present')).lower()}",
            "- Discord API send allowed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
        ]
    ) + "\n"
