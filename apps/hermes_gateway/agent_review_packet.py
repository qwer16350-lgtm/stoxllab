"""Phase 35D agent review packet.

Report-only review packets derived from Phase 35C evidence/prompt previews.
No LLM, Discord send, embedding/vector creation, full content dump, or external
execution is performed.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent_evidence_pack_composer import build_agent_evidence_pack_composer, validate_agent_source
from agent_prompt_preview import build_agent_prompt_preview


VERSION = "phase35d_agent_review_packet_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
RISK_FLAGS = {
    "no_evidence_citations",
    "forbidden_source_requested",
    "unknown_source_requested",
    "broad_source_scope",
    "full_content_requested",
    "not_ready_for_approval",
}


def _risk_flags(
    agent: str,
    allowed_sources: list[str],
    blocked_sources: list[str],
    evidence_citations: list[str],
    *,
    full_content_requested: bool = False,
) -> list[str]:
    flags: list[str] = []
    if not evidence_citations:
        flags.append("no_evidence_citations")
    if "operations" in blocked_sources:
        flags.append("forbidden_source_requested")
    if any(validate_agent_source(agent, source).get("reason") == "unknown_source" for source in blocked_sources):
        flags.append("unknown_source_requested")
    if len(allowed_sources) >= 4 or agent == "decision_maker_review":
        flags.append("broad_source_scope")
    if full_content_requested:
        flags.append("full_content_requested")
    if not _ready_for_approval(evidence_citations, agent):
        flags.append("not_ready_for_approval")
    return [flag for flag in flags if flag in RISK_FLAGS]


def _ready_for_approval(evidence_citations: list[str], agent: str) -> bool:
    return bool(evidence_citations) and agent not in {"decision_maker_review", "unrouted"}


def build_agent_review_packet() -> dict[str, Any]:
    composer = build_agent_evidence_pack_composer()
    prompt = build_agent_prompt_preview(composer)
    packets: dict[str, Any] = {}
    for agent, pack in composer.get("agent_evidence_packs", {}).items():
        prompt_preview = prompt.get("agent_prompt_previews", {}).get(agent, {})
        citations = [str(item.get("path", "")) for item in pack.get("evidence_items", []) if item.get("path")]
        allowed_sources = list(pack.get("allowed_sources", []))
        blocked_sources = list(pack.get("blocked_sources", []))
        risks = _risk_flags(agent, allowed_sources, blocked_sources, citations)
        packets[agent] = {
            "agent": agent,
            "allowed_sources": allowed_sources,
            "blocked_sources": blocked_sources,
            "evidence_citations": citations,
            "evidence_citation_summary": {
                "citation_count": len(citations),
                "citations": citations,
            },
            "prompt_preview_summary": prompt_preview.get("prompt_preview_summary", ""),
            "risk_flags": risks,
            "human_review_required": True,
            "ready_for_approval_packet": "not_ready_for_approval" not in risks,
        }
    report = {
        "report_type": "agent_review_packet",
        "version": VERSION,
        "review_packet_available": True,
        "rule_only": True,
        "human_review_required": True,
        "llm_called": False,
        "discord_message_sent": False,
        "ready_for_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "relative_paths_only": True,
        "full_content_included": False,
        "ready_for_unattended_auto_reply": False,
        "agent_review_packets": packets,
        "risk_flag_catalog": sorted(RISK_FLAGS),
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "embedding_called": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
            "public_team_channel_reply_allowed": False,
            "unattended_auto_reply_allowed": False,
        },
    }
    assert_agent_review_packet_safe(report)
    return report


def assert_agent_review_packet_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Agent review packet contains sensitive values.")
    for key in (
        "llm_called",
        "discord_message_sent",
        "ready_for_llm_call",
        "ready_for_discord_send",
        "ready_for_embedding",
        "ready_for_external_sources",
        "full_content_included",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Agent review packet unsafe flag is true: {key}")
    for packet in report.get("agent_review_packets", {}).values():
        for path in packet.get("evidence_citations", []):
            if ":" in path or str(path).startswith("/") or str(path).startswith("\\\\"):
                raise ValueError("Agent review packet requires relative citation paths only.")


def render_agent_review_packet_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# STOXL Agent Review Packet",
        "",
        "- Review packet available: true",
        "- Rule only: true",
        "- Human review required: true",
        "- LLM called: false",
        "- Discord message sent: false",
        "- Ready for LLM call: false",
        "- Ready for Discord send: false",
        "- Ready for embedding: false",
        "- Ready for external sources: false",
        "- Full content included: false",
        f"- Agent review packet count: {len(report.get('agent_review_packets', {}))}",
        "",
        "## Agents",
    ]
    for agent, packet in report.get("agent_review_packets", {}).items():
        risks = ", ".join(packet.get("risk_flags", [])) or "none"
        lines.append(f"- {agent}: citations={len(packet.get('evidence_citations', []))}, risks={risks}, human_review_required=true")
    return "\n".join(lines) + "\n"
