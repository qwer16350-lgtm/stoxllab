"""Phase 35D manual approval packet preview.

Shows which manual gates would be needed for a later live run. It does not
generate approval phrases, approve anything, call LLMs, send Discord messages,
or perform external execution.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent_review_packet import build_agent_review_packet


VERSION = "phase35d_manual_approval_packet_preview_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _approval_scope(ready: bool) -> str:
    return "private_test_only" if ready else "none"


def _allowed_future_action(ready: bool) -> str:
    return "one_private_test_review_only_llm_draft" if ready else "none"


def build_manual_approval_packet_preview(review_packet: dict[str, Any] | None = None) -> dict[str, Any]:
    review = review_packet or build_agent_review_packet()
    previews: dict[str, Any] = {}
    for agent, packet in review.get("agent_review_packets", {}).items():
        ready = bool(packet.get("ready_for_approval_packet"))
        previews[agent] = {
            "agent": agent,
            "review_packet_ready": ready,
            "manual_approval_required_for_future_live_run": True,
            "approval_scope": _approval_scope(ready),
            "allowed_future_action": _allowed_future_action(ready),
            "discord_send_allowed": False,
            "llm_call_allowed": False,
            "embedding_allowed": False,
            "external_execution_allowed": False,
            "approval_phrase_generated": False,
        }
    report = {
        "report_type": "manual_approval_packet_preview",
        "version": VERSION,
        "approval_packet_preview_available": True,
        "rule_only": True,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "human_review_required": True,
        "ready_for_actual_approval": False,
        "ready_for_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "approval_packet_previews": previews,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "approval_phrase_generated": False,
            "embedding_called": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
            "public_team_channel_reply_allowed": False,
            "unattended_auto_reply_allowed": False,
        },
    }
    assert_manual_approval_packet_preview_safe(report)
    return report


def assert_manual_approval_packet_preview_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Manual approval packet preview contains sensitive values.")
    for key in (
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "ready_for_actual_approval",
        "ready_for_llm_call",
        "ready_for_discord_send",
        "ready_for_embedding",
        "ready_for_external_sources",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Manual approval packet preview unsafe flag is true: {key}")
    for preview in report.get("approval_packet_previews", {}).values():
        if preview.get("discord_send_allowed") or preview.get("llm_call_allowed") or preview.get("approval_phrase_generated"):
            raise ValueError("Manual approval packet preview allows a live action.")


def render_manual_approval_packet_preview_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# STOXL Manual Approval Packet Preview",
        "",
        "- Approval packet preview available: true",
        "- Rule only: true",
        "- Approval phrase generated: false",
        "- Approval phrase value logged: false",
        "- Human review required: true",
        "- Ready for actual approval: false",
        "- Ready for LLM call: false",
        "- Ready for Discord send: false",
        "- Ready for embedding: false",
        "- Ready for external sources: false",
        "- Ready for unattended auto reply: false",
        f"- Approval packet preview count: {len(report.get('approval_packet_previews', {}))}",
        "",
        "## Future Gate Preview",
    ]
    for agent, preview in report.get("approval_packet_previews", {}).items():
        lines.append(
            f"- {agent}: review_packet_ready={str(preview.get('review_packet_ready')).lower()}, "
            f"scope={preview.get('approval_scope')}, approval_phrase_generated=false"
        )
    return "\n".join(lines) + "\n"
