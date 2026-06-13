"""No-live-send replay closeout for Phase 32D LLM private test replies."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any


VERSION = "phase32d_closeout_no_live_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_MARKERS = ("sk-", "xoxb-", "mfa.", "bearer ", "token=", "password=")
RAW_DISCORD_ID_RE = re.compile(r"(?<!redacted:)\b\d{15,25}\b")

LIVE_SUCCESS_FIXTURE = "\n".join(
    [
        "[PRIVATE_TEST_LLM_READY] runtime_mode=private_test_llm_reply private_test_channel_configured=true llm_enabled=true provider=openrouter model_configured=true discord_send_enabled=true public_send_disabled=true rag_disabled=true external_disabled=true",
        "[READONLY_EVENT] accepted_private_test_channel channel=hermes-private-test author=discord_id_redacted:2216 content_present=true content_length=49",
        "[PRIVATE_TEST_LLM_REPLY] llm_call_allowed",
        "[PRIVATE_TEST_LLM_REPLY] output_safety_allowed",
        "[READONLY_EVENT] ignored_self_message channel=hermes-private-test author=discord_id_redacted:0062 content_present=true content_length=318",
        "[PRIVATE_TEST_LLM_REPLY] skipped reason=self_message",
        "[PRIVATE_TEST_LLM_REPLY_SENT] message_sent=true channel=hermes-private-test",
    ]
)

EVENT_TYPES = [
    "human_private_test_llm_allowed_sent",
    "self_message_skipped",
    "bot_message_skipped",
    "duplicate_message_blocked",
    "cooldown_blocked",
    "budget_exhausted_blocked",
    "public_channel_blocked",
    "private_channel_id_mismatch_blocked",
    "output_safety_blocked",
    "provider_error_blocked",
    "packet_safety_blocked",
    "rate_limit_circuit_breaker",
    "send_exception_circuit_breaker",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def verify_live_success_fixture(fixture: str = LIVE_SUCCESS_FIXTURE) -> dict[str, Any]:
    lines = [line.strip() for line in fixture.splitlines() if line.strip()]
    joined = "\n".join(lines)
    ready = any(line.startswith("[PRIVATE_TEST_LLM_READY]") for line in lines)
    accepted = any("accepted_private_test_channel" in line for line in lines)
    llm_calls = sum(1 for line in lines if line == "[PRIVATE_TEST_LLM_REPLY] llm_call_allowed")
    output_allowed = sum(1 for line in lines if line == "[PRIVATE_TEST_LLM_REPLY] output_safety_allowed")
    sent = sum(1 for line in lines if line.startswith("[PRIVATE_TEST_LLM_REPLY_SENT]"))
    self_index = next((idx for idx, line in enumerate(lines) if "ignored_self_message" in line), -1)
    second_llm_after_self = any(line == "[PRIVATE_TEST_LLM_REPLY] llm_call_allowed" for line in lines[self_index + 1 :]) if self_index >= 0 else False
    result = {
        "fixture_type": "llm_private_test_reply_live_success_fixture",
        "ready_log_exists": ready,
        "accepted_private_test_event_exists": accepted,
        "llm_call_allowed_count": llm_calls,
        "output_safety_allowed_count": output_allowed,
        "sent_count": sent,
        "self_message_skipped_exists": "skipped reason=self_message" in joined and "ignored_self_message" in joined,
        "no_second_llm_call_after_self_message": not second_llm_after_self,
        "no_public_channel_send": "channel=marketing-brief" not in joined and "public" not in joined.lower().replace("public_send_disabled=true", ""),
        "raw_discord_ids_present": bool(RAW_DISCORD_ID_RE.search(joined)),
        "verified": (
            ready
            and accepted
            and llm_calls == 1
            and output_allowed == 1
            and sent == 1
            and "skipped reason=self_message" in joined
            and not second_llm_after_self
            and not RAW_DISCORD_ID_RE.search(joined)
        ),
    }
    assert_llm_private_test_reply_replay_safe(result)
    return result


def build_llm_private_test_reply_replay_event(event_type: str) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unknown LLM private test reply replay event type: {event_type}")
    event = {
        "event_type": event_type,
        "version": VERSION,
        "event_id": f"event_redacted_{EVENT_TYPES.index(event_type):04d}",
        "channel_name": "hermes-private-test",
        "allowed": False,
        "blocked": False,
        "skipped": False,
        "historical_message_sent": False,
        "llm_call_allowed_in_fixture": False,
        "discord_send_attempted_in_fixture": False,
        "reason": "",
        "message_sent": False,
        "llm_api_called": False,
        "rag_called": False,
        "external_execution": False,
    }
    updates = {
        "human_private_test_llm_allowed_sent": {
            "allowed": True,
            "historical_message_sent": True,
            "llm_call_allowed_in_fixture": True,
            "discord_send_attempted_in_fixture": True,
            "reason": "llm_private_test_reply_sent",
        },
        "self_message_skipped": {"skipped": True, "reason": "self_message"},
        "bot_message_skipped": {"skipped": True, "reason": "bot_message"},
        "duplicate_message_blocked": {"blocked": True, "reason": "duplicate_message"},
        "cooldown_blocked": {"blocked": True, "reason": "cooldown_active"},
        "budget_exhausted_blocked": {"blocked": True, "reason": "reply_budget_exhausted"},
        "public_channel_blocked": {"blocked": True, "reason": "private_test_channel_only", "channel_name": "marketing-brief"},
        "private_channel_id_mismatch_blocked": {"blocked": True, "reason": "private_test_channel_only"},
        "output_safety_blocked": {"blocked": True, "reason": "output_safety_blocked"},
        "provider_error_blocked": {"blocked": True, "reason": "provider_error"},
        "packet_safety_blocked": {"blocked": True, "reason": "packet_safety_failed"},
        "rate_limit_circuit_breaker": {"blocked": True, "reason": "rate_limit_seen", "circuit_breaker_opened": True},
        "send_exception_circuit_breaker": {"blocked": True, "reason": "send_exception_seen", "circuit_breaker_opened": True},
    }
    event.update(updates[event_type])
    assert_llm_private_test_reply_replay_safe(event)
    return event


def build_llm_private_test_reply_replay_report(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    selected_events = events or [build_llm_private_test_reply_replay_event(kind) for kind in EVENT_TYPES]
    fixture = verify_live_success_fixture()
    summary = {
        "events_replayed": len(selected_events),
        "sent": sum(1 for event in selected_events if event.get("historical_message_sent")),
        "blocked": sum(1 for event in selected_events if event.get("blocked")),
        "skipped": sum(1 for event in selected_events if event.get("skipped")),
        "llm_calls": sum(1 for event in selected_events if event.get("llm_call_allowed_in_fixture")),
        "discord_send_attempts": sum(1 for event in selected_events if event.get("discord_send_attempted_in_fixture")),
        "self_messages_skipped": sum(1 for event in selected_events if event.get("reason") == "self_message"),
        "bot_messages_skipped": sum(1 for event in selected_events if event.get("reason") == "bot_message"),
        "public_channel_blocked": sum(1 for event in selected_events if event.get("channel_name") == "marketing-brief"),
        "private_channel_id_mismatch_blocked": sum(1 for event in selected_events if event.get("event_type") == "private_channel_id_mismatch_blocked"),
        "duplicates_blocked": sum(1 for event in selected_events if event.get("reason") == "duplicate_message"),
        "cooldown_blocked": sum(1 for event in selected_events if event.get("reason") == "cooldown_active"),
        "budget_exhausted_blocked": sum(1 for event in selected_events if event.get("reason") == "reply_budget_exhausted"),
        "provider_error_blocked": sum(1 for event in selected_events if event.get("reason") == "provider_error"),
        "output_safety_blocked": sum(1 for event in selected_events if event.get("reason") == "output_safety_blocked"),
        "packet_safety_blocked": sum(1 for event in selected_events if event.get("reason") == "packet_safety_failed"),
        "circuit_breakers": sum(1 for event in selected_events if event.get("circuit_breaker_opened")),
    }
    report = {
        "report_type": "llm_private_test_reply_replay_closeout",
        "version": VERSION,
        "created_at": utc_now(),
        "live_success_fixture_verified": bool(fixture.get("verified")),
        "live_success_fixture": fixture,
        "summary": summary,
        "events": selected_events,
        "ready_for_phase33a_rag_preflight": bool(fixture.get("verified")),
        "message_sent": False,
        "live_discord_send_executed": False,
        "llm_api_called": False,
        "rag_called": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "raw_discord_ids_logged": False,
            "rag_called": False,
            "external_execution": False,
        },
    }
    assert_llm_private_test_reply_replay_safe(report)
    return report


def render_llm_private_test_reply_replay_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# LLM Private Test Reply Closeout",
        "",
        f"- Live success fixture verified: {str(report.get('live_success_fixture_verified')).lower()}",
        f"- Events replayed: {summary.get('events_replayed', 0)}",
        f"- Sent in fixture: {summary.get('sent', 0)}",
        f"- LLM calls in fixture: {summary.get('llm_calls', 0)}",
        f"- Discord send attempts in fixture: {summary.get('discord_send_attempts', 0)}",
        f"- Self-message skipped: {summary.get('self_messages_skipped', 0)}",
        f"- Public channel blocked: {summary.get('public_channel_blocked', 0)}",
        f"- Circuit breakers: {summary.get('circuit_breakers', 0)}",
        f"- Ready for Phase 33A RAG preflight: {str(report.get('ready_for_phase33a_rag_preflight')).lower()}",
        "",
        "## Safety",
        "- Replay Discord send: false",
        "- Replay LLM API call: false",
        "- RAG called: false",
        "- External execution: false",
    ]
    text = "\n".join(lines) + "\n"
    assert_llm_private_test_reply_replay_safe({"markdown": text})
    return text


def assert_llm_private_test_reply_replay_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if any(marker in text for marker in SECRET_MARKERS):
        raise ValueError("LLM private test reply replay contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("LLM private test reply replay contains raw Discord-like IDs.")
    if isinstance(report, dict):
        safety = report.get("safety_assertions", {})
        if safety.get("discord_message_sent") or safety.get("rag_called") or safety.get("external_execution"):
            raise ValueError("LLM private test reply replay safety assertions are unsafe.")
