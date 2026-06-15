"""Phase 38E private-test live send entry gate, report-only."""

from __future__ import annotations

import json
import re
from typing import Any

from actual_private_test_send_contract import build_actual_private_test_send_contract
from final_would_send_payload_freeze import build_final_would_send_payload_freeze
from private_test_send_operator_checklist import build_private_test_send_operator_checklist
from private_test_send_rollback_gate import build_private_test_send_rollback_gate


VERSION = "phase38e_private_test_live_send_entry_gate_report_only"
FUTURE_MANUAL_GATE_NAMES = [
    "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED",
    "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE",
    "HERMES_DISCORD_SEND_MESSAGES",
    "HERMES_DISCORD_PRIVATE_TEST_REPLY",
    "HERMES_DISCORD_REPLY_MODE",
    "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID",
    "DISCORD_BOT_TOKEN",
]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_private_test_live_send_entry_gate(
    contract: dict[str, Any] | None = None,
    payload_freeze: dict[str, Any] | None = None,
    rollback_gate: dict[str, Any] | None = None,
    operator_checklist: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_contract = contract or build_actual_private_test_send_contract()
    selected_freeze = payload_freeze or build_final_would_send_payload_freeze(selected_contract)
    selected_rollback = rollback_gate or build_private_test_send_rollback_gate(selected_freeze)
    selected_checklist = operator_checklist or build_private_test_send_operator_checklist(selected_rollback)
    report = {
        "report_type": "private_test_live_send_entry_gate",
        "version": VERSION,
        "live_send_entry_gate_available": True,
        "report_only": True,
        "source_phase38a_contract_available": bool(selected_contract.get("contract_available")),
        "source_phase38b_payload_frozen": bool(selected_freeze.get("would_send_payload_frozen")),
        "source_phase38c_rollback_gate_available": bool(selected_rollback.get("rollback_gate_available")),
        "source_phase38d_operator_checklist_available": bool(selected_checklist.get("operator_checklist_available")),
        "actual_private_test_send_not_started": True,
        "phase39_not_started": True,
        "requires_explicit_user_approval": True,
        "future_manual_gate_names": FUTURE_MANUAL_GATE_NAMES,
        "future_send_scope": "private_test_only",
        "public_team_send_forbidden": True,
        "unattended_auto_reply_allowed": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "actual_send_implementation_executed": False,
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
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "ready_for_phase39_live_execution": False,
        "ready_for_unattended_auto_reply": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
    }
    assert_private_test_live_send_entry_gate_safe(report)
    return report


def assert_private_test_live_send_entry_gate_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    scrubbed = text
    for gate_name in FUTURE_MANUAL_GATE_NAMES:
        scrubbed = scrubbed.replace(gate_name, "")
    if SECRET_RE.search(scrubbed.lower()) or LONG_ID_RE.search(scrubbed) or APPROVAL_RE.search(scrubbed):
        raise ValueError("Phase 38E live send entry gate contains sensitive values.")
    for key in (
        "source_phase38a_contract_available",
        "source_phase38b_payload_frozen",
        "source_phase38c_rollback_gate_available",
        "source_phase38d_operator_checklist_available",
        "actual_private_test_send_not_started",
        "phase39_not_started",
        "requires_explicit_user_approval",
        "public_team_send_forbidden",
    ):
        if not report.get(key):
            raise ValueError(f"Phase 38E required flag is false: {key}")
    if report.get("future_manual_gate_names") != FUTURE_MANUAL_GATE_NAMES:
        raise ValueError("Phase 38E future gate names changed.")
    if report.get("future_send_scope") != "private_test_only":
        raise ValueError("Phase 38E future send scope must be private_test_only.")
    for key in (
        "unattended_auto_reply_allowed",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_live_runtime_executed",
        "actual_send_implementation_executed",
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
        "ready_for_phase39_live_execution",
        "ready_for_unattended_auto_reply",
        "discord_api_send_called",
        "discord_message_sent",
    ):
        if report.get(key):
            raise ValueError(f"Phase 38E unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 38E message sent count must be 0.")


def render_private_test_live_send_entry_gate_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Private-test Live Send Entry Gate",
            "",
            "- Live send entry gate available: true",
            "- Report only: true",
            "- Actual private-test send not started: true",
            "- Phase 39 not started: true",
            "- Requires explicit user approval: true",
            "- Future send scope: private_test_only",
            "- Public/team send forbidden: true",
            "- Unattended auto reply allowed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
            "- Ready for Phase 39 live execution: false",
        ]
    ) + "\n"
