"""Phase 36F no-send final lock for the one-shot LLM draft.

Report-only lock. It consumes the Phase 36E closeout fixture and never attempts
another LLM call, starts Discord, sends messages, creates embeddings, or
executes external actions.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any

from actual_one_shot_llm_draft_call_closeout import build_actual_one_shot_llm_draft_call_closeout


VERSION = "phase36f_one_shot_llm_no_send_final_lock"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_one_shot_llm_no_send_final_lock(closeout: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = copy.deepcopy(closeout) if closeout is not None else build_actual_one_shot_llm_draft_call_closeout()
    report = {
        "report_type": "one_shot_llm_no_send_final_lock",
        "version": VERSION,
        "final_lock_available": True,
        "report_only": True,
        "phase36d_actual_llm_draft_call_complete": bool(selected.get("phase36d_actual_llm_draft_call_complete")),
        "phase36e_closeout_passed": bool(selected.get("phase36e_closeout_passed")),
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_call_count_locked": int(selected.get("llm_api_called_count", 0) or 0),
        "discord_send_count_locked": int(selected.get("message_sent_count", 0) or 0),
        "discord_message_sent": bool(selected.get("discord_message_sent")),
        "message_sent_count": int(selected.get("message_sent_count", 0) or 0),
        "ready_for_discord_send": bool(selected.get("ready_for_discord_send")),
        "public_channel_send_allowed": bool(selected.get("public_channel_send_allowed")),
        "team_channel_send_allowed": bool(selected.get("team_channel_send_allowed")),
        "public_channel_reply_allowed": bool(selected.get("public_channel_reply_allowed")),
        "team_channel_reply_allowed": bool(selected.get("team_channel_reply_allowed")),
        "unattended_auto_reply_allowed": bool(selected.get("unattended_auto_reply_allowed")),
        "embedding_api_called": bool(selected.get("embedding_api_called")),
        "vector_index_created": bool(selected.get("vector_index_created")),
        "embedding_vector_disabled": True,
        "external_execution": bool(selected.get("external_execution")),
        "full_content_included": bool(selected.get("full_content_included")),
        "approval_phrase_generated": bool(selected.get("approval_phrase_generated")),
        "manual_approval_actualized_for_send": bool(selected.get("manual_approval_actualized_for_send")),
        "phase36_state": "actual_llm_draft_succeeded_discord_send_not_opened",
        "phase36f_no_send_final_lock_passed": False,
        "ready_for_phase37_entry_gate": False,
        "ready_for_phase37_live_execution": False,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "full_content_included": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "discord_message_sent": False,
            "public_channel_send_called": False,
            "team_channel_send_called": False,
            "llm_call_count": int(selected.get("llm_api_called_count", 0) or 0),
        },
    }
    report["phase36f_no_send_final_lock_passed"] = _passes_final_lock(report)
    report["ready_for_phase37_entry_gate"] = bool(report["phase36f_no_send_final_lock_passed"])
    assert_one_shot_llm_no_send_final_lock_safe(report)
    return report


def _passes_final_lock(report: dict[str, Any]) -> bool:
    return bool(
        report.get("phase36d_actual_llm_draft_call_complete")
        and report.get("phase36e_closeout_passed")
        and not report.get("new_llm_api_call_attempted")
        and not report.get("new_llm_api_called")
        and int(report.get("llm_call_count_locked", 0) or 0) == 1
        and int(report.get("discord_send_count_locked", 0) or 0) == 0
        and not report.get("discord_message_sent")
        and int(report.get("message_sent_count", 0) or 0) == 0
        and not report.get("ready_for_discord_send")
        and not report.get("public_channel_send_allowed")
        and not report.get("team_channel_send_allowed")
        and not report.get("public_channel_reply_allowed")
        and not report.get("team_channel_reply_allowed")
        and not report.get("unattended_auto_reply_allowed")
        and not report.get("embedding_api_called")
        and not report.get("vector_index_created")
        and report.get("embedding_vector_disabled")
        and not report.get("external_execution")
        and not report.get("full_content_included")
        and not report.get("approval_phrase_generated")
        and not report.get("manual_approval_actualized_for_send")
    )


def assert_one_shot_llm_no_send_final_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 36F final lock contains sensitive values.")
    if not report.get("phase36f_no_send_final_lock_passed"):
        raise ValueError("Phase 36F final lock did not pass.")
    if int(report.get("llm_call_count_locked", 0) or 0) != 1:
        raise ValueError("Phase 36F LLM call count must be locked to 1.")
    if int(report.get("discord_send_count_locked", 0) or 0) != 0:
        raise ValueError("Phase 36F Discord send count must be locked to 0.")
    for key in (
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "discord_message_sent",
        "ready_for_discord_send",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "full_content_included",
        "approval_phrase_generated",
        "manual_approval_actualized_for_send",
        "ready_for_phase37_live_execution",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Phase 36F unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 36F message sent count must be 0.")


def render_one_shot_llm_no_send_final_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL One-shot LLM No-send Final Lock",
            "",
            f"- Final lock passed: {str(report.get('phase36f_no_send_final_lock_passed')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            f"- LLM call count locked: {report.get('llm_call_count_locked')}",
            f"- Discord send count locked: {report.get('discord_send_count_locked')}",
            "- New LLM API call attempted: false",
            "- Discord message sent: false",
            "- Ready for Discord send: false",
            "- Public/team send/reply allowed: false",
            "- Unattended auto reply allowed: false",
            "- Embedding/vector disabled: true",
            "- External execution: false",
            f"- Ready for Phase 37 entry gate: {str(report.get('ready_for_phase37_entry_gate')).lower()}",
            "- Ready for Phase 37 live execution: false",
        ]
    ) + "\n"
