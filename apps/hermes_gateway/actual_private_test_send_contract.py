"""Phase 38A actual private-test send contract, no send."""

from __future__ import annotations

import json
import re
from typing import Any

from private_test_send_no_send_lock import build_private_test_send_no_send_lock


VERSION = "phase38a_actual_private_test_send_contract_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_actual_private_test_send_contract(lock: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_lock = lock or build_private_test_send_no_send_lock()
    report = {
        "report_type": "actual_private_test_send_contract",
        "version": VERSION,
        "contract_available": True,
        "report_only": True,
        "source_phase37f_no_send_lock_passed": bool(selected_lock.get("phase37f_no_send_lock_passed")),
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "actual_send_implementation_executed": False,
        "discord_live_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "send_scope": "private_test_only",
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "manual_approval_required_for_future_send": True,
        "manual_approval_actualized": False,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_payload_freeze": True,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "ready_for_phase38_live_execution": False,
    }
    assert_actual_private_test_send_contract_safe(report)
    return report


def assert_actual_private_test_send_contract_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 38A contract contains sensitive values.")
    if not report.get("source_phase37f_no_send_lock_passed"):
        raise ValueError("Phase 38A contract requires Phase 37F no-send lock.")
    if report.get("send_scope") != "private_test_only":
        raise ValueError("Phase 38A send scope must be private_test_only.")
    for key in (
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "actual_send_implementation_executed",
        "discord_live_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "manual_approval_actualized",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
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
        "ready_for_phase38_live_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 38A unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 38A message sent count must be 0.")


def render_actual_private_test_send_contract_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Actual Private-test Send Contract",
            "",
            "- Contract available: true",
            "- Report only: true",
            f"- Source Phase 37F no-send lock passed: {str(report.get('source_phase37f_no_send_lock_passed')).lower()}",
            "- Send scope: private_test_only",
            "- Actual send implementation executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for payload freeze: true",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
            "- Ready for Phase 38 live execution: false",
        ]
    ) + "\n"
