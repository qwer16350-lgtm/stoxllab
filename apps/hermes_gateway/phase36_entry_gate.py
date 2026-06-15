"""Phase 36 entry gate preview.

This is a report-only gate. Phase 36 is not started by this module.
"""

from __future__ import annotations

import json
import re
from typing import Any

from forbidden_behavior_sentinel import build_forbidden_behavior_sentinel
from operations_dashboard_lock import build_operations_dashboard_lock


VERSION = "phase36_entry_gate_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase36_entry_gate() -> dict[str, Any]:
    dashboard = build_operations_dashboard_lock()
    sentinel = build_forbidden_behavior_sentinel()
    report = {
        "report_type": "phase36_entry_gate",
        "version": VERSION,
        "phase36_entry_gate_available": True,
        "report_only": True,
        "phase36_not_started": True,
        "requires_explicit_user_approval": True,
        "ready_for_phase36_live_execution": False,
        "ready_for_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "ready_for_unattended_auto_reply": False,
        "dashboard_lock_available": bool(dashboard.get("dashboard_lock_available")),
        "forbidden_behavior_sentinel_passed": bool(sentinel.get("forbidden_behavior_sentinel_passed")),
        "allowed_next_candidates": [
            "private_test_one_shot_llm_draft_preflight_no_send",
            "agent_review_packet_to_llm_draft_preview_no_send",
        ],
        "hold_candidates": [
            "private_test_multi_turn_runtime",
            "embedding_vector_db",
            "scheduler",
        ],
        "forbidden_candidates": [
            "public_team_auto_reply",
            "unattended_auto_reply",
            "external_execution",
        ],
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "approval_phrase_generated": False,
            "live_runtime_executed": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
        },
    }
    assert_phase36_entry_gate_safe(report)
    return report


def assert_phase36_entry_gate_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 36 entry gate contains sensitive values.")
    for key in (
        "ready_for_phase36_live_execution",
        "ready_for_llm_call",
        "ready_for_discord_send",
        "ready_for_embedding",
        "ready_for_external_sources",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Phase 36 entry gate unsafe flag is true: {key}")


def render_phase36_entry_gate_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 36 Entry Gate",
            "",
            "- Phase 36 entry gate available: true",
            "- Phase 36 not started: true",
            "- Requires explicit user approval: true",
            "- Ready for Phase 36 live execution: false",
            "- Ready for LLM call: false",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
            f"- Allowed next candidates: {len(report.get('allowed_next_candidates', []))}",
            f"- Hold candidates: {len(report.get('hold_candidates', []))}",
            f"- Forbidden candidates: {len(report.get('forbidden_candidates', []))}",
        ]
    ) + "\n"
