"""Phase 36G post-LLM-call dashboard lock."""

from __future__ import annotations

import copy
import json
import re
from typing import Any

from forbidden_behavior_sentinel import build_forbidden_behavior_sentinel
from one_shot_llm_no_send_final_lock import build_one_shot_llm_no_send_final_lock


VERSION = "phase36g_post_llm_call_dashboard_lock"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_post_llm_call_dashboard_lock(final_lock: dict[str, Any] | None = None, sentinel_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = copy.deepcopy(final_lock) if final_lock is not None else build_one_shot_llm_no_send_final_lock()
    sentinel = build_forbidden_behavior_sentinel(
        {
            "post_llm_call_sentinel": True,
            "total_phase36_llm_call_count": int(selected.get("llm_call_count_locked", 0) or 0),
            "total_phase36_discord_message_sent_count": int(selected.get("discord_send_count_locked", 0) or 0),
            **(sentinel_overrides or {}),
        }
    )
    report = {
        "report_type": "post_llm_call_dashboard_lock",
        "version": VERSION,
        "dashboard_lock_available": True,
        "report_only": True,
        "phase36d_actual_llm_draft_call_complete": bool(selected.get("phase36d_actual_llm_draft_call_complete")),
        "phase36e_closeout_passed": bool(selected.get("phase36e_closeout_passed")),
        "phase36f_no_send_final_lock_passed": bool(selected.get("phase36f_no_send_final_lock_passed")),
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "total_phase36_llm_call_count": int(selected.get("llm_call_count_locked", 0) or 0),
        "total_phase36_discord_message_sent_count": int(selected.get("discord_send_count_locked", 0) or 0),
        "sent_channel_scope": "none",
        "output_safety_allowed": True,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "forbidden_behavior_sentinel_passed": bool(sentinel.get("forbidden_behavior_sentinel_passed")),
        "ready_for_phase37_entry_gate": False,
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
            "llm_call_count": int(selected.get("llm_call_count_locked", 0) or 0),
        },
    }
    report["ready_for_phase37_entry_gate"] = _passes_dashboard_lock(report)
    assert_post_llm_call_dashboard_lock_safe(report)
    return report


def _passes_dashboard_lock(report: dict[str, Any]) -> bool:
    safety = report.get("safety_assertions", {})
    return bool(
        report.get("phase36d_actual_llm_draft_call_complete")
        and report.get("phase36e_closeout_passed")
        and report.get("phase36f_no_send_final_lock_passed")
        and not report.get("new_llm_api_call_attempted")
        and not report.get("new_llm_api_called")
        and int(report.get("total_phase36_llm_call_count", 0) or 0) == 1
        and int(report.get("total_phase36_discord_message_sent_count", 0) or 0) == 0
        and report.get("sent_channel_scope") == "none"
        and report.get("output_safety_allowed")
        and not report.get("ready_for_discord_send")
        and not report.get("ready_for_unattended_auto_reply")
        and report.get("forbidden_behavior_sentinel_passed")
        and not any(
            bool(safety.get(key))
            for key in (
                "api_key_value_logged",
                "token_value_logged",
                "raw_discord_ids_logged",
                "approval_phrase_value_logged",
                "full_content_included",
                "embedding_called",
                "vector_index_created",
                "external_execution",
                "discord_message_sent",
                "public_channel_send_called",
                "team_channel_send_called",
            )
        )
    )


def assert_post_llm_call_dashboard_lock_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 36G dashboard lock contains sensitive values.")
    if not report.get("ready_for_phase37_entry_gate"):
        raise ValueError("Phase 36G dashboard lock did not pass.")
    if int(report.get("total_phase36_llm_call_count", 0) or 0) != 1:
        raise ValueError("Phase 36G LLM call count must be exactly 1.")
    if int(report.get("total_phase36_discord_message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 36G Discord message count must be 0.")
    for key in ("new_llm_api_call_attempted", "new_llm_api_called", "ready_for_discord_send", "ready_for_unattended_auto_reply"):
        if report.get(key):
            raise ValueError(f"Phase 36G unsafe flag is true: {key}")
    safety = report.get("safety_assertions", {})
    for key, value in safety.items():
        if key != "llm_call_count" and value:
            raise ValueError(f"Phase 36G unsafe assertion is true: {key}")


def render_post_llm_call_dashboard_lock_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Post-LLM-call Dashboard Lock",
            "",
            f"- Dashboard lock available: {str(report.get('dashboard_lock_available')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            f"- Phase 36F no-send final lock passed: {str(report.get('phase36f_no_send_final_lock_passed')).lower()}",
            f"- Total Phase 36 LLM call count: {report.get('total_phase36_llm_call_count')}",
            f"- Total Phase 36 Discord message count: {report.get('total_phase36_discord_message_sent_count')}",
            f"- Sent channel scope: {report.get('sent_channel_scope')}",
            f"- Output safety allowed: {str(report.get('output_safety_allowed')).lower()}",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
            f"- Forbidden behavior sentinel passed: {str(report.get('forbidden_behavior_sentinel_passed')).lower()}",
            f"- Ready for Phase 37 entry gate: {str(report.get('ready_for_phase37_entry_gate')).lower()}",
        ]
    ) + "\n"
