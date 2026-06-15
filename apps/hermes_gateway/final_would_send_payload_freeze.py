"""Phase 38B final would-send payload freeze, no send."""

from __future__ import annotations

import json
import re
from typing import Any

from actual_private_test_send_contract import build_actual_private_test_send_contract
from private_test_llm_draft_review_packet import build_private_test_llm_draft_review_packet


VERSION = "phase38b_final_would_send_payload_freeze_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_final_would_send_payload_freeze(
    contract: dict[str, Any] | None = None,
    review_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_contract = contract or build_actual_private_test_send_contract()
    selected_review = review_packet or build_private_test_llm_draft_review_packet()
    report = {
        "report_type": "final_would_send_payload_freeze",
        "version": VERSION,
        "payload_freeze_available": True,
        "report_only": True,
        "source_phase38a_contract_available": bool(selected_contract.get("contract_available")),
        "source_phase37a_review_packet_available": bool(selected_review.get("review_packet_available")),
        "would_send_payload_created": True,
        "would_send_payload_frozen": True,
        "would_send_payload_scope": "private_test_only",
        "would_send_review_only": True,
        "would_send_external_action_claim": False,
        "would_send_full_content_included": False,
        "safe_disclaimer_required": True,
        "safe_disclaimer_present": True,
        "payload_preview": "Review-only private-test payload preview. No external action has been taken.",
        "payload_contains_api_key": False,
        "payload_contains_token": False,
        "payload_contains_raw_discord_id": False,
        "payload_contains_private_channel_id_value": False,
        "payload_contains_approval_phrase_value": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "actual_send_implementation_executed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "manual_approval_actualized": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_rollback_gate": True,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
    }
    assert_final_would_send_payload_freeze_safe(report)
    return report


def assert_final_would_send_payload_freeze_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 38B payload freeze contains sensitive values.")
    if not report.get("source_phase38a_contract_available") or not report.get("source_phase37a_review_packet_available"):
        raise ValueError("Phase 38B requires Phase 38A contract and Phase 37A review packet.")
    if report.get("would_send_payload_scope") != "private_test_only":
        raise ValueError("Phase 38B payload must remain private_test_only.")
    if "No external action has been taken." not in str(report.get("payload_preview", "")):
        raise ValueError("Phase 38B payload must include the safe disclaimer.")
    for key in (
        "would_send_external_action_claim",
        "would_send_full_content_included",
        "payload_contains_api_key",
        "payload_contains_token",
        "payload_contains_raw_discord_id",
        "payload_contains_private_channel_id_value",
        "payload_contains_approval_phrase_value",
        "discord_api_send_called",
        "discord_message_sent",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_live_runtime_executed",
        "actual_send_implementation_executed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "manual_approval_actualized",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_actual_private_test_send",
        "ready_for_discord_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 38B unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 38B message sent count must be 0.")


def render_final_would_send_payload_freeze_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Final Would-send Payload Freeze",
            "",
            "- Payload freeze available: true",
            "- Report only: true",
            "- Would-send payload frozen: true",
            "- Would-send review only: true",
            "- Safe disclaimer present: true",
            "- Full content included: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for rollback gate: true",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
        ]
    ) + "\n"
