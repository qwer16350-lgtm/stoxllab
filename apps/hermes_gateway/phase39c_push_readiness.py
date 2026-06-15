"""Phase 39C push readiness report, report-only."""

from __future__ import annotations

import json
import re
from typing import Any

from phase39c_actual_send_closeout import build_phase39c_actual_send_closeout
from phase39c_no_repeat_send_lock import build_phase39c_no_repeat_send_lock
from phase39c_post_send_safety_audit import build_phase39c_post_send_safety_audit


VERSION = "phase39c_push_readiness_after_closeout"
BRANCH = "feature/stoxl-hermes-agent-org"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase39c_push_readiness(
    *,
    closeout: dict[str, Any] | None = None,
    no_repeat_lock: dict[str, Any] | None = None,
    safety_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_closeout = closeout or build_phase39c_actual_send_closeout()
    selected_lock = no_repeat_lock or build_phase39c_no_repeat_send_lock(selected_closeout)
    selected_audit = safety_audit or build_phase39c_post_send_safety_audit(closeout=selected_closeout, no_repeat_lock=selected_lock)
    report = {
        "report_type": "phase39c_push_readiness",
        "version": VERSION,
        "report_only": True,
        "working_tree_expected_clean_after_commit": True,
        "branch": BRANCH,
        "local_head_after_phase39c_expected": True,
        "remote_push_required": True,
        "actual_discord_send_count_locked": int(selected_lock.get("actual_discord_send_count_locked", 0) or 0),
        "phase39c_closeout_required_before_push": True,
        "phase39c_closeout_completed": bool(selected_closeout.get("phase39c_closeout_completed")),
        "phase39c_no_repeat_lock_active": bool(selected_lock.get("actual_discord_send_count_locked") == 1 and not selected_lock.get("repeat_send_allowed")),
        "phase39c_gate_off_verified": bool(selected_audit.get("gate_off_verified")),
        "push_command": f"git push origin {BRANCH}",
        "push_executed_by_codex": False,
        "discord_api_send_called_in_phase39c": False,
        "discord_message_sent_in_phase39c": False,
        "message_sent_count_in_phase39c": 0,
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "manual_retry_allowed": False,
        "ready_for_repeat_send": False,
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
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
    }
    assert_phase39c_push_readiness_safe(report)
    return report


def assert_phase39c_push_readiness_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    command = str(report.get("push_command", ""))
    scrubbed = text.replace(command, "")
    if SECRET_RE.search(scrubbed.lower()) or LONG_ID_RE.search(scrubbed) or APPROVAL_RE.search(scrubbed):
        raise ValueError("Phase 39C push readiness contains sensitive values.")
    if report.get("actual_discord_send_count_locked") != 1:
        raise ValueError("Phase 39C push readiness requires locked send count 1.")
    if not report.get("phase39c_closeout_completed") or not report.get("phase39c_no_repeat_lock_active") or not report.get("phase39c_gate_off_verified"):
        raise ValueError("Phase 39C push readiness requires closeout, no-repeat lock, and gate-off audit.")
    for key in (
        "push_executed_by_codex",
        "discord_api_send_called_in_phase39c",
        "discord_message_sent_in_phase39c",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "manual_retry_allowed",
        "ready_for_repeat_send",
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
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39C push readiness unsafe flag is true: {key}")
    if int(report.get("message_sent_count_in_phase39c", 0) or 0) != 0:
        raise ValueError("Phase 39C push readiness must not record a new message.")


def render_phase39c_push_readiness_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 39C Push Readiness",
            "",
            "- Report only: true",
            "- Branch: feature/stoxl-hermes-agent-org",
            "- Phase 39C closeout completed: true",
            "- Phase 39C no-repeat lock active: true",
            "- Gate off verified: true",
            "- Push executed by Codex: false",
            "- Push command: git push origin feature/stoxl-hermes-agent-org",
        ]
    ) + "\n"
