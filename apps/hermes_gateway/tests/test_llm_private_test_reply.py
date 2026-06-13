"""Phase 32D guarded private test LLM reply tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_private_test_reply.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from discord_readonly_runtime import build_private_test_llm_reply_runtime_preflight, run_discord_private_test_reply_bot, run_readonly_discord_bot
from discord_safety_wrapper import is_outgoing_action_allowed
from llm_private_test_reply import (
    build_llm_private_test_reply_attempt,
    build_llm_private_test_reply_payload,
    build_llm_private_test_reply_preflight,
    build_llm_private_test_reply_request,
    record_llm_private_test_reply_result,
    send_llm_private_test_reply_only,
    should_allow_llm_private_test_reply,
)
from private_test_reply_safety import build_private_test_reply_safety_state, record_private_test_reply_send_exception


ROOT = APP_DIR.parents[1]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def allowed_env(**overrides: object) -> dict[str, object]:
    env: dict[str, object] = {
        "token_present": True,
        "send_messages": True,
        "private_test_reply_enabled": True,
        "reply_mode": "private_test_only",
        "_private_test_channel_id": "private_test_channel",
        "external_execution": False,
        "rag_enabled": False,
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "HERMES_LLM_ENABLED": "true",
        "HERMES_LLM_API_CALL_ENABLED": "true",
        "HERMES_LLM_PROVIDER": "openrouter",
        "HERMES_LLM_MODEL": "openai/gpt-5.4-mini",
        "HERMES_LLM_API_KEY": "present",
        "HERMES_LLM_DRY_RUN_ONLY": "false",
        "HERMES_LLM_DRY_CALL_MODE": "private_test_only",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "true",
        "HERMES_LLM_PRIVATE_TEST_ONLY": "true",
        "HERMES_LLM_COST_GUARD_ENABLED": "true",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "true",
        "HERMES_LLM_PRIVATE_TEST_REPLY_MODE": "private_test_only",
        "HERMES_LLM_PRIVATE_TEST_REPLY_REQUIRE_PACKET": "true",
        "HERMES_LLM_PRIVATE_TEST_REPLY_MAX_PER_SESSION": "3",
        "HERMES_LLM_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS": "15",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_LLM_EXTERNAL_EXECUTION": "false",
    }
    env.update(overrides)
    return env


def private_event(**overrides: object) -> dict[str, object]:
    event: dict[str, object] = {
        "id": "msg-1",
        "channel_id": "private_test_channel",
        "channel_name": "hermes-private-test",
        "content": "마린, private test LLM reply draft please.",
        "author": {"id": "human_user", "bot": False},
    }
    event.update(overrides)
    return event


def success_result() -> dict:
    text = "This is a review-only draft. No external action has been taken.\n\n초안 검토용 답변입니다."
    return {
        "result_type": "llm_client_result",
        "version": "phase32d_guarded_private_test_only",
        "provider": "openrouter",
        "model": "openai/gpt-5.4-mini",
        "api_call_attempted": True,
        "api_call_succeeded": True,
        "api_call_failed": False,
        "error_type": None,
        "response_text": text,
        "usage": {"input_chars": 10, "output_chars": len(text), "estimated_cost_krw": 0.001, "provider_usage": {"total_tokens": 20}},
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def provider_error_result() -> dict:
    result = success_result()
    result.update({"api_call_succeeded": False, "api_call_failed": True, "error_type": "provider_error", "response_text": ""})
    return result


def unsafe_result() -> dict:
    result = success_result()
    result["response_text"] = "I published it."
    return result


def test_preflight_blocks_when_llm_private_test_reply_disabled() -> None:
    report = build_llm_private_test_reply_preflight(allowed_env(HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"))
    assert_true(report["ready"] is False, "Disabled LLM private reply should block")
    assert_true("llm_private_test_reply_disabled" in report["blocked_reasons"], "Block reason should be explicit")


def test_preflight_blocks_when_discord_send_disabled() -> None:
    assert_true("discord_send_disabled" in build_llm_private_test_reply_preflight(allowed_env(HERMES_DISCORD_SEND_MESSAGES="false", send_messages=False))["blocked_reasons"], "Discord send disabled should block")


def test_preflight_blocks_when_llm_discord_send_disabled() -> None:
    assert_true("llm_discord_send_disabled" in build_llm_private_test_reply_preflight(allowed_env(HERMES_LLM_DISCORD_SEND_ENABLED="false"))["blocked_reasons"], "LLM Discord send flag disabled should block")


def test_preflight_blocks_when_private_channel_missing() -> None:
    assert_true("private_test_channel_id_missing" in build_llm_private_test_reply_preflight(allowed_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID="", _private_test_channel_id=""))["blocked_reasons"], "Missing private channel should block")


def test_preflight_blocks_when_reply_mode_wrong() -> None:
    assert_true("reply_mode_not_private_test_only" in build_llm_private_test_reply_preflight(allowed_env(HERMES_DISCORD_REPLY_MODE="disabled", reply_mode="disabled"))["blocked_reasons"], "Wrong reply mode should block")


def test_preflight_blocks_rag_and_external() -> None:
    assert_true("rag_enabled" in build_llm_private_test_reply_preflight(allowed_env(HERMES_LLM_RAG_ENABLED="true"))["blocked_reasons"], "RAG should block")
    assert_true("external_execution_enabled" in build_llm_private_test_reply_preflight(allowed_env(HERMES_LLM_EXTERNAL_EXECUTION="true"))["blocked_reasons"], "External execution should block")


def test_preflight_ready_when_all_gates_true() -> None:
    report = build_llm_private_test_reply_preflight(allowed_env())
    assert_true(report["ready"] is True, "All gates true should pass preflight")
    assert_true(report["blocked"] is False, "Ready preflight should not be blocked")


def test_runtime_preflight_requires_token() -> None:
    report = build_private_test_llm_reply_runtime_preflight(ROOT, allowed_env(token_present=False))
    assert_true(report["ready"] is False, "Runtime preflight should require token presence")
    assert_true("token_missing" in report["blocked_reasons"], "Token missing should be explicit")


def test_public_mapped_channel_blocked() -> None:
    decision = should_allow_llm_private_test_reply(private_event(channel_id="marketing_channel"), "accepted_mapped_channel", {"allowed": True}, build_llm_private_test_reply_preflight(allowed_env()))
    assert_true(decision["reason"] == "private_test_channel_only", "Mapped public channel should block")


def test_private_channel_id_mismatch_blocked() -> None:
    decision = should_allow_llm_private_test_reply(private_event(channel_id="other"), "ignored_unmapped_channel", {"allowed": True}, build_llm_private_test_reply_preflight(allowed_env()))
    assert_true(decision["reason"] == "private_test_channel_only", "ID mismatch should not pass by channel name")


def test_self_and_bot_message_block_before_llm() -> None:
    preflight = build_llm_private_test_reply_preflight(allowed_env())
    self_decision = should_allow_llm_private_test_reply(private_event(author={"id": "bot", "bot": False}), "accepted_private_test_channel", {"allowed": True}, preflight, bot_user_id="bot")
    bot_decision = should_allow_llm_private_test_reply(private_event(author={"id": "bot2", "bot": True}), "accepted_private_test_channel", {"allowed": True}, preflight)
    assert_true(self_decision["will_call_llm"] is False and self_decision["reason"] == "self_message", "Self message should block before LLM")
    assert_true(bot_decision["will_call_llm"] is False and bot_decision["reason"] == "self_message", "Bot message should block before LLM")


def test_duplicate_message_blocks_before_llm() -> None:
    state = build_private_test_reply_safety_state()
    state["processed_message_ids"] = ["message_hash:" + hashlib.sha256("msg-1".encode("utf-8")).hexdigest()[:16]]
    attempt = build_llm_private_test_reply_attempt(private_event(), env=allowed_env(), safety_state=state, llm_result=success_result())
    assert_true(attempt["allowed"] is False, "Duplicate should block")
    assert_true(attempt["llm_api_called"] is False, "Duplicate should block before LLM")


def test_cooldown_blocks_before_llm() -> None:
    state = build_private_test_reply_safety_state()
    state["last_reply_at"] = "2999-01-01T00:00:00+00:00"
    attempt = build_llm_private_test_reply_attempt(private_event(id="msg-2"), env=allowed_env(), safety_state=state, llm_result=success_result())
    assert_true(attempt["allowed"] is False, "Cooldown should block")
    assert_true(attempt["llm_api_called"] is False, "Cooldown should block before LLM")


def test_budget_exhausted_blocks_before_llm() -> None:
    state = build_private_test_reply_safety_state()
    state["reply_count"] = 3
    attempt = build_llm_private_test_reply_attempt(private_event(id="msg-3"), env=allowed_env(), safety_state=state, llm_result=success_result())
    assert_true(attempt["allowed"] is False, "Budget should block")
    assert_true(attempt["llm_api_called"] is False, "Budget should block before LLM")


def test_provider_error_blocks_send() -> None:
    attempt = build_llm_private_test_reply_attempt(private_event(id="msg-4"), env=allowed_env(), llm_result=provider_error_result())
    assert_true(attempt["allowed"] is False, "Provider error should block")
    assert_true(attempt["message_sent"] is False, "Provider error should not send")


def test_output_safety_blocked_response_blocks_send() -> None:
    attempt = build_llm_private_test_reply_attempt(private_event(id="msg-5"), env=allowed_env(), llm_result=unsafe_result())
    assert_true(attempt["allowed"] is False, "Unsafe output should block")
    assert_true(attempt["reason"] == "output_safety_blocked", "Output safety block should be explicit")


def test_packet_safety_failure_blocks_send() -> None:
    decision = should_allow_llm_private_test_reply(
        private_event(),
        "accepted_private_test_channel",
        {"allowed": True},
        build_llm_private_test_reply_preflight(allowed_env()),
        {"allowed": True},
        {"response_available": True, "response_text": "123456789012345678", "message_sent": False, "discord_send_attempted": False, "rag_called": False, "external_execution": False, "safety_assertions": {}},
    )
    assert_true(decision["reason"] == "packet_safety_failed", "Unsafe packet should block")


def test_successful_allowed_response_sends_once() -> None:
    attempt = build_llm_private_test_reply_attempt(private_event(id="msg-6"), env=allowed_env(), llm_result=success_result())
    payload = build_llm_private_test_reply_payload(attempt["packet"])

    class Channel:
        def __init__(self) -> None:
            self.sent: list[str] = []

        async def send(self, content: str) -> None:
            self.sent.append(content)

    channel = Channel()
    send_result = asyncio.run(send_llm_private_test_reply_only(channel, payload))
    assert_true(attempt["allowed"] is True, "Safe response should be allowed")
    assert_true(send_result["message_sent"] is True, "Mock send should succeed")
    assert_true(len(channel.sent) == 1, "Exactly one message should be sent")


def test_bot_self_echo_skipped_after_send() -> None:
    decision = should_allow_llm_private_test_reply(private_event(author={"id": "bot", "bot": True}), "ignored_self_message", {"allowed": True}, build_llm_private_test_reply_preflight(allowed_env()))
    assert_true(decision["reason"] == "self_message", "Self echo should be skipped")
    assert_true(decision["will_call_llm"] is False, "Self echo must not call LLM")


def test_429_and_send_exception_open_circuit_breaker() -> None:
    state = build_private_test_reply_safety_state()
    record_private_test_reply_send_exception(private_event(id="msg-7"), state, "HTTPException 429")
    assert_true(state["circuit_breaker_open"] is True and state["circuit_breaker_reason"] == "rate_limit", "429 should open rate-limit circuit")
    state2 = build_private_test_reply_safety_state()
    record_private_test_reply_send_exception(private_event(id="msg-8"), state2, "RuntimeError")
    assert_true(state2["circuit_breaker_open"] is True and state2["circuit_breaker_reason"] == "send_exception", "Send exception should open circuit")


def test_safety_flags_false_in_blocked_cases() -> None:
    attempt = build_llm_private_test_reply_attempt(private_event(id="msg-9"), env=allowed_env(), llm_result=unsafe_result())
    assert_true(attempt["message_sent"] is False, "Blocked case should not send")
    assert_true(attempt["safety_assertions"]["rag_called"] is False, "RAG should stay false")
    assert_true(attempt["safety_assertions"]["external_execution"] is False, "External execution should stay false")


def test_no_api_key_or_raw_discord_id_logged() -> None:
    attempt = build_llm_private_test_reply_attempt(private_event(content="token=secret 123456789012345678"), env=allowed_env(HERMES_LLM_API_KEY="sk-secret"), llm_result=success_result())
    text = json.dumps(attempt, ensure_ascii=False).lower()
    assert_true("sk-secret" not in text and "token=secret" not in text, "Secrets should not be logged")
    assert_true(not LONG_ID_RE.search(text), "Raw Discord IDs should not be logged")


def test_deterministic_private_reply_mode_remains_separate() -> None:
    report = run_discord_private_test_reply_bot(ROOT, runtime_env=allowed_env(token_present=False, HERMES_DISCORD_LLM_ENABLED="false"))
    assert_true(report["started"] is False or report.get("preflight", {}).get("report_type") == "private_test_reply_runtime_preflight", "Placeholder runtime should remain separate")


def test_readonly_strict_behavior_unchanged() -> None:
    report = run_readonly_discord_bot(ROOT, runtime_env=allowed_env())
    assert_true(report["started"] is False, "Strict read-only should still block send_messages=true")
    assert_true(report["blocked"] is True, "Strict read-only should remain blocked")


def test_outgoing_wrapper_separates_placeholder_and_llm_send() -> None:
    assert_true(is_outgoing_action_allowed("private_test_reply_send", allowed_env(HERMES_DISCORD_LLM_ENABLED="false")) is True, "Placeholder exception should still work")
    assert_true(is_outgoing_action_allowed("private_test_llm_reply_send", allowed_env(llm_private_test_reply_enabled=True, llm_private_test_reply_mode="private_test_only", llm_discord_send_enabled=True)) is True, "LLM exception should be separate")
    assert_true(is_outgoing_action_allowed("message_create", allowed_env()) is False, "General message_create remains blocked")


def test_request_and_result_recording_possible() -> None:
    request = build_llm_private_test_reply_request(private_event(), "marin")
    record = record_llm_private_test_reply_result(private_event(), build_llm_private_test_reply_preflight(allowed_env()), {"allowed": False, "blocked": True, "reason": "test"}, request=request)
    assert_true(record["message_sent"] is False, "Record should not mark send by default")
    assert_true(record["request"]["request_type"] == "llm_private_test_reply_request", "Request should be included")


def main() -> int:
    tests = [
        test_preflight_blocks_when_llm_private_test_reply_disabled,
        test_preflight_blocks_when_discord_send_disabled,
        test_preflight_blocks_when_llm_discord_send_disabled,
        test_preflight_blocks_when_private_channel_missing,
        test_preflight_blocks_when_reply_mode_wrong,
        test_preflight_blocks_rag_and_external,
        test_preflight_ready_when_all_gates_true,
        test_runtime_preflight_requires_token,
        test_public_mapped_channel_blocked,
        test_private_channel_id_mismatch_blocked,
        test_self_and_bot_message_block_before_llm,
        test_duplicate_message_blocks_before_llm,
        test_cooldown_blocks_before_llm,
        test_budget_exhausted_blocks_before_llm,
        test_provider_error_blocks_send,
        test_output_safety_blocked_response_blocks_send,
        test_packet_safety_failure_blocks_send,
        test_successful_allowed_response_sends_once,
        test_bot_self_echo_skipped_after_send,
        test_429_and_send_exception_open_circuit_breaker,
        test_safety_flags_false_in_blocked_cases,
        test_no_api_key_or_raw_discord_id_logged,
        test_deterministic_private_reply_mode_remains_separate,
        test_readonly_strict_behavior_unchanged,
        test_outgoing_wrapper_separates_placeholder_and_llm_send,
        test_request_and_result_recording_possible,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM private test reply tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
