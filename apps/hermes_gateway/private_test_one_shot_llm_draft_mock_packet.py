"""Phase 36B one-shot LLM draft mock packet.

Creates review-only mock response packets from the Phase 36A preflight without
calling an LLM, attempting an API call, sending Discord messages, generating
approval phrases, creating embeddings, or executing external actions.
"""

from __future__ import annotations

import json
import re
from typing import Any

from private_test_one_shot_llm_draft_preflight import build_private_test_one_shot_llm_draft_preflight


VERSION = "phase36b_one_shot_llm_draft_mock_packet_no_api_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _mock_packet_for(agent: str, preflight: dict[str, Any]) -> dict[str, Any]:
    if not preflight.get("candidate"):
        return {
            "agent": agent,
            "candidate_from_preflight": False,
            "mock_response_created": False,
            "blocked_reason": "not_preflight_candidate",
        }
    citations = list(preflight.get("evidence_citations", []))
    return {
        "agent": agent,
        "candidate_from_preflight": True,
        "allowed_sources": list(preflight.get("allowed_sources", [])),
        "evidence_citations": citations,
        "mock_response_created": True,
        "mock_response_review_only": True,
        "mock_response_summary": "Review-only operational draft based on operation evidence. No Discord send is allowed in this phase.",
        "mock_response_text": (
            "Review-only draft for internal review. Based on the cited operation evidence, "
            "the response should summarize operational checks, separate known facts from "
            "uncertainty, and request human review before any next step. "
            "No external action has been taken."
        ),
        "full_content_included": False,
        "ready_for_output_safety_rehearsal": bool(citations),
        "ready_for_actual_llm_call": False,
    }


def build_private_test_one_shot_llm_draft_mock_packet() -> dict[str, Any]:
    preflight = build_private_test_one_shot_llm_draft_preflight()
    packets = {
        agent: _mock_packet_for(agent, candidate)
        for agent, candidate in preflight.get("preflight_candidates", {}).items()
    }
    report = {
        "report_type": "private_test_one_shot_llm_draft_mock_packet",
        "version": VERSION,
        "mock_packet_available": True,
        "report_only": True,
        "phase36_live_execution_started": False,
        "source_preflight": preflight.get("version", ""),
        "llm_called": False,
        "llm_api_call_attempted": False,
        "llm_api_call_count": 0,
        "discord_message_sent": False,
        "discord_api_send_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "manual_approval_actualized": False,
        "ready_for_actual_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "mock_candidate_agents": [
            agent
            for agent, packet in packets.items()
            if packet.get("mock_response_created")
        ],
        "mock_draft_packets": packets,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "approval_phrase_generated": False,
            "full_content_included": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
        },
    }
    assert_private_test_one_shot_llm_draft_mock_packet_safe(report)
    return report


def assert_private_test_one_shot_llm_draft_mock_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("One-shot LLM draft mock packet contains sensitive values.")
    for key in (
        "phase36_live_execution_started",
        "llm_called",
        "llm_api_call_attempted",
        "discord_message_sent",
        "discord_api_send_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "manual_approval_actualized",
        "ready_for_actual_llm_call",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"One-shot LLM draft mock packet unsafe flag is true: {key}")
    if int(report.get("llm_api_call_count", 0) or 0) != 0:
        raise ValueError("One-shot LLM draft mock packet attempted an LLM call.")
    for packet in report.get("mock_draft_packets", {}).values():
        if packet.get("full_content_included"):
            raise ValueError("One-shot LLM draft mock packet includes full content.")
        for path in packet.get("evidence_citations", []):
            if ":" in path or str(path).startswith("/") or str(path).startswith("\\\\"):
                raise ValueError("One-shot LLM draft mock packet requires relative citation paths only.")


def render_private_test_one_shot_llm_draft_mock_packet_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Private-test One-shot LLM Draft Mock Packet",
            "",
            "- Mock packet available: true",
            "- Report only: true",
            "- Phase 36 live execution started: false",
            "- LLM called: false",
            "- LLM API call attempted: false",
            "- LLM API call count: 0",
            "- Discord message sent: false",
            "- Discord API send called: false",
            "- Approval phrase generated: false",
            "- Manual approval actualized: false",
            "- Ready for actual LLM call: false",
            "- Ready for Discord send: false",
            f"- Mock candidate agents: {', '.join(report.get('mock_candidate_agents', [])) or 'none'}",
        ]
    ) + "\n"
