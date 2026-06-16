from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40w_synthetic_private_test_replay import build_synthetic_event
from phase40y_phase41_reply_preflight_gate import EXPECTED_APPROVAL_PHRASE, build_phase40y_phase41_reply_preflight_gate


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env(**overrides: str) -> dict[str, str]:
    env = {
        "DISCORD_BOT_TOKEN": "present",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "present",
        "HERMES_PHASE41_PRIVATE_TEST_REPLY_APPROVED": "true",
        "HERMES_PHASE41_PRIVATE_TEST_REPLY_APPROVAL_PHRASE": EXPECTED_APPROVAL_PHRASE,
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_RAG_LLM_REPLY_ENABLED": "false",
        "HERMES_EMBEDDING_API_ENABLED": "false",
        "HERMES_VECTOR_INDEX_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
    }
    env.update(overrides)
    return env


def assert_no_send(report: dict[str, object]) -> None:
    assert_true(report["actual_reply_send_executed"] is False, "No actual reply")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")
    assert_true(report["ready_for_actual_reply_send"] is False, "No actual send readiness")


def test_default_blocked() -> None:
    report = build_phase40y_phase41_reply_preflight_gate()
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true(report["blocked"] is True, "Blocked")
    assert_no_send(report)


def test_ready_conditions_still_no_actual_send() -> None:
    report = build_phase40y_phase41_reply_preflight_gate(env=ready_env(), event=build_synthetic_event())
    assert_true(report["blocked"] is False, "Preflight can become ready")
    assert_true(report["ready_for_phase41_manual_private_test_reply"] is True, "Manual preflight ready")
    assert_no_send(report)


def test_negative_matrix_blocks() -> None:
    cases = [
        (ready_env(HERMES_PHASE41_PRIVATE_TEST_REPLY_APPROVED="false"), build_synthetic_event(), "approval_missing"),
        (ready_env(HERMES_PHASE41_PRIVATE_TEST_REPLY_APPROVAL_PHRASE="wrong"), build_synthetic_event(), "approval_phrase_mismatch"),
        (ready_env(DISCORD_BOT_TOKEN=""), build_synthetic_event(), "token_missing_before_login"),
        (ready_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=""), build_synthetic_event(), "channel_missing_before_login"),
        (ready_env(HERMES_DISCORD_SEND_MESSAGES="false"), build_synthetic_event(), "send_messages_false"),
        (ready_env(HERMES_DISCORD_PRIVATE_TEST_REPLY="false"), build_synthetic_event(), "private_test_reply_false"),
        (ready_env(HERMES_DISCORD_REPLY_MODE="readonly_private_test_only"), build_synthetic_event(), "wrong_reply_mode"),
        (ready_env(), build_synthetic_event(channel_scope="public"), "public_or_team_channel"),
        (ready_env(), build_synthetic_event(author_type="self", is_self=True), "self_message"),
        (ready_env(), build_synthetic_event(author_type="bot", is_bot=True), "bot_message"),
        (ready_env(), build_synthetic_event(is_duplicate=True), "duplicate_message"),
        (ready_env(HERMES_LLM_DISCORD_SEND_ENABLED="true"), build_synthetic_event(), "llm_enabled"),
        (ready_env(HERMES_DISCORD_RAG_ENABLED="true"), build_synthetic_event(), "rag_enabled"),
        (ready_env(HERMES_EMBEDDING_API_ENABLED="true"), build_synthetic_event(), "embedding_enabled"),
        (ready_env(HERMES_DISCORD_EXTERNAL_EXECUTION="true"), build_synthetic_event(), "external_execution_enabled"),
    ]
    for env, event, reason in cases:
        report = build_phase40y_phase41_reply_preflight_gate(env=env, event=event)
        assert_true(report["blocked"] is True, reason)
        assert_true(report["block_reason"] == reason, reason)
        assert_no_send(report)
    consumed = build_phase40y_phase41_reply_preflight_gate(env=ready_env(), event=build_synthetic_event(), one_shot_lock_consumed=True)
    assert_true(consumed["block_reason"] == "one_shot_lock_consumed", "One-shot consumed")
    assert_no_send(consumed)


def main() -> int:
    for test in (test_default_blocked, test_ready_conditions_still_no_actual_send, test_negative_matrix_blocks):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40Y preflight gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
