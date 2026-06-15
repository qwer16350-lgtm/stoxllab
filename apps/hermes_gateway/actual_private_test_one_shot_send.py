"""Phase 39A actual private-test one-shot send path, default blocked."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from actual_private_test_send_blocked_report import build_actual_private_test_send_blocked_report
from actual_private_test_send_safety_gate import build_actual_private_test_send_safety_gate


VERSION = "phase39a_actual_private_test_one_shot_send_path_default_blocked_no_execution"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _env_flag(env: dict[str, Any], key: str) -> bool:
    return str(env.get(key, "") or "").strip().lower() == "true"


def _env_present(env: dict[str, Any], key: str) -> bool:
    return bool(str(env.get(key, "") or "").strip())


def build_actual_private_test_one_shot_send(
    *,
    allow_flag_present: bool = False,
    env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_env = env if env is not None else os.environ
    safety_gate = build_actual_private_test_send_safety_gate(allow_flag_present=allow_flag_present, env=source_env)
    blocked_report = build_actual_private_test_send_blocked_report(safety_gate)
    blocked_reasons = _blocked_reasons(safety_gate)
    report = {
        "report_type": "actual_private_test_one_shot_send",
        "version": VERSION,
        "actual_send_path_available": True,
        "report_only": True,
        "phase39a_implementation_only": True,
        "actual_private_test_send_executed": False,
        "actual_send_executed": False,
        "discord_live_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "allow_flag_present": bool(allow_flag_present),
        "manual_approval_required": True,
        "manual_approval_actualized": False,
        "approval_phrase_present": _env_present(source_env, "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE"),
        "approval_phrase_exact_match": bool(safety_gate.get("condition_values", {}).get("approval_phrase_exact_match")),
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "discord_send_messages_enabled": _env_flag(source_env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_enabled": _env_flag(source_env, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "reply_mode_private_test_only": str(source_env.get("HERMES_DISCORD_REPLY_MODE", "") or "").strip() == "private_test_only",
        "discord_token_present": _env_present(source_env, "DISCORD_BOT_TOKEN"),
        "discord_token_value_logged": False,
        "private_test_channel_id_present": _env_present(source_env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "private_test_channel_id_value_logged": False,
        "source_phase38e_live_send_entry_gate_available": bool(safety_gate.get("condition_values", {}).get("phase38e_gate_available")),
        "payload_frozen": bool(safety_gate.get("condition_values", {}).get("payload_frozen")),
        "rollback_gate_ready": bool(safety_gate.get("condition_values", {}).get("rollback_gate_ready")),
        "operator_checklist_ready": bool(safety_gate.get("condition_values", {}).get("operator_checklist_ready")),
        "send_scope": "private_test_only",
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "ready_for_phase39b_manual_one_shot_send": False,
        "blocked": True,
        "blocked_reasons": blocked_reasons,
        "source_safety_gate_available": bool(safety_gate.get("safety_gate_available")),
        "source_blocked_report_available": bool(blocked_report.get("blocked_report_available")),
    }
    assert_actual_private_test_one_shot_send_safe(report)
    return report


def _blocked_reasons(safety_gate: dict[str, Any]) -> list[str]:
    values = safety_gate.get("condition_values", {})
    reasons = []
    if not values.get("allow_flag_present"):
        reasons.append("allow_flag_missing")
    if not values.get("manual_approval_flag_true") or not values.get("approval_phrase_exact_match"):
        reasons.append("manual_approval_not_actualized")
    if not values.get("discord_send_messages_true"):
        reasons.append("discord_send_messages_disabled")
    if not values.get("private_test_reply_true"):
        reasons.append("private_test_reply_disabled")
    if not values.get("reply_mode_private_test_only"):
        reasons.append("reply_mode_not_private_test_only")
    if not values.get("discord_token_present"):
        reasons.append("discord_token_missing")
    if not values.get("private_test_channel_id_present"):
        reasons.append("private_test_channel_id_missing")
    reasons.append("phase39a_no_execution_policy")
    return reasons


def assert_actual_private_test_one_shot_send_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 39A one-shot send report contains sensitive values.")
    if not report.get("blocked"):
        raise ValueError("Phase 39A one-shot send must be blocked.")
    for key in (
        "actual_private_test_send_executed",
        "actual_send_executed",
        "discord_live_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "manual_approval_actualized",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "ready_for_actual_private_test_send",
        "ready_for_discord_send",
        "ready_for_phase39b_manual_one_shot_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39A one-shot send unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 39A one-shot send message sent count must be 0.")


def render_actual_private_test_one_shot_send_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Actual Private-test One-shot Send Path",
            "",
            "- Actual send path available: true",
            "- Report only: true",
            "- Phase 39A implementation only: true",
            "- Blocked: true",
            "- Actual private-test send executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
            "- Ready for Phase 39B manual one-shot send: false",
        ]
    ) + "\n"
