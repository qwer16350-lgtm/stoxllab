"""Phase 37 entry gate after Phase 36 no-send lock."""

from __future__ import annotations

import json
import re
from typing import Any

from one_shot_llm_no_send_final_lock import build_one_shot_llm_no_send_final_lock


VERSION = "phase37_entry_gate_report_only_after_phase36_no_send_lock"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase37_entry_gate(final_lock: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = final_lock or build_one_shot_llm_no_send_final_lock()
    report = {
        "report_type": "phase37_entry_gate",
        "version": VERSION,
        "phase37_entry_gate_available": True,
        "report_only": True,
        "phase37_not_started": True,
        "requires_explicit_user_approval": True,
        "source_phase36f_no_send_final_lock_passed": bool(selected.get("phase36f_no_send_final_lock_passed")),
        "allowed_next_candidates": [
            "private_test_llm_draft_review_packet_no_send",
            "private_test_discord_send_preflight_no_send",
        ],
        "hold_candidates": [
            "actual_private_test_discord_send",
            "multi_turn_private_test_runtime",
        ],
        "forbidden_candidates": [
            "public_team_send",
            "public_team_auto_reply",
            "unattended_auto_reply",
            "external_execution",
        ],
        "ready_for_phase37_live_execution": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_live_runtime_executed": False,
        "discord_message_sent": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
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
            "llm_called": False,
        },
    }
    assert_phase37_entry_gate_safe(report)
    return report


def assert_phase37_entry_gate_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 37 entry gate contains sensitive values.")
    if not report.get("phase37_not_started"):
        raise ValueError("Phase 37 must not be started.")
    if not report.get("requires_explicit_user_approval"):
        raise ValueError("Phase 37 requires explicit user approval.")
    for key in (
        "ready_for_phase37_live_execution",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
        "llm_api_call_attempted",
        "llm_api_called",
        "discord_live_runtime_executed",
        "discord_message_sent",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase 37 entry gate unsafe flag is true: {key}")
    for required in ("public_team_send", "public_team_auto_reply", "unattended_auto_reply", "external_execution"):
        if required not in report.get("forbidden_candidates", []):
            raise ValueError(f"Phase 37 missing forbidden candidate: {required}")


def render_phase37_entry_gate_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 37 Entry Gate",
            "",
            f"- Entry gate available: {str(report.get('phase37_entry_gate_available')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            f"- Phase 37 not started: {str(report.get('phase37_not_started')).lower()}",
            f"- Requires explicit user approval: {str(report.get('requires_explicit_user_approval')).lower()}",
            f"- Source Phase 36F no-send final lock passed: {str(report.get('source_phase36f_no_send_final_lock_passed')).lower()}",
            f"- Allowed next candidates: {', '.join(report.get('allowed_next_candidates', []))}",
            f"- Hold candidates: {', '.join(report.get('hold_candidates', []))}",
            f"- Forbidden candidates: {', '.join(report.get('forbidden_candidates', []))}",
            "- Ready for Phase 37 live execution: false",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
        ]
    ) + "\n"
