"""Phase 40Z operations handoff summary for Phase 41 preparation."""

from __future__ import annotations

from typing import Any, Mapping

from phase40u_readonly_live_connection_closeout import build_phase40u_readonly_live_connection_closeout
from phase40v_capture_review_closeout import build_phase40v_capture_review_closeout
from phase40w_synthetic_private_test_replay import build_phase40w_synthetic_private_test_replay
from phase40x_reply_decision_dry_run import build_phase40x_reply_decision_dry_run
from phase40y_phase41_reply_preflight_gate import build_phase40y_phase41_reply_preflight_gate


def build_phase40z_operations_handoff() -> dict[str, Any]:
    closeout = build_phase40u_readonly_live_connection_closeout()
    capture = build_phase40v_capture_review_closeout()
    synthetic = build_phase40w_synthetic_private_test_replay()
    dry_run = build_phase40x_reply_decision_dry_run()
    gate = build_phase40y_phase41_reply_preflight_gate()
    report = {
        "report_type": "phase40z_operations_handoff",
        "version": "phase40z_operations_handoff",
        "report_only": True,
        "phase40t_gateway_connect_verified": bool(closeout.get("gateway_connect_verified")),
        "phase40u_closeout_ready": bool(closeout.get("ready_for_phase41_dry_run_preparation")),
        "phase40v_capture_review_ready": bool(capture.get("capture_valid")),
        "phase40w_synthetic_fixture_ready": bool(synthetic.get("synthetic_fixture_available")),
        "phase40x_reply_dry_run_ready": bool(dry_run.get("ready_for_phase41_preflight_gate")),
        "phase41_actual_reply_default_blocked": bool(gate.get("default_blocked")),
        "ready_for_actual_reply_send": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "public_team_blocked": True,
        "unattended_auto_reply_allowed": False,
        "next_manual_step": "separate_phase41_manual_private_test_reply_approval",
    }
    assert_phase40z_operations_handoff_safe(report)
    return report


def assert_phase40z_operations_handoff_safe(report: Mapping[str, Any]) -> None:
    for key in ("ready_for_actual_reply_send", "discord_api_send_called", "discord_message_sent", "llm_called", "rag_called", "embedding_api_called", "external_execution", "unattended_auto_reply_allowed"):
        if report.get(key):
            raise ValueError(f"Phase 40Z unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40Z message_sent_count must remain 0.")


def render_phase40z_operations_handoff_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40Z Operations Handoff",
            "",
            f"- Gateway connect verified: {str(report.get('phase40t_gateway_connect_verified')).lower()}",
            f"- Phase 40U closeout ready: {str(report.get('phase40u_closeout_ready')).lower()}",
            f"- Phase 40X reply dry-run ready: {str(report.get('phase40x_reply_dry_run_ready')).lower()}",
            "- Phase 41 actual reply default blocked: true",
            "- Ready for actual reply send: false",
        ]
    ) + "\n"
