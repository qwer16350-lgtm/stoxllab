"""Phase 37A private-test LLM draft review packet.

Report-only packet for human review. It uses the locked Phase 36 state and
never calls an LLM provider, starts Discord, sends messages, creates embeddings,
or executes external actions.
"""

from __future__ import annotations

import json
import re
from typing import Any

from one_shot_llm_no_send_final_lock import build_one_shot_llm_no_send_final_lock


VERSION = "phase37a_private_test_llm_draft_review_packet_no_send"
CITATION = "knowledge/operation/stoxl_operation_tone_sample.md"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_private_test_llm_draft_review_packet(final_lock: dict[str, Any] | None = None) -> dict[str, Any]:
    lock = final_lock or build_one_shot_llm_no_send_final_lock()
    report = {
        "report_type": "private_test_llm_draft_review_packet",
        "version": VERSION,
        "review_packet_available": True,
        "report_only": True,
        "source_phase36f_no_send_final_lock_passed": bool(lock.get("phase36f_no_send_final_lock_passed")),
        "phase36_llm_call_count_locked": int(lock.get("llm_call_count_locked", 0) or 0),
        "phase36_discord_send_count_locked": int(lock.get("discord_send_count_locked", 0) or 0),
        "agent": "kasumi",
        "allowed_sources": ["operation"],
        "evidence_citations": [CITATION],
        "draft_review_packet_created": True,
        "draft_review_only": True,
        "response_preview_only": True,
        "response_summary": "Kasumi operation draft is ready for private-test human review only. No external action has been taken.",
        "full_content_included": False,
        "human_review_required": True,
        "ready_for_private_test_send_preflight_preview": True,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": _safety_assertions(),
    }
    assert_private_test_llm_draft_review_packet_safe(report)
    return report


def _safety_assertions() -> dict[str, bool]:
    return {
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
        "llm_called": False,
    }


def assert_private_test_llm_draft_review_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 37A review packet contains sensitive values.")
    if report.get("agent") != "kasumi" or report.get("allowed_sources") != ["operation"]:
        raise ValueError("Phase 37A review packet must use kasumi and operation only.")
    if report.get("evidence_citations") != [CITATION]:
        raise ValueError("Phase 37A review packet has invalid citation.")
    for key in (
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "discord_api_send_called",
        "discord_message_sent",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
        "full_content_included",
    ):
        if report.get(key):
            raise ValueError(f"Phase 37A unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 37A message sent count must be 0.")


def render_private_test_llm_draft_review_packet_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Private-test LLM Draft Review Packet",
            "",
            f"- Review packet available: {str(report.get('review_packet_available')).lower()}",
            f"- Report only: {str(report.get('report_only')).lower()}",
            f"- Agent: {report.get('agent')}",
            f"- Sources: {', '.join(report.get('allowed_sources', []))}",
            f"- Draft review packet created: {str(report.get('draft_review_packet_created')).lower()}",
            "- New LLM API call attempted: false",
            "- Discord message sent: false",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
        ]
    ) + "\n"
