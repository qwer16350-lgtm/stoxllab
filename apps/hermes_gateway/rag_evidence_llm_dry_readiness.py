"""Phase 34H-0 no-API/mock-only LLM dry-call readiness for RAG evidence prompts."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_response_packet import build_llm_response_packet
from llm_safety_policy import build_llm_safety_policy, check_llm_output_allowed
from rag_evidence_prompt_envelope import build_rag_evidence_prompt_envelope


VERSION = "phase34h0_no_api_mock_only"
MOCK_RESPONSE_TEXT = (
    "This is a review-only draft. No external action has been taken. "
    "Based on the provided local evidence preview, STOXL operation wording should stay calm, concise, "
    "and separated into confirmed points, risks, and next manual review actions. "
    "If more precision is required, the current evidence is insufficient and should be reviewed by a human."
)
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fake_dry_call_report(envelope: dict[str, Any], output_safety: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_type": "rag_evidence_llm_mock_dry_call_report",
        "created_at": utc_now(),
        "request": {
            "agent_route_candidate": envelope.get("agent", "kasumi"),
            "allow_api_call": False,
        },
        "client_result": {
            "provider": "mock_no_api",
            "model": "mock-review-only",
            "api_call_attempted": False,
            "api_call_succeeded": False,
            "response_text": MOCK_RESPONSE_TEXT,
            "usage": {
                "input_chars": len(json.dumps(envelope.get("messages_preview", []), ensure_ascii=False)),
                "provider_usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "estimated_cost_krw": 0,
            },
        },
        "output_safety": output_safety,
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
    }


def build_rag_evidence_llm_dry_readiness_report(
    root: str | Path | None = None,
    source: str = "operation",
    agent: str = "kasumi",
    query: str = "STOXL brand tone",
) -> dict[str, Any]:
    envelope = build_rag_evidence_prompt_envelope(root=root, source=source, agent=agent, query=query)
    policy = build_llm_safety_policy({"HERMES_LLM_PRIVATE_TEST_ONLY": "true", "HERMES_LLM_ALLOW_DISCORD_SEND": "false"})
    output_safety = check_llm_output_allowed(MOCK_RESPONSE_TEXT, policy)
    llm_packet = build_llm_response_packet(_fake_dry_call_report(envelope, output_safety))
    report = {
        "report_type": "rag_evidence_llm_dry_readiness",
        "version": VERSION,
        "created_at": utc_now(),
        "prompt_envelope_available": bool(envelope),
        "prompt_safety_allowed": bool(envelope.get("ready_for_prompt_preview")) and not envelope.get("ready_for_llm_api_call"),
        "mock_response_created": True,
        "mock_response_safety_allowed": bool(output_safety.get("allowed")),
        "llm_response_packet_created": bool(llm_packet.get("packet_type") == "llm_response_packet"),
        "ready_for_actual_llm_dry_call": bool(envelope.get("ready_for_prompt_preview")) and bool(output_safety.get("allowed")),
        "actual_llm_api_call": False,
        "discord_message_sent": False,
        "embedding_api_called": False,
        "external_execution": False,
        "ready_for_discord_send": False,
        "ready_for_embedding": False,
        "ready_for_external_sources": False,
        "mock_response": {
            "review_only": True,
            "text_preview": MOCK_RESPONSE_TEXT[:180],
        },
        "llm_response_packet": {
            "packet_type": llm_packet.get("packet_type"),
            "provider": llm_packet.get("provider"),
            "model": llm_packet.get("model"),
            "response_available": bool(llm_packet.get("response_available")),
            "message_sent": False,
            "discord_send_attempted": False,
            "rag_called": False,
            "external_execution": False,
        },
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_llm_dry_readiness_safe(report)
    return report


def render_rag_evidence_llm_dry_readiness_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence LLM Dry Readiness",
            "",
            f"- Prompt envelope available: {str(report.get('prompt_envelope_available')).lower()}",
            f"- Prompt safety allowed: {str(report.get('prompt_safety_allowed')).lower()}",
            f"- Mock response created: {str(report.get('mock_response_created')).lower()}",
            f"- Mock response safety allowed: {str(report.get('mock_response_safety_allowed')).lower()}",
            f"- LLM response packet created: {str(report.get('llm_response_packet_created')).lower()}",
            f"- Ready for actual LLM dry call: {str(report.get('ready_for_actual_llm_dry_call')).lower()}",
            "- Actual LLM API call: false",
            "- Ready for Discord send: false",
            "- Ready for embedding: false",
            "- Ready for external sources: false",
            "- Discord message sent: false",
            "- External execution: false",
        ]
    ) + "\n"


def assert_rag_evidence_llm_dry_readiness_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG evidence LLM dry readiness contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG evidence LLM dry readiness contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in (
            "actual_llm_api_call",
            "ready_for_discord_send",
            "ready_for_embedding",
            "ready_for_external_sources",
            "discord_message_sent",
            "embedding_api_called",
            "external_execution",
        ):
            if report.get(key):
                raise ValueError(f"RAG evidence LLM dry readiness unsafe flag is true: {key}")
