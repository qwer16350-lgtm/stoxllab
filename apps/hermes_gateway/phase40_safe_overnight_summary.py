"""Phase 40I safe overnight summary, report-only."""

from __future__ import annotations

import json
import re
from typing import Any

from phase40_inbound_event_replay_dry_run import build_phase40_inbound_event_replay_dry_run
from phase40_live_runtime_entry_gate import build_phase40_live_runtime_entry_gate
from phase40_operator_handoff_packet import build_phase40_operator_handoff_packet
from phase40_outbound_queue_lock import build_phase40_outbound_queue_lock
from phase40_post_phase39_state_audit import build_phase40_post_phase39_state_audit
from phase40_private_test_runtime_plan import build_phase40_private_test_runtime_plan
from phase40_reply_decision_audit import build_phase40_reply_decision_audit
from phase40_session_idempotency_lock import build_phase40_session_idempotency_lock


VERSION = "phase40_safe_overnight_summary"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40_safe_overnight_summary() -> dict[str, Any]:
    state = build_phase40_post_phase39_state_audit()
    plan = build_phase40_private_test_runtime_plan()
    replay = build_phase40_inbound_event_replay_dry_run()
    decision = build_phase40_reply_decision_audit()
    queue = build_phase40_outbound_queue_lock()
    idempotency = build_phase40_session_idempotency_lock()
    handoff = build_phase40_operator_handoff_packet()
    entry_gate = build_phase40_live_runtime_entry_gate()
    report = {
        "report_type": "phase40_safe_overnight_summary",
        "version": VERSION,
        "report_only": True,
        "phase40_reports_completed": True,
        "phase40_report_status": {
            "post_phase39_state_audit": bool(state.get("ready_for_phase40_private_test_runtime_readiness")),
            "private_test_runtime_plan": bool(plan.get("ready_for_runtime_dry_replay")),
            "inbound_event_replay_dry_run": bool(replay.get("uses_recorded_or_synthetic_events_only")),
            "reply_decision_audit": decision.get("private_test_human_message_decision") == "eligible_for_future_manual_reply",
            "outbound_queue_lock": not bool(queue.get("outbound_queue_enabled")),
            "session_idempotency_lock": bool(idempotency.get("duplicate_message_id_guard")),
            "operator_handoff_packet": bool(handoff.get("operator_must_confirm_before_live_runtime")),
            "live_runtime_entry_gate": bool(entry_gate.get("live_runtime_entry_gate_available")),
        },
        "live_runtime_started": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "additional_discord_send_count": 0,
        "actual_discord_send_count_locked_from_phase39": int(state.get("actual_discord_send_count_locked", 0) or 0),
        "repeat_send_allowed": False,
        "automatic_retry_allowed": False,
        "unattended_auto_reply_allowed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "approval_phrase_value_logged": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "safe_to_review_next_morning": True,
        "next_human_confirmation_required": True,
        "recommended_next_phase": "Phase 40J private-test live runtime manual entry",
    }
    assert_phase40_safe_overnight_summary_safe(report)
    return report


def assert_phase40_safe_overnight_summary_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40I overnight summary contains sensitive values.")
    if report.get("actual_discord_send_count_locked_from_phase39") != 1:
        raise ValueError("Phase 40I requires Phase 39 send count locked to 1.")
    if not all(bool(value) for value in report.get("phase40_report_status", {}).values()):
        raise ValueError("Phase 40I requires all Phase 40 report statuses complete.")
    for key in (
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "unattended_auto_reply_allowed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase 40I unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0 or int(report.get("additional_discord_send_count", 0) or 0) != 0:
        raise ValueError("Phase 40I send counts must remain 0.")


def render_phase40_safe_overnight_summary_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40I Safe Overnight Summary",
            "",
            "- Report only: true",
            "- Phase 40 reports completed: true",
            "- Live runtime started: false",
            "- Additional Discord send count: 0",
            "- Actual Discord send count locked from Phase 39: 1",
            "- Safe to review next morning: true",
            "- Next human confirmation required: true",
            "- Recommended next phase: Phase 40J private-test live runtime manual entry",
        ]
    ) + "\n"
