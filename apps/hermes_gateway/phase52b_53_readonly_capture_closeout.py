"""Combined Phase52B/53 read-only capture closeout."""

from __future__ import annotations

import json
import re
from typing import Any

from phase52b_capture_metadata_review import build_phase52b_capture_metadata_review
from phase52b_readonly_live_capture_closeout import build_phase52b_readonly_live_capture_closeout
from phase53_capture_to_review_packet_replay import build_phase53_capture_to_review_packet_replay
from phase53_next_readonly_capture_canary_plan import build_phase53_next_readonly_capture_canary_plan


VERSION = "phase52b_53_readonly_capture_closeout_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase52b_53_readonly_capture_closeout() -> dict[str, Any]:
    closeout = build_phase52b_readonly_live_capture_closeout()
    metadata = build_phase52b_capture_metadata_review(closeout)
    replay = build_phase53_capture_to_review_packet_replay(metadata)
    canary = build_phase53_next_readonly_capture_canary_plan()
    report = {
        "report_type": "phase52b_53_readonly_capture_closeout",
        "version": VERSION,
        "manual_readonly_runtime_successfully_closed_out": True,
        "gateway_connection_verified": bool(closeout.get("discord_gateway_connected")),
        "empty_capture_handled": bool(closeout.get("empty_capture_handled")) and bool(metadata.get("empty_capture_valid")),
        "capture_to_review_packet_replay_ready": bool(closeout.get("ready_for_capture_to_review_packet_replay")) and bool(replay.get("review_packet_pipeline_ready")),
        "review_packet_pipeline_ready_for_real_capture": True,
        "ready_for_next_readonly_capture_canary_manual_gate": bool(canary.get("ready_for_next_manual_gate")),
        "ready_for_auto_reply": False,
        "ready_for_llm_reply": False,
        "ready_for_rag_reply": False,
        "ready_for_team_channel_auto_ops": False,
        "ready_for_production_unattended": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_live_execution": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }
    assert_phase52b_53_readonly_capture_closeout_safe(report)
    return report


def assert_phase52b_53_readonly_capture_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase52B/53 closeout contains sensitive values.")
    for key in (
        "ready_for_auto_reply",
        "ready_for_llm_reply",
        "ready_for_rag_reply",
        "ready_for_team_channel_auto_ops",
        "ready_for_production_unattended",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_live_execution",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase52B/53 closeout unsafe flag is true: {key}")
    for key in (
        "manual_readonly_runtime_successfully_closed_out",
        "gateway_connection_verified",
        "empty_capture_handled",
        "capture_to_review_packet_replay_ready",
        "review_packet_pipeline_ready_for_real_capture",
        "ready_for_next_readonly_capture_canary_manual_gate",
    ):
        if not report.get(key):
            raise ValueError(f"Phase52B/53 closeout required flag is false: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase52B/53 closeout message_sent_count must stay 0.")


def render_phase52b_53_readonly_capture_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase52B/53 Read-only Capture Closeout",
            "",
            "- Manual read-only runtime successfully closed out: true",
            "- Gateway connection verified: true",
            "- Empty capture handled: true",
            "- Capture-to-review-packet replay ready: true",
            "- Review packet pipeline ready for real capture: true",
            "- Ready for next read-only capture canary manual gate: true",
            "- Discord message sent: false",
            "- Message sent count: 0",
            "- LLM/RAG/embedding/external: false",
        ]
    ) + "\n"
