"""Phase 38C private-test send rollback and kill-switch gate, no send."""

from __future__ import annotations

import json
import re
from typing import Any

from final_would_send_payload_freeze import build_final_would_send_payload_freeze


VERSION = "phase38c_private_test_send_rollback_gate_no_send"
EMERGENCY_DISABLE_GATE_NAMES = [
    "HERMES_DISCORD_SEND_MESSAGES",
    "HERMES_DISCORD_PRIVATE_TEST_REPLY",
    "HERMES_DISCORD_REPLY_MODE",
    "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED",
    "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE",
]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_private_test_send_rollback_gate(payload_freeze: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_freeze = payload_freeze or build_final_would_send_payload_freeze()
    report = {
        "report_type": "private_test_send_rollback_gate",
        "version": VERSION,
        "rollback_gate_available": True,
        "report_only": True,
        "source_phase38b_payload_frozen": bool(selected_freeze.get("would_send_payload_frozen")),
        "rollback_checklist_ready": True,
        "emergency_disable_gates_listed": True,
        "emergency_disable_gate_names": EMERGENCY_DISABLE_GATE_NAMES,
        "post_send_observation_required": True,
        "post_send_delete_or_edit_api_implemented": False,
        "post_send_delete_or_edit_api_called": False,
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
        "ready_for_operator_checklist": True,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
    }
    assert_private_test_send_rollback_gate_safe(report)
    return report


def assert_private_test_send_rollback_gate_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    scrubbed = text
    for gate_name in EMERGENCY_DISABLE_GATE_NAMES:
        scrubbed = scrubbed.replace(gate_name, "")
    if SECRET_RE.search(scrubbed.lower()) or LONG_ID_RE.search(scrubbed) or APPROVAL_RE.search(scrubbed):
        raise ValueError("Phase 38C rollback gate contains sensitive values.")
    if not report.get("source_phase38b_payload_frozen"):
        raise ValueError("Phase 38C requires Phase 38B payload freeze.")
    if report.get("emergency_disable_gate_names") != EMERGENCY_DISABLE_GATE_NAMES:
        raise ValueError("Phase 38C emergency gate names changed.")
    for key in (
        "post_send_delete_or_edit_api_implemented",
        "post_send_delete_or_edit_api_called",
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
            raise ValueError(f"Phase 38C unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 38C message sent count must be 0.")


def render_private_test_send_rollback_gate_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Private-test Send Rollback Gate",
            "",
            "- Rollback gate available: true",
            "- Report only: true",
            "- Rollback checklist ready: true",
            "- Emergency disable gates listed: true",
            "- Post-send delete/edit API implemented: false",
            "- Post-send delete/edit API called: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for operator checklist: true",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
        ]
    ) + "\n"
