"""Phase 35G forbidden behavior sentinel.

Report-only guardrail sentinel. It never runs Discord, sends messages, calls
LLMs, creates embeddings/vector indexes, or executes external actions.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase35g_forbidden_behavior_sentinel_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
FORBIDDEN_TRUE_FIELDS = (
    "public_channel_reply_allowed",
    "team_channel_reply_allowed",
    "public_channel_send_allowed",
    "team_channel_send_allowed",
    "unattended_auto_reply_allowed",
    "scheduler_auto_reply_allowed",
    "embedding_api_called",
    "vector_index_created",
    "external_execution",
    "full_content_included",
    "approval_phrase_generated",
    "discord_api_send_called",
    "actual_private_test_send_executed",
    "actual_send_implementation_executed",
    "new_llm_api_call_attempted",
    "new_llm_api_called",
    "llm_api_call_attempted",
    "llm_api_called",
    "discord_live_runtime_executed",
    "ready_for_discord_send",
    "ready_for_actual_private_test_send",
    "ready_for_phase37d_actual_private_test_send",
    "ready_for_phase38_actual_private_test_send_path",
    "ready_for_phase39_live_execution",
    "ready_for_phase39b_manual_one_shot_send",
    "actual_discord_api_send_called",
    "actual_discord_message_sent",
    "api_key_value_logged",
    "token_value_logged",
    "discord_token_value_logged",
    "private_test_channel_id_value_logged",
    "raw_discord_ids_logged",
    "approval_phrase_value_logged",
)


def build_forbidden_behavior_sentinel(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_type": "forbidden_behavior_sentinel",
        "version": VERSION,
        "sentinel_available": True,
        "report_only": True,
        "live_runtime_executed": False,
        "llm_called": False,
        "discord_message_sent": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "unattended_auto_reply_allowed": False,
        "scheduler_auto_reply_allowed": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "full_content_included": False,
        "approval_phrase_generated": False,
        "discord_api_send_called": False,
        "actual_private_test_send_executed": False,
        "actual_send_implementation_executed": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "ready_for_discord_send": False,
        "ready_for_actual_private_test_send": False,
        "ready_for_phase37d_actual_private_test_send": False,
        "ready_for_phase38_actual_private_test_send_path": False,
        "ready_for_phase39_live_execution": False,
        "ready_for_phase39b_manual_one_shot_send": False,
        "actual_discord_api_send_called": False,
        "actual_discord_message_sent": False,
        "actual_message_sent_count": 0,
        "api_key_value_logged": False,
        "token_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "raw_discord_ids_logged": False,
        "approval_phrase_value_logged": False,
        "post_llm_call_sentinel": False,
        "total_phase36_llm_call_count": 1,
        "total_phase36_discord_message_sent_count": 0,
        "phase36_discord_message_sent": False,
        "public_team_blocked": True,
        "embedding_vector_disabled": True,
        "forbidden_behavior_sentinel_passed": True,
    }
    if overrides:
        report.update(overrides)
    report["public_team_blocked"] = not any(
        bool(report.get(key))
        for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed")
    )
    report["embedding_vector_disabled"] = not (bool(report.get("embedding_api_called")) or bool(report.get("vector_index_created")))
    report["forbidden_behavior_sentinel_passed"] = _sentinel_passed(report)
    assert_forbidden_behavior_sentinel_safe(report)
    return report


def _sentinel_passed(report: dict[str, Any]) -> bool:
    if any(bool(report.get(key)) for key in FORBIDDEN_TRUE_FIELDS):
        return False
    if bool(report.get("post_llm_call_sentinel")):
        if int(report.get("total_phase36_llm_call_count", 0) or 0) != 1:
            return False
        if int(report.get("total_phase36_discord_message_sent_count", 0) or 0) != 0:
            return False
        if report.get("phase36_discord_message_sent"):
            return False
    if int(report.get("actual_message_sent_count", 0) or 0) != 0:
        return False
    return True


def assert_forbidden_behavior_sentinel_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Forbidden behavior sentinel contains sensitive values.")
    if not report.get("forbidden_behavior_sentinel_passed"):
        raise ValueError("Forbidden behavior sentinel failed.")
    for key in FORBIDDEN_TRUE_FIELDS:
        if report.get(key):
            raise ValueError(f"Forbidden behavior enabled: {key}")
    if bool(report.get("post_llm_call_sentinel")):
        if int(report.get("total_phase36_llm_call_count", 0) or 0) != 1:
            raise ValueError("Post-LLM sentinel requires Phase 36 LLM call count exactly 1.")
        if int(report.get("total_phase36_discord_message_sent_count", 0) or 0) != 0:
            raise ValueError("Post-LLM sentinel requires Phase 36 Discord message count 0.")
        if report.get("phase36_discord_message_sent"):
            raise ValueError("Post-LLM sentinel requires Phase 36 Discord message sent false.")
    if int(report.get("actual_message_sent_count", 0) or 0) != 0:
        raise ValueError("Forbidden behavior sentinel requires actual message sent count 0.")


def render_forbidden_behavior_sentinel_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Forbidden Behavior Sentinel",
            "",
            "- Sentinel available: true",
            "- Report only: true",
            "- Public/team blocked: true",
            "- Unattended auto reply allowed: false",
            "- Scheduler auto reply allowed: false",
            "- Embedding/vector disabled: true",
            "- External execution: false",
            "- Full content included: false",
            "- Approval phrase generated: false",
            "- Forbidden behavior sentinel passed: true",
        ]
    ) + "\n"
