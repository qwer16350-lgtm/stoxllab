"""Phase 36A private-test one-shot LLM draft preflight.

This report identifies future one-shot draft candidates without calling an LLM,
sending Discord messages, generating approval phrases, creating embeddings, or
executing external actions.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent_review_packet import build_agent_review_packet
from forbidden_behavior_sentinel import build_forbidden_behavior_sentinel
from local_knowledge_ingestion_preview import CANONICAL_SOURCES, FORBIDDEN_SOURCES
from manual_approval_packet_preview import build_manual_approval_packet_preview
from phase36_entry_gate import build_phase36_entry_gate


VERSION = "phase36a_private_test_one_shot_llm_draft_preflight_no_call_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
CRITICAL_RISK_FLAGS = {
    "forbidden_source_requested",
    "unknown_source_requested",
    "full_content_requested",
    "not_ready_for_approval",
}


def _candidate_risk_flags(packet: dict[str, Any]) -> list[str]:
    # Phase 35D review packets include forbidden_source_requested when a source
    # is blocked. Phase 36A treats it as critical only when the candidate
    # actually requests or includes that source.
    flags = [
        flag
        for flag in packet.get("risk_flags", [])
        if flag != "forbidden_source_requested"
    ]
    if any(source in FORBIDDEN_SOURCES for source in packet.get("allowed_sources", [])):
        flags.append("forbidden_source_requested")
    return flags


def _candidate_from_review(agent: str, packet: dict[str, Any]) -> dict[str, Any]:
    allowed_sources = list(packet.get("allowed_sources", []))
    citations = list(packet.get("evidence_citations", []))
    risks = _candidate_risk_flags(packet)
    sources_are_canonical = all(source in CANONICAL_SOURCES for source in allowed_sources)
    has_critical_risk = any(flag in CRITICAL_RISK_FLAGS for flag in risks)
    candidate = bool(
        packet.get("human_review_required")
        and sources_are_canonical
        and citations
        and not has_critical_risk
        and agent == "kasumi"
    )
    return {
        "agent": agent,
        "candidate": candidate,
        "allowed_sources": allowed_sources,
        "evidence_citations": citations,
        "risk_flags": risks,
        "human_review_required": True,
        "future_action": "one_private_test_review_only_llm_draft_no_send" if candidate else "none",
        "ready_for_future_manual_llm_draft": False,
    }


def build_private_test_one_shot_llm_draft_preflight() -> dict[str, Any]:
    review = build_agent_review_packet()
    approval = build_manual_approval_packet_preview(review)
    entry_gate = build_phase36_entry_gate()
    sentinel = build_forbidden_behavior_sentinel()
    candidates = {
        agent: _candidate_from_review(agent, packet)
        for agent, packet in review.get("agent_review_packets", {}).items()
    }
    report = {
        "report_type": "private_test_one_shot_llm_draft_preflight",
        "version": VERSION,
        "preflight_available": True,
        "report_only": True,
        "phase36_started": False,
        "requires_explicit_user_approval": bool(entry_gate.get("requires_explicit_user_approval")),
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
        "ready_for_actual_approval": False,
        "ready_for_actual_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "review_packet_available": bool(review.get("review_packet_available")),
        "manual_approval_packet_preview_available": bool(approval.get("approval_packet_preview_available")),
        "phase36_entry_gate_available": bool(entry_gate.get("phase36_entry_gate_available")),
        "forbidden_behavior_sentinel_passed": bool(sentinel.get("forbidden_behavior_sentinel_passed")),
        "preflight_candidates": candidates,
        "candidate_agents": [agent for agent, item in candidates.items() if item.get("candidate")],
        "future_manual_gate_names": [
            "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVED",
            "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVAL_PHRASE",
            "OPENROUTER_API_KEY",
        ],
        "critical_risk_flags": sorted(CRITICAL_RISK_FLAGS),
        "blocked_scopes": {
            "public_channel_reply_allowed": False,
            "team_channel_reply_allowed": False,
            "public_channel_send_allowed": False,
            "team_channel_send_allowed": False,
            "discord_send_allowed": False,
            "unattended_auto_reply_allowed": False,
        },
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
    assert_private_test_one_shot_llm_draft_preflight_safe(report)
    return report


def assert_private_test_one_shot_llm_draft_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Private-test one-shot LLM draft preflight contains sensitive values.")
    for key in (
        "phase36_started",
        "llm_called",
        "llm_api_call_attempted",
        "discord_message_sent",
        "discord_api_send_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "ready_for_actual_approval",
        "ready_for_actual_llm_call",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Private-test one-shot LLM draft preflight unsafe flag is true: {key}")
    if int(report.get("llm_api_call_count", 0) or 0) != 0:
        raise ValueError("Private-test one-shot LLM draft preflight attempted an LLM call.")
    for packet in report.get("preflight_candidates", {}).values():
        for path in packet.get("evidence_citations", []):
            if ":" in path or str(path).startswith("/") or str(path).startswith("\\\\"):
                raise ValueError("Private-test one-shot LLM draft preflight requires relative citation paths only.")


def render_private_test_one_shot_llm_draft_preflight_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Private-test One-shot LLM Draft Preflight",
            "",
            "- Preflight available: true",
            "- Report only: true",
            "- Phase 36 started: false",
            "- Requires explicit user approval: true",
            "- LLM called: false",
            "- LLM API call attempted: false",
            "- LLM API call count: 0",
            "- Discord message sent: false",
            "- Discord API send called: false",
            "- Approval phrase generated: false",
            "- Ready for actual LLM call: false",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
            f"- Candidate agents: {', '.join(report.get('candidate_agents', [])) or 'none'}",
        ]
    ) + "\n"
