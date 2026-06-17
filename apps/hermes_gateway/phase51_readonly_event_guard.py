"""Phase51 read-only event guard for normalized synthetic events."""

from __future__ import annotations

import json
import re
from typing import Any

from phase51_readonly_event_schema import SYNTHETIC_EVENTS, normalize_readonly_event


VERSION = "phase51_readonly_event_guard_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def guard_readonly_event(normalized_event: dict[str, Any]) -> dict[str, Any]:
    author_kind = normalized_event.get("author_kind")
    message_kind = normalized_event.get("message_kind")
    channel_risk = normalized_event.get("channel_risk")
    ignored = {
        "self_message_ignored": author_kind == "self",
        "bot_message_ignored": author_kind == "bot",
        "duplicate_message_ignored": message_kind == "duplicate",
        "operator_command_detected": message_kind == "operator_command",
        "public_high_risk_detected": channel_risk == "public_high",
    }
    allowed_for_packet = (
        author_kind == "human"
        and message_kind == "normal"
        and channel_risk in {"private_test", "team_low"}
    )
    result = {
        "event_allowed_for_review_packet": allowed_for_packet,
        "event_allowed_for_reply": False,
        "discord_send_allowed": False,
        "llm_call_allowed": False,
        "rag_call_allowed": False,
        "external_execution_allowed": False,
        **ignored,
    }
    assert_phase51_readonly_event_guard_safe(result)
    return result


def build_phase51_readonly_event_guard() -> dict[str, Any]:
    fixture_results = []
    for raw_event in SYNTHETIC_EVENTS:
        normalized = normalize_readonly_event(raw_event)
        guard = guard_readonly_event(normalized)
        fixture_results.append(
            {
                "event_ref_hash": normalized["event_ref_hash"],
                "channel_risk": normalized["channel_risk"],
                "author_kind": normalized["author_kind"],
                "message_kind": normalized["message_kind"],
                "event_allowed_for_review_packet": guard["event_allowed_for_review_packet"],
                "event_allowed_for_reply": False,
                "discord_send_allowed": False,
            }
        )
    report = {
        "report_type": "phase51_readonly_event_guard",
        "version": VERSION,
        "guard_available": True,
        "synthetic_fixture_only": True,
        "fixture_count": len(fixture_results),
        "fixture_results": fixture_results,
        "event_allowed_for_review_packet": True,
        "event_allowed_for_reply": False,
        "discord_send_allowed": False,
        "self_message_ignored": any(item["author_kind"] == "self" for item in fixture_results),
        "bot_message_ignored": any(item["author_kind"] == "bot" for item in fixture_results),
        "duplicate_message_ignored": any(item["message_kind"] == "duplicate" for item in fixture_results),
        "operator_command_detected": any(item["message_kind"] == "operator_command" for item in fixture_results),
        "public_high_risk_detected": any(item["channel_risk"] == "public_high" for item in fixture_results),
        "actual_discord_runtime_executed": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    assert_phase51_readonly_event_guard_safe(report)
    return report


def assert_phase51_readonly_event_guard_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase51 readonly event guard contains sensitive values.")
    for key in (
        "event_allowed_for_reply",
        "discord_send_allowed",
        "llm_call_allowed",
        "rag_call_allowed",
        "external_execution_allowed",
        "actual_discord_runtime_executed",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        if report.get(key):
            raise ValueError(f"Phase51 readonly event guard unsafe flag is true: {key}")


def render_phase51_readonly_event_guard_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase51 Read-only Event Guard",
            "",
            "- Guard available: true",
            f"- Fixture count: {report.get('fixture_count')}",
            "- Event allowed for reply: false",
            "- Discord send allowed: false",
            f"- Self message ignored: {str(report.get('self_message_ignored')).lower()}",
            f"- Bot message ignored: {str(report.get('bot_message_ignored')).lower()}",
            f"- Duplicate message ignored: {str(report.get('duplicate_message_ignored')).lower()}",
            f"- Operator command detected: {str(report.get('operator_command_detected')).lower()}",
        ]
    ) + "\n"
