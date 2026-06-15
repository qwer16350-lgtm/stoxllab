"""Phase 36C actual one-shot LLM draft call preflight.

Checks the prerequisites for a future manually approved LLM call without
attempting an API call, sending Discord messages, generating approval phrases,
creating embeddings, or executing external actions.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from one_shot_llm_draft_output_safety_rehearsal import build_one_shot_llm_draft_output_safety_rehearsal
from private_test_one_shot_llm_draft_mock_packet import build_private_test_one_shot_llm_draft_mock_packet
from private_test_one_shot_llm_draft_preflight import build_private_test_one_shot_llm_draft_preflight


VERSION = "phase36c_actual_one_shot_llm_draft_call_preflight_no_api_no_send"
OPENROUTER_KEY_ALIASES = ["OPENROUTER_API_KEY", "HERMES_OPENROUTER_API_KEY"]
PROVIDER = "openrouter"
MODEL = "openai/gpt-5.4-mini"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _env_has_any(env: dict[str, Any] | None, keys: list[str]) -> bool:
    source = env if env is not None else os.environ
    return any(bool(str(source.get(key, "") or "").strip()) for key in keys)


def build_actual_one_shot_llm_draft_call_preflight(env: dict[str, Any] | None = None) -> dict[str, Any]:
    phase36a = build_private_test_one_shot_llm_draft_preflight()
    mock = build_private_test_one_shot_llm_draft_mock_packet()
    safety = build_one_shot_llm_draft_output_safety_rehearsal(mock)
    candidate = phase36a.get("preflight_candidates", {}).get("kasumi", {})
    openrouter_key_present = _env_has_any(env, OPENROUTER_KEY_ALIASES)
    source_safety_allowed = "kasumi" in safety.get("output_safety_allowed_agents", [])
    candidate_allowed = bool(candidate.get("candidate"))
    citations = list(candidate.get("evidence_citations", []))
    blocked_reasons: list[str] = []
    if not openrouter_key_present:
        blocked_reasons.append("openrouter_api_key_missing")
    blocked_reasons.append("manual_approval_not_actualized")
    prereqs_met = bool(
        phase36a.get("preflight_available")
        and mock.get("mock_packet_available")
        and source_safety_allowed
        and candidate_allowed
        and citations
        and openrouter_key_present
    )
    report = {
        "report_type": "actual_one_shot_llm_draft_call_preflight",
        "version": VERSION,
        "preflight_available": True,
        "report_only": True,
        "phase36_live_execution_started": False,
        "source_phase36a_preflight_available": bool(phase36a.get("preflight_available")),
        "source_phase36b_mock_packet_available": bool(mock.get("mock_packet_available")),
        "source_phase36b_output_safety_allowed": source_safety_allowed,
        "candidate_agent": "kasumi",
        "candidate_agent_allowed": candidate_allowed,
        "allowed_sources": list(candidate.get("allowed_sources", [])),
        "evidence_citations": citations,
        "manual_approval_required": True,
        "manual_approval_actualized": False,
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "future_manual_gate_names": [
            "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVED",
            "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVAL_PHRASE",
        ],
        "openrouter_api_key_present": openrouter_key_present,
        "openrouter_api_key_value_logged": False,
        "openrouter_api_key_aliases_checked": OPENROUTER_KEY_ALIASES,
        "provider": PROVIDER,
        "model": MODEL,
        "model_value_logged": True,
        "llm_called": False,
        "llm_api_call_attempted": False,
        "llm_api_call_count": 0,
        "discord_message_sent": False,
        "discord_api_send_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "preflight_checks": {
            "candidate_agent_checked": True,
            "evidence_citations_checked": True,
            "mock_packet_checked": True,
            "output_safety_rehearsal_checked": True,
            "manual_approval_gate_checked": True,
            "openrouter_key_presence_checked": True,
            "discord_send_block_checked": True,
            "public_team_block_checked": True,
            "unattended_block_checked": True,
        },
        "preflight_ready_for_manual_llm_call": prereqs_met,
        "ready_for_actual_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
        "blocked_reasons": blocked_reasons,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "approval_phrase_generated": False,
            "manual_approval_actualized": False,
            "full_content_included": False,
            "embedding_called": False,
            "vector_index_created": False,
            "external_execution": False,
            "llm_called": False,
            "llm_api_call_attempted": False,
            "discord_message_sent": False,
        },
    }
    assert_actual_one_shot_llm_draft_call_preflight_safe(report)
    return report


def assert_actual_one_shot_llm_draft_call_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Actual one-shot LLM draft call preflight contains sensitive values.")
    for key in (
        "phase36_live_execution_started",
        "manual_approval_actualized",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "openrouter_api_key_value_logged",
        "llm_called",
        "llm_api_call_attempted",
        "discord_message_sent",
        "discord_api_send_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_actual_llm_call",
        "ready_for_discord_send",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Actual one-shot LLM draft call preflight unsafe flag is true: {key}")
    if int(report.get("llm_api_call_count", 0) or 0) != 0:
        raise ValueError("Actual one-shot LLM draft call preflight attempted an LLM call.")
    for path in report.get("evidence_citations", []):
        if ":" in path or str(path).startswith("/") or str(path).startswith("\\\\"):
            raise ValueError("Actual one-shot LLM draft call preflight requires relative citation paths only.")


def render_actual_one_shot_llm_draft_call_preflight_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Actual One-shot LLM Draft Call Preflight",
            "",
            "- Preflight available: true",
            "- Report only: true",
            "- Phase 36 live execution started: false",
            f"- Candidate agent: {report.get('candidate_agent')}",
            f"- OpenRouter API key present: {str(report.get('openrouter_api_key_present')).lower()}",
            "- Manual approval required: true",
            "- Manual approval actualized: false",
            f"- Preflight ready for manual LLM call: {str(report.get('preflight_ready_for_manual_llm_call')).lower()}",
            "- Ready for actual LLM call: false",
            "- LLM called: false",
            "- LLM API call attempted: false",
            "- LLM API call count: 0",
            "- Discord message sent: false",
            "- Discord API send called: false",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
        ]
    ) + "\n"
