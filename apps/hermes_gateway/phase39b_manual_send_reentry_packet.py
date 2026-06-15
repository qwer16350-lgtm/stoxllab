"""Phase 39B-0 manual send re-entry packet, report-only."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase39b_manual_send_reentry_packet_report_only_no_execution"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


REQUIRED_USER_POWERSHELL_PRECONDITIONS = [
    "working_tree_clean",
    "DISCORD_BOT_TOKEN present",
    "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID present",
    "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED=true",
    "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE present and exact",
    "HERMES_DISCORD_SEND_MESSAGES=true",
    "HERMES_DISCORD_PRIVATE_TEST_REPLY=true",
    "HERMES_DISCORD_REPLY_MODE=private_test_only",
    "LLM disabled",
    "RAG disabled",
    "embedding disabled",
    "external execution disabled",
]

NEXT_PHASE_COMMAND = r"python apps\hermes_gateway\cli.py --actual-private-test-one-shot-send --json --allow-actual-private-test-send"


def build_phase39b_manual_send_reentry_packet() -> dict[str, Any]:
    report = {
        "report_type": "phase39b_manual_send_reentry_packet",
        "version": VERSION,
        "report_only": True,
        "phase39a_hotfix_allow_flag_required": True,
        "allow_flag_cli_available": True,
        "allow_flag_parser_error_fixed": True,
        "actual_send_executed": False,
        "actual_private_test_send_executed": False,
        "discord_live_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "codex_session_env_isolated_from_user_powershell": True,
        "actual_send_must_be_run_from_same_user_powershell_session": True,
        "load_dotenv_values_in_codex_session": False,
        "print_dotenv_values": False,
        "required_user_powershell_preconditions": REQUIRED_USER_POWERSHELL_PRECONDITIONS,
        "allowed_actual_send_command_for_next_phase_only": NEXT_PHASE_COMMAND,
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "secret_values_logged": False,
        "approval_phrase_generated": False,
        "manual_approval_actualized": False,
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "ready_for_phase39b_actual_send_manual_attempt": False,
        "ready_for_phase39c_send_closeout": False,
    }
    assert_phase39b_manual_send_reentry_packet_safe(report)
    return report


def assert_phase39b_manual_send_reentry_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    command = str(report.get("allowed_actual_send_command_for_next_phase_only", ""))
    text_without_command = text.replace(command, "")
    if SECRET_RE.search(text_without_command.lower()) or LONG_ID_RE.search(text_without_command) or APPROVAL_RE.search(text_without_command):
        raise ValueError("Phase 39B-0 re-entry packet contains sensitive values.")
    for key in (
        "actual_send_executed",
        "actual_private_test_send_executed",
        "discord_live_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "secret_values_logged",
        "approval_phrase_generated",
        "manual_approval_actualized",
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "ready_for_phase39b_actual_send_manual_attempt",
        "ready_for_phase39c_send_closeout",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39B-0 re-entry unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 39B-0 re-entry message sent count must be 0.")


def render_phase39b_manual_send_reentry_packet_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 39B Manual Send Re-entry Packet",
            "",
            "- Report only: true",
            "- Allow flag CLI available: true",
            "- Allow flag parser error fixed: true",
            "- Codex/user PowerShell env separated: true",
            "- Actual send must run from same user PowerShell session: true",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
            "- Ready for Phase 39B actual send manual attempt: false",
            "- Ready for Phase 39C send closeout: false",
        ]
    ) + "\n"
