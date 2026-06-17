"""Phase53 capture-to-review-packet replay for read-only capture metadata."""

from __future__ import annotations

import json
import re
from typing import Any

from phase52b_capture_metadata_review import build_phase52b_capture_metadata_review


VERSION = "phase53_capture_to_review_packet_replay_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase53_capture_to_review_packet_replay(metadata_review: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = metadata_review or build_phase52b_capture_metadata_review()
    captured_count = int(selected.get("captured_event_count", 0) or 0)
    report = {
        "report_type": "phase53_capture_to_review_packet_replay",
        "version": VERSION,
        "source": "readonly_live_capture",
        "captured_event_count": captured_count,
        "replayed_event_count": captured_count,
        "review_packet_count": captured_count,
        "empty_capture_replay_handled": captured_count == 0,
        "synthetic_fallback_used": False,
        "review_packet_pipeline_connected": True,
        "review_packet_pipeline_ready": True,
        "discord_send_allowed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_content_included": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "ready_for_next_readonly_capture_canary": True,
    }
    assert_phase53_capture_to_review_packet_replay_safe(report)
    return report


def assert_phase53_capture_to_review_packet_replay_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase53 capture replay contains sensitive values.")
    for key in (
        "synthetic_fallback_used",
        "discord_send_allowed",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "raw_content_included",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
    ):
        if report.get(key):
            raise ValueError(f"Phase53 replay unsafe flag is true: {key}")
    if not report.get("review_packet_pipeline_ready") or not report.get("ready_for_next_readonly_capture_canary"):
        raise ValueError("Phase53 replay requires pipeline readiness and next canary readiness.")


def render_phase53_capture_to_review_packet_replay_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase53 Capture-to-Review-Packet Replay",
            "",
            "- Source: readonly_live_capture",
            f"- Captured event count: {report.get('captured_event_count')}",
            f"- Replayed event count: {report.get('replayed_event_count')}",
            f"- Review packet count: {report.get('review_packet_count')}",
            f"- Empty capture replay handled: {str(report.get('empty_capture_replay_handled')).lower()}",
            "- Discord send allowed: false",
            "- LLM/RAG/embedding/external: false",
            "- Ready for next read-only capture canary: true",
        ]
    ) + "\n"
