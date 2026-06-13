"""Phase 31D private test reply safety closeout tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_private_test_reply_safety.py
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agent_placeholder_response import build_agent_placeholder_response
from discord_readonly_runtime import execute_private_test_reply_with_safety
from live_event_audit_persistence import build_live_event_audit_record, build_sample_visibility_event
from live_event_routing_report import build_live_event_routing_report
from private_test_reply import build_private_test_reply_payload, build_private_test_reply_policy
from private_test_reply_safety import (
    assert_private_test_reply_safety_report_safe,
    build_private_test_reply_safety_policy,
    build_private_test_reply_safety_report,
    build_private_test_reply_safety_state,
    check_private_test_reply_safety,
    record_private_test_reply_send_exception,
    record_private_test_reply_sent,
)


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def policy(**overrides: object) -> dict:
    env = {
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
        "HERMES_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS": "10",
        "HERMES_PRIVATE_TEST_MAX_REPLIES_PER_SESSION": "3",
        "HERMES_PRIVATE_TEST_RATE_LIMIT_CIRCUIT_BREAKER": "true",
        "HERMES_PRIVATE_TEST_DISABLE_AFTER_SEND_EXCEPTION": "true",
        "HERMES_DISCORD_LLM_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
    }
    env.update(overrides)
    return build_private_test_reply_safety_policy(env)


def event(message_id: str = "msg-1", channel_id: str = "private_test_channel", bot: bool = False) -> dict:
    return {
        "id": message_id,
        "channel_id": channel_id,
        "channel_name": "hermes-private-test",
        "author": {"id": "human" if not bot else "bot", "bot": bot},
    }


def placeholder_response() -> dict:
    visibility = build_sample_visibility_event()
    visibility["event_id"] = "event_redacted_0000"
    audit = build_live_event_audit_record(visibility, content="private safety test")
    routing = build_live_event_routing_report(audit)
    return build_agent_placeholder_response(audit, routing)


class MockChannel:
    def __init__(self, channel_id: str = "private_test_channel", fail: Exception | None = None) -> None:
        self.id = channel_id
        self.name = "hermes-private-test"
        self.sent: list[str] = []
        self.fail = fail

    async def send(self, content: str) -> None:
        if self.fail:
            raise self.fail
        self.sent.append(content)


class MockMessage:
    def __init__(self, message_id: str = "msg-1", channel_id: str = "private_test_channel", bot: bool = False, fail: Exception | None = None) -> None:
        self.id = message_id
        self.channel_id = channel_id
        self.channel_name = "hermes-private-test"
        self.channel = MockChannel(channel_id=channel_id, fail=fail)
        self.author = type("Author", (), {"id": "bot" if bot else "human", "bot": bot})()


def runtime_policy() -> dict:
    return build_private_test_reply_policy(
        {
            "HERMES_DISCORD_SEND_MESSAGES": "true",
            "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
            "HERMES_DISCORD_REPLY_MODE": "private_test_only",
            "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
            "HERMES_DISCORD_LLM_ENABLED": "false",
            "HERMES_DISCORD_RAG_ENABLED": "false",
            "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        }
    )


def test_default_policy_values() -> None:
    selected = build_private_test_reply_safety_policy({})
    assert_true(selected["cooldown_seconds"] == 10, "Default cooldown should be 10 seconds")
    assert_true(selected["max_replies_per_session"] == 3, "Default max replies should be 3")


def test_first_human_private_test_event_allowed() -> None:
    decision = check_private_test_reply_safety(event(), policy(), build_private_test_reply_safety_state())
    assert_true(decision["allowed"] is True, "First human private test event should be allowed")


def test_duplicate_message_id_blocked() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_sent(event("msg-dup"), state, now="2026-06-13T00:00:00+00:00")
    decision = check_private_test_reply_safety(event("msg-dup"), policy(), state, now="2026-06-13T00:00:20+00:00")
    assert_true(decision["reason"] == "duplicate_message", "Duplicate message should block")


def test_cooldown_active_blocked() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_sent(event("msg-a"), state, now="2026-06-13T00:00:00+00:00")
    decision = check_private_test_reply_safety(event("msg-b"), policy(), state, now="2026-06-13T00:00:05+00:00")
    assert_true(decision["reason"] == "cooldown_active", "Cooldown should block before expiry")


def test_cooldown_expired_allowed() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_sent(event("msg-a"), state, now="2026-06-13T00:00:00+00:00")
    decision = check_private_test_reply_safety(event("msg-b"), policy(), state, now="2026-06-13T00:00:11+00:00")
    assert_true(decision["allowed"] is True, "Cooldown expiry should allow next message")


def test_max_replies_reached_blocked() -> None:
    state = build_private_test_reply_safety_state()
    for index in range(3):
        record_private_test_reply_sent(event(f"msg-{index}"), state, now=f"2026-06-13T00:00:{index * 11:02d}+00:00")
    decision = check_private_test_reply_safety(event("msg-4"), policy(), state, now="2026-06-13T00:01:00+00:00")
    assert_true(decision["reason"] == "reply_budget_exhausted", "Max session reply budget should block")


def test_circuit_breaker_open_blocked() -> None:
    state = build_private_test_reply_safety_state()
    state["circuit_breaker_open"] = True
    state["circuit_breaker_reason"] = "manual"
    decision = check_private_test_reply_safety(event("msg-c"), policy(), state)
    assert_true(decision["reason"] == "circuit_breaker_open", "Open circuit breaker should block")


def test_send_exception_opens_circuit_breaker() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_send_exception(event("msg-error"), state, error_type="SendError")
    decision = check_private_test_reply_safety(event("msg-next"), policy(), state)
    assert_true(decision["reason"] == "send_exception_seen", "Send exception should open circuit breaker")


def test_rate_limit_opens_circuit_breaker() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_send_exception(event("msg-429"), state, error_type="HTTP 429 rate limited")
    decision = check_private_test_reply_safety(event("msg-next"), policy(), state)
    assert_true(decision["reason"] == "rate_limit_seen", "Rate limit should open circuit breaker")


def test_self_and_bot_message_blocked() -> None:
    ignored = dict(event("msg-self"))
    ignored["decision"] = "ignored_self_message"
    assert_true(check_private_test_reply_safety(ignored, policy(), build_private_test_reply_safety_state())["reason"] == "self_message", "Self message should block")
    assert_true(check_private_test_reply_safety(event("msg-bot", bot=True), policy(), build_private_test_reply_safety_state())["reason"] == "bot_message", "Bot message should block")


def test_non_private_channel_blocked() -> None:
    decision = check_private_test_reply_safety(event("msg-public", channel_id="marketing_channel"), policy(), build_private_test_reply_safety_state())
    assert_true(decision["reason"] == "not_private_test_channel", "Non-private channel should block")


def test_report_safe() -> None:
    report = build_private_test_reply_safety_report(policy(), build_private_test_reply_safety_state())
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_private_test_reply_safety_report_safe(report)
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Report should not contain token markers")
    assert_true(not LONG_NUMBER_RE.search(text), "Report should not contain raw Discord IDs")
    assert_true(report["message_sent"] is False and report["llm_called"] is False, "Report execution flags should stay false")


def test_policy_llm_rag_external_false() -> None:
    selected = policy()
    assert_true(selected["llm_enabled"] is False, "LLM flag should remain false")
    assert_true(selected["rag_enabled"] is False, "RAG flag should remain false")
    assert_true(selected["external_execution"] is False, "External execution flag should remain false")


def test_state_message_sent_false_after_record_sent() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_sent(event("msg-state"), state)
    assert_true(state["message_sent"] is False, "Safety state should not represent Discord send side effect as enabled")


def test_send_exception_report_safe() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_send_exception(event("msg-report-exc"), state, error_type="SendError")
    report = build_private_test_reply_safety_report(policy(), state)
    assert_true(report["state"]["circuit_breaker_open"] is True, "Report should show circuit breaker open")
    assert_private_test_reply_safety_report_safe(report)


def test_rate_limit_report_safe() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_send_exception(event("msg-report-429"), state, error_type="429 Too Many Requests")
    report = build_private_test_reply_safety_report(policy(), state)
    assert_true(report["state"]["circuit_breaker_reason"] == "rate_limit", "Report should preserve rate limit circuit breaker reason")
    assert_private_test_reply_safety_report_safe(report)


def test_runtime_allowed_human_message_path_one_send() -> None:
    message = MockMessage("msg-runtime-1")
    payload = build_private_test_reply_payload(message, placeholder_response(), runtime_policy())
    state = build_private_test_reply_safety_state()
    result = asyncio.run(execute_private_test_reply_with_safety(message, payload, runtime_policy(), policy(HERMES_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS="0"), state))
    assert_true(result["sent"] is True, "Runtime helper should send allowed human private test message")
    assert_true(len(message.channel.sent) == 1, "Runtime helper should send exactly once")
    assert_true(state["reply_count"] == 1, "Runtime helper should record one reply")


def test_runtime_ignored_self_message_never_sends() -> None:
    message = MockMessage("msg-runtime-self", bot=True)
    payload = build_private_test_reply_payload(message, placeholder_response(), runtime_policy())
    state = build_private_test_reply_safety_state()
    result = asyncio.run(execute_private_test_reply_with_safety(message, payload, runtime_policy(), policy(), state))
    assert_true(result["sent"] is False, "Runtime helper should not send bot/self message")
    assert_true(len(message.channel.sent) == 0, "Self message should never call send")


def test_runtime_duplicate_message_never_sends() -> None:
    message = MockMessage("msg-runtime-dup")
    payload = build_private_test_reply_payload(message, placeholder_response(), runtime_policy())
    state = build_private_test_reply_safety_state()
    record_private_test_reply_sent(event("msg-runtime-dup"), state, now="2026-06-13T00:00:00+00:00")
    result = asyncio.run(execute_private_test_reply_with_safety(message, payload, runtime_policy(), policy(), state))
    assert_true(result["sent"] is False, "Runtime helper should not send duplicate message")
    assert_true(len(message.channel.sent) == 0, "Duplicate message should not call send")


def test_runtime_budget_exhausted_never_sends() -> None:
    message = MockMessage("msg-runtime-budget")
    payload = build_private_test_reply_payload(message, placeholder_response(), runtime_policy())
    state = build_private_test_reply_safety_state()
    for index in range(3):
        record_private_test_reply_sent(event(f"budget-{index}"), state, now=f"2026-06-13T00:00:{index * 11:02d}+00:00")
    result = asyncio.run(execute_private_test_reply_with_safety(message, payload, runtime_policy(), policy(), state))
    assert_true(result["sent"] is False, "Runtime helper should not send after budget exhausted")
    assert_true(len(message.channel.sent) == 0, "Budget exhausted should not call send")


def main() -> int:
    tests = [
        test_default_policy_values,
        test_first_human_private_test_event_allowed,
        test_duplicate_message_id_blocked,
        test_cooldown_active_blocked,
        test_cooldown_expired_allowed,
        test_max_replies_reached_blocked,
        test_circuit_breaker_open_blocked,
        test_send_exception_opens_circuit_breaker,
        test_rate_limit_opens_circuit_breaker,
        test_self_and_bot_message_blocked,
        test_non_private_channel_blocked,
        test_report_safe,
        test_policy_llm_rag_external_false,
        test_state_message_sent_false_after_record_sent,
        test_send_exception_report_safe,
        test_rate_limit_report_safe,
        test_runtime_allowed_human_message_path_one_send,
        test_runtime_ignored_self_message_never_sends,
        test_runtime_duplicate_message_never_sends,
        test_runtime_budget_exhausted_never_sends,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private test reply safety tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
