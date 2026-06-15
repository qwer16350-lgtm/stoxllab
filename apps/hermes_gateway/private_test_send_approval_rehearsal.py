"""Phase 37C private-test send approval rehearsal.

Lists future gate names only. It never generates approval phrases, actualizes
manual approval, sends Discord messages, or calls external services.
"""

from __future__ import annotations

import json
import re
from typing import Any

from private_test_discord_send_preflight_preview import build_private_test_discord_send_preflight_preview
from private_test_llm_draft_review_packet import build_private_test_llm_draft_review_packet


VERSION = "phase37c_private_test_send_approval_rehearsal_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_VALUE_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
FUTURE_GATES = [
    "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED",
    "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE",
    "HERMES_DISCORD_SEND_MESSAGES",
    "HERMES_DISCORD_PRIVATE_TEST_REPLY",
    "HERMES_DISCORD_REPLY_MODE",
    "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID",
    "DISCORD_BOT_TOKEN",
]


def build_private_test_send_approval_rehearsal(
    review_packet: dict[str, Any] | None = None,
    send_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review = review_packet or build_private_test_llm_draft_review_packet()
    preview = send_preflight or build_private_test_discord_send_preflight_preview(review_packet=review)
    report = {
        "report_type": "private_test_send_approval_rehearsal",
        "version": VERSION,
        "approval_rehearsal_available": True,
        "report_only": True,
        "source_phase37a_review_packet_available": bool(review.get("review_packet_available")),
        "source_phase37b_send_preflight_preview_available": bool(preview.get("send_preflight_preview_available")),
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "manual_approval_actualized": False,
        "future_manual_gate_names": FUTURE_GATES,
        "future_send_scope": "private_test_only",
        "public_team_send_forbidden": True,
        "unattended_auto_reply_allowed": False,
        "ready_for_phase37d_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "ready_for_phase37_live_execution": False,
        "ready_for_unattended_auto_reply": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "approval_phrase_generated": False,
            "manual_approval_actualized": False,
            "full_content_included": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "discord_message_sent": False,
        },
    }
    assert_private_test_send_approval_rehearsal_safe(report)
    return report


def assert_private_test_send_approval_rehearsal_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    # Gate names may include *_APPROVAL_PHRASE, but actual approval phrase values
    # must not appear.
    without_gate_names = text
    for gate in FUTURE_GATES:
        without_gate_names = without_gate_names.replace(gate, "")
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_VALUE_RE.search(without_gate_names):
        raise ValueError("Phase 37C approval rehearsal contains sensitive values.")
    for key in (
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "manual_approval_actualized",
        "unattended_auto_reply_allowed",
        "ready_for_phase37d_actual_private_test_send",
        "ready_for_discord_send",
        "ready_for_phase37_live_execution",
        "ready_for_unattended_auto_reply",
        "discord_api_send_called",
        "discord_message_sent",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 37C unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 37C message sent count must be 0.")


def render_private_test_send_approval_rehearsal_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Private-test Send Approval Rehearsal",
            "",
            f"- Approval rehearsal available: {str(report.get('approval_rehearsal_available')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            "- Approval phrase generated: false",
            "- Manual approval actualized: false",
            f"- Future send scope: {report.get('future_send_scope')}",
            "- Ready for Phase 37D actual private-test send: false",
            "- Ready for Discord send: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
