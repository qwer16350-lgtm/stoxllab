"""Phase 36B one-shot LLM draft output safety rehearsal."""

from __future__ import annotations

import json
import re
from typing import Any

from private_test_one_shot_llm_draft_mock_packet import build_private_test_one_shot_llm_draft_mock_packet


VERSION = "phase36b_one_shot_llm_draft_output_safety_rehearsal_no_api_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
PUBLIC_TEAM_SEND_RE = re.compile(r"(?i)(send|post|publish|reply).{0,80}(public|team|channel|discord)|public.{0,80}(send|reply|post)|team.{0,80}(send|reply|post)")
UNATTENDED_RE = re.compile(r"(?i)(unattended|auto[- ]?reply|automatic reply|scheduler|cron)")


def check_mock_output_safety(packet: dict[str, Any]) -> dict[str, Any]:
    text = str(packet.get("mock_response_text", "") or "")
    blocked_reasons: list[str] = []
    if not packet.get("mock_response_review_only") or "review-only" not in text.lower():
        blocked_reasons.append("missing_review_only_language")
    if packet.get("mock_response_created") and not packet.get("evidence_citations"):
        blocked_reasons.append("missing_evidence_citation")
    if SECRET_RE.search(text.lower()):
        blocked_reasons.append("secret_value_present")
    if LONG_ID_RE.search(text):
        blocked_reasons.append("raw_discord_id_present")
    if APPROVAL_RE.search(text):
        blocked_reasons.append("approval_phrase_present")
    if PUBLIC_TEAM_SEND_RE.search(text):
        blocked_reasons.append("public_team_send_instruction")
    if UNATTENDED_RE.search(text):
        blocked_reasons.append("unattended_auto_reply_instruction")
    if packet.get("full_content_included"):
        blocked_reasons.append("full_content_included")
    return {
        "output_safety_checked": True,
        "output_safety_allowed": not blocked_reasons,
        "blocked_reasons": blocked_reasons,
        "ready_for_actual_llm_call": False,
        "ready_for_discord_send": False,
    }


def _negative_fixture_results() -> dict[str, bool]:
    base = {
        "mock_response_created": True,
        "mock_response_review_only": True,
        "evidence_citations": ["knowledge/operation/stoxl_operation_tone_sample.md"],
        "full_content_included": False,
    }
    fixtures = {
        "secret_value_present_blocks": dict(base, mock_response_text="Review-only draft with api key: sk-test-secret"),
        "approval_phrase_present_blocks": dict(base, mock_response_text="Review-only draft I_APPROVE_TEST_VALUE"),
        "raw_discord_id_present_blocks": dict(base, mock_response_text="Review-only draft for 123456789012345678"),
        "public_team_send_instruction_blocks": dict(base, mock_response_text="Review-only draft. Send this to the public team channel."),
        "unattended_auto_reply_instruction_blocks": dict(base, mock_response_text="Review-only draft. Enable unattended auto reply."),
        "full_content_included_blocks": dict(base, mock_response_text="Review-only draft.", full_content_included=True),
    }
    return {
        name: not check_mock_output_safety(packet)["output_safety_allowed"]
        for name, packet in fixtures.items()
    }


def build_one_shot_llm_draft_output_safety_rehearsal(
    mock_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = mock_packet or build_private_test_one_shot_llm_draft_mock_packet()
    results: dict[str, Any] = {}
    for agent, packet in selected.get("mock_draft_packets", {}).items():
        if not packet.get("mock_response_created"):
            continue
        safety = check_mock_output_safety(packet)
        results[agent] = {
            "mock_response_created": True,
            **safety,
        }
    negative = _negative_fixture_results()
    report = {
        "report_type": "one_shot_llm_draft_output_safety_rehearsal",
        "version": VERSION,
        "output_safety_rehearsal_available": True,
        "report_only": True,
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
        "input_mock_packet_available": bool(selected.get("mock_packet_available")),
        "safety_checks": {
            "review_only_language_checked": True,
            "evidence_citation_checked": True,
            "no_secret_checked": True,
            "no_raw_discord_id_checked": True,
            "no_approval_phrase_checked": True,
            "no_public_team_send_instruction_checked": True,
            "no_unattended_instruction_checked": True,
            "full_content_absence_checked": True,
        },
        "agent_safety_results": results,
        "output_safety_allowed_agents": [
            agent for agent, result in results.items() if result.get("output_safety_allowed")
        ],
        "negative_fixtures": negative,
        "negative_fixtures_passed": all(negative.values()),
        "ready_for_phase36c_actual_llm_call_preflight": bool(results) and all(negative.values()),
        "ready_for_actual_llm_call": False,
        "ready_for_discord_send": False,
        "ready_for_unattended_auto_reply": False,
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
    assert_one_shot_llm_draft_output_safety_rehearsal_safe(report)
    return report


def assert_one_shot_llm_draft_output_safety_rehearsal_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("One-shot LLM draft output safety rehearsal contains sensitive values.")
    for key in (
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
            raise ValueError(f"One-shot LLM draft output safety rehearsal unsafe flag is true: {key}")
    if int(report.get("llm_api_call_count", 0) or 0) != 0:
        raise ValueError("One-shot LLM draft output safety rehearsal attempted an LLM call.")


def render_one_shot_llm_draft_output_safety_rehearsal_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL One-shot LLM Draft Output Safety Rehearsal",
            "",
            "- Output safety rehearsal available: true",
            "- Report only: true",
            "- LLM called: false",
            "- Discord message sent: false",
            "- Input mock packet available: true",
            f"- Output safety allowed agents: {', '.join(report.get('output_safety_allowed_agents', [])) or 'none'}",
            f"- Negative fixtures passed: {str(report.get('negative_fixtures_passed')).lower()}",
            f"- Ready for Phase 36C actual LLM call preflight: {str(report.get('ready_for_phase36c_actual_llm_call_preflight')).lower()}",
            "- Ready for actual LLM call: false",
            "- Ready for Discord send: false",
            "- Ready for unattended auto reply: false",
        ]
    ) + "\n"
