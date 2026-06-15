"""Phase 35C agent prompt preview.

Rule-only prompt preview from composed evidence packs. No prompt execution.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent_evidence_pack_composer import build_agent_evidence_pack_composer


VERSION = "phase35c_agent_prompt_preview_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def _summary_for(agent: str, sources: list[str]) -> str:
    if agent == "kasumi":
        return "Use operation evidence only. Produce review-only operational guidance. Do not use operations source."
    if agent == "marin":
        return "Use marketing/brand evidence only. Operation source is blocked for marin."
    if agent == "decision_maker_review":
        return "May review all canonical sources. Forbidden source operations remains blocked."
    if not sources:
        return "No routed sources. Keep response unrouted and request human review."
    return f"Use {', '.join(sources)} evidence only. Produce review-only guidance."


def build_agent_prompt_preview(composer: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = composer or build_agent_evidence_pack_composer()
    previews: dict[str, Any] = {}
    for agent, pack in selected.get("agent_evidence_packs", {}).items():
        citations = [item.get("path", "") for item in pack.get("evidence_items", []) if item.get("path")]
        previews[agent] = {
            "agent": agent,
            "allowed_sources": pack.get("allowed_sources", []),
            "prompt_preview_summary": _summary_for(agent, pack.get("allowed_sources", [])),
            "evidence_citations": citations,
            "ready_for_llm_call": False,
        }
    report = {
        "report_type": "agent_prompt_preview",
        "version": VERSION,
        "prompt_preview_available": True,
        "rule_only": True,
        "llm_called": False,
        "discord_message_sent": False,
        "ready_for_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "full_prompt_executed": False,
        "full_content_included": False,
        "relative_paths_only": True,
        "agent_prompt_previews": previews,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "embedding_called": False,
            "external_execution": False,
            "llm_called": False,
            "discord_message_sent": False,
        },
    }
    assert_agent_prompt_preview_safe(report)
    return report


def assert_agent_prompt_preview_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text):
        raise ValueError("Agent prompt preview contains sensitive values.")
    for key in ("llm_called", "discord_message_sent", "ready_for_llm_call", "ready_for_discord_send", "ready_for_embedding", "ready_for_external_sources", "full_prompt_executed", "full_content_included", "ready_for_unattended_auto_reply"):
        if report.get(key):
            raise ValueError(f"Agent prompt preview unsafe flag is true: {key}")
    for preview in report.get("agent_prompt_previews", {}).values():
        for path in preview.get("evidence_citations", []):
            if ":" in path or str(path).startswith("/") or str(path).startswith("\\\\"):
                raise ValueError("Agent prompt preview requires relative citation paths only.")


def render_agent_prompt_preview_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Agent Prompt Preview",
            "",
            "- Prompt preview available: true",
            "- Rule only: true",
            "- LLM called: false",
            "- Discord message sent: false",
            "- Ready for LLM call: false",
            "- Ready for Discord send: false",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Full prompt executed: false",
            "- Full content included: false",
            f"- Agent prompt preview count: {len(report.get('agent_prompt_previews', {}))}",
        ]
    ) + "\n"
