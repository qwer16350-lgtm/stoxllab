"""Phase 39A actual private-test send safety gate, no execution."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from final_would_send_payload_freeze import build_final_would_send_payload_freeze
from private_test_live_send_entry_gate import build_private_test_live_send_entry_gate
from private_test_send_operator_checklist import build_private_test_send_operator_checklist
from private_test_send_rollback_gate import build_private_test_send_rollback_gate


VERSION = "phase39a_actual_private_test_send_safety_gate_no_execution"
PHASE39B_READY_VERSION = "phase39b_manual_actual_private_test_send_ready_gate"
REQUIRED_CONDITIONS = [
    "allow_flag_present",
    "manual_approval_flag_true",
    "approval_phrase_exact_match",
    "discord_send_messages_true",
    "private_test_reply_true",
    "reply_mode_private_test_only",
    "discord_token_present",
    "private_test_channel_id_present",
    "phase38e_gate_available",
    "payload_frozen",
    "rollback_gate_ready",
    "operator_checklist_ready",
    "private_test_scope_only",
    "public_team_forbidden",
    "unattended_false",
]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
EXPECTED_APPROVAL_PHRASE = "I_APPROVE_ONE_PRIVATE_TEST_DRAFT_SEND_PRIVATE_TEST_ONLY_ONCE"


def _env_flag(env: dict[str, Any], key: str) -> bool:
    return str(env.get(key, "") or "").strip().lower() == "true"


def _env_present(env: dict[str, Any], key: str) -> bool:
    return bool(str(env.get(key, "") or "").strip())


def build_actual_private_test_send_safety_gate(
    *,
    allow_flag_present: bool = False,
    env: dict[str, Any] | None = None,
    phase38e_gate: dict[str, Any] | None = None,
    payload_freeze: dict[str, Any] | None = None,
    rollback_gate: dict[str, Any] | None = None,
    operator_checklist: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_env = env if env is not None else os.environ
    selected_gate = phase38e_gate or build_private_test_live_send_entry_gate()
    selected_freeze = payload_freeze or build_final_would_send_payload_freeze()
    selected_rollback = rollback_gate or build_private_test_send_rollback_gate(selected_freeze)
    selected_checklist = operator_checklist or build_private_test_send_operator_checklist(selected_rollback)
    approval_phrase = str(source_env.get("HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE", "") or "")
    condition_values = {
        "allow_flag_present": bool(allow_flag_present),
        "manual_approval_flag_true": _env_flag(source_env, "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED"),
        "approval_phrase_exact_match": approval_phrase == EXPECTED_APPROVAL_PHRASE,
        "discord_send_messages_true": _env_flag(source_env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_true": _env_flag(source_env, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "reply_mode_private_test_only": str(source_env.get("HERMES_DISCORD_REPLY_MODE", "") or "").strip() == "private_test_only",
        "discord_token_present": _env_present(source_env, "DISCORD_BOT_TOKEN"),
        "private_test_channel_id_present": _env_present(source_env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "phase38e_gate_available": bool(selected_gate.get("live_send_entry_gate_available")),
        "payload_frozen": bool(selected_freeze.get("would_send_payload_frozen")),
        "rollback_gate_ready": bool(selected_rollback.get("rollback_checklist_ready")),
        "operator_checklist_ready": bool(selected_checklist.get("operator_checklist_ready")),
        "private_test_scope_only": selected_gate.get("future_send_scope") == "private_test_only",
        "public_team_forbidden": bool(selected_gate.get("public_team_send_forbidden")),
        "unattended_false": not bool(selected_gate.get("unattended_auto_reply_allowed")),
    }
    raw_required_conditions_met = all(condition_values.get(key) for key in REQUIRED_CONDITIONS)
    report = {
        "report_type": "actual_private_test_send_safety_gate",
        "version": VERSION,
        "safety_gate_available": True,
        "report_only": True,
        "expected_approval_phrase_documented": True,
        "required_conditions": REQUIRED_CONDITIONS,
        "condition_values": condition_values,
        "raw_required_conditions_met": raw_required_conditions_met,
        "conditions_met": False,
        "actual_send_allowed": False,
        "actual_send_executed": False,
        "actual_private_test_send_executed": False,
        "discord_live_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "secret_values_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "approval_phrase_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "approval_phrase_generated": False,
        "manual_approval_actualized": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "ready_for_phase39b_manual_one_shot_send": False,
    }
    assert_actual_private_test_send_safety_gate_safe(report)
    return report


def assert_actual_private_test_send_safety_gate_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    scrubbed = text.replace(EXPECTED_APPROVAL_PHRASE, "")
    if SECRET_RE.search(scrubbed.lower()) or LONG_ID_RE.search(scrubbed) or APPROVAL_RE.search(scrubbed):
        raise ValueError("Phase 39A safety gate contains sensitive values.")
    if report.get("required_conditions") != REQUIRED_CONDITIONS:
        raise ValueError("Phase 39A required conditions changed.")
    if report.get("actual_send_allowed") or report.get("conditions_met"):
        raise ValueError("Phase 39A must not allow actual send.")
    for key in (
        "actual_send_executed",
        "actual_private_test_send_executed",
        "discord_live_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "secret_values_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "approval_phrase_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "approval_phrase_generated",
        "manual_approval_actualized",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_actual_private_test_send",
        "ready_for_discord_send",
        "ready_for_phase39b_manual_one_shot_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39A safety gate unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 39A safety gate message sent count must be 0.")


def render_actual_private_test_send_safety_gate_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Actual Private-test Send Safety Gate",
            "",
            "- Safety gate available: true",
            "- Report only: true",
            f"- Conditions met: {str(report.get('conditions_met')).lower()}",
            "- Actual send allowed: false",
            "- Actual send executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for Phase 39B manual one-shot send: false",
        ]
    ) + "\n"
