"""Phase 37D actual private-test send manual preflight, no send."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from private_test_discord_send_preflight_preview import build_private_test_discord_send_preflight_preview
from private_test_llm_draft_review_packet import build_private_test_llm_draft_review_packet
from private_test_send_approval_rehearsal import FUTURE_GATES, build_private_test_send_approval_rehearsal


VERSION = "phase37d_actual_private_test_send_manual_preflight_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_VALUE_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _present(env: dict[str, Any] | None, key: str) -> bool:
    source = env if env is not None else os.environ
    return bool(str(source.get(key, "") or "").strip())


def build_actual_private_test_send_manual_preflight(env: dict[str, Any] | None = None) -> dict[str, Any]:
    review = build_private_test_llm_draft_review_packet()
    preview = build_private_test_discord_send_preflight_preview(env=env, review_packet=review)
    rehearsal = build_private_test_send_approval_rehearsal(review, preview)
    report = {
        "report_type": "actual_private_test_send_manual_preflight",
        "version": VERSION,
        "preflight_available": True,
        "report_only": True,
        "source_phase37a_review_packet_available": bool(review.get("review_packet_available")),
        "source_phase37b_send_preflight_preview_available": bool(preview.get("send_preflight_preview_available")),
        "source_phase37c_approval_rehearsal_available": bool(rehearsal.get("approval_rehearsal_available")),
        "private_test_scope_only": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "discord_token_present": _present(env, "DISCORD_BOT_TOKEN"),
        "discord_token_value_logged": False,
        "private_test_channel_id_present": _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "private_test_channel_id_value_logged": False,
        "manual_approval_required": True,
        "manual_approval_actualized": False,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "future_manual_gate_names": FUTURE_GATES,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "preflight_ready_for_future_send_rehearsal": True,
        "ready_for_actual_private_test_send": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": _safety_assertions(),
    }
    assert_actual_private_test_send_manual_preflight_safe(report)
    return report


def _safety_assertions() -> dict[str, bool]:
    return {
        "api_key_value_logged": False,
        "token_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "raw_discord_ids_logged": False,
        "approval_phrase_value_logged": False,
        "approval_phrase_generated": False,
        "manual_approval_actualized": False,
        "full_content_included": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "discord_message_sent": False,
    }


def assert_actual_private_test_send_manual_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    scrubbed = text
    for gate in FUTURE_GATES:
        scrubbed = scrubbed.replace(gate, "")
    lowered = scrubbed.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(scrubbed) or APPROVAL_VALUE_RE.search(scrubbed):
        raise ValueError("Phase 37D manual preflight contains sensitive values.")
    for key in (
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "manual_approval_actualized",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_live_runtime_executed",
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
            raise ValueError(f"Phase 37D unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 37D message sent count must be 0.")


def render_actual_private_test_send_manual_preflight_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Actual Private-test Send Manual Preflight",
            "",
            f"- Preflight available: {str(report.get('preflight_available')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            "- Private-test scope only: true",
            f"- Discord token present: {str(report.get('discord_token_present')).lower()}",
            f"- Private-test channel ID present: {str(report.get('private_test_channel_id_present')).lower()}",
            "- Manual approval required: true",
            "- Manual approval actualized: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
        ]
    ) + "\n"
