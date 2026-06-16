from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase41b_private_test_reply_one_shot import build_phase41b_private_test_reply_one_shot


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env() -> dict[str, str]:
    return {
        "DISCORD_BOT_TOKEN": "SENSITIVE_TOKEN_VALUE_DO_NOT_LOG",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "SENSITIVE_CHANNEL_VALUE_DO_NOT_LOG",
        "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVED": "true",
        "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE": "I_APPROVE_PHASE41B_PRIVATE_TEST_REPLY_ONE_SHOT",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_RAG_LLM_REPLY_ENABLED": "false",
    }


def assert_no_send(report: dict) -> None:
    assert_true(report["actual_reply_send_executed"] is False, "No actual reply")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["message_sent_count"] == 0, "Message count 0")


def test_default_blocked() -> None:
    report = build_phase41b_private_test_reply_one_shot()
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true(report["ready_for_manual_private_test_reply_one_shot"] is False, "Not ready")
    assert_true(report["actual_runtime_path_available"] is True, "Runtime path available")
    assert_true(report["real_discord_send_adapter_wired"] is True, "Real adapter wired")
    assert_true(report["fake_adapter_contract_passed"] is True, "Fake contract passed")
    assert_no_send(report)


def test_gate_blocks() -> None:
    cases = [
        ({}, "token_missing"),
        ({"DISCORD_BOT_TOKEN": "SENSITIVE_TOKEN_VALUE_DO_NOT_LOG"}, "private_test_channel_id_missing"),
        ({**ready_env(), "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVED": "false"}, "manual_approval_missing"),
        ({**ready_env(), "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE": "wrong"}, "approval_phrase_mismatch"),
        ({**ready_env(), "HERMES_DISCORD_SEND_MESSAGES": "false"}, "send_messages_disabled"),
        ({**ready_env(), "HERMES_DISCORD_PRIVATE_TEST_REPLY": "false"}, "private_test_reply_disabled"),
        ({**ready_env(), "HERMES_DISCORD_REPLY_MODE": "team"}, "reply_mode_not_private_test_only"),
    ]
    for env, failed_reason in cases:
        report = build_phase41b_private_test_reply_one_shot(env, allow_actual_private_test_reply=True)
        assert_true(failed_reason in report["blocked_reasons"], failed_reason)
        assert_true("token_present" not in report["blocked_reasons"], "Positive reason absent")
        assert_true("manual_approval_true" not in report["blocked_reasons"], "Positive reason absent")
        assert_true("send_messages_enabled" not in report["blocked_reasons"], "Positive reason absent")
        assert_no_send(report)


def test_public_self_bot_duplicate_and_lock_blocks() -> None:
    for event in (
        {"channel_scope": "public"},
        {"channel_scope": "team"},
        {"author_type": "self"},
        {"author_type": "bot"},
        {"duplicate": True},
    ):
        report = build_phase41b_private_test_reply_one_shot(ready_env(), allow_actual_private_test_reply=True, event=event)
        assert_true(report["blocked"] is True, "Guard blocks")
        assert_no_send(report)
    locked = build_phase41b_private_test_reply_one_shot(ready_env(), allow_actual_private_test_reply=True, one_shot_lock_consumed=True)
    assert_true("one_shot_lock_consumed" in locked["blocked_reasons"], "Lock consumed")


def test_process_env_gate_checks_true_without_actual_flag() -> None:
    env = ready_env()
    original = {key: os.environ.get(key) for key in env}
    try:
        os.environ.update(env)
        report = build_phase41b_private_test_reply_one_shot()
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    for key in (
        "token_present",
        "private_test_channel_id_present",
        "manual_approval_true",
        "approval_phrase_match",
        "send_messages_enabled",
        "private_test_reply_enabled",
        "reply_mode_private_test_only",
    ):
        assert_true(report["gate_checks"][key] is True, f"{key} true")
    assert_true(report["blocked"] is True, "Blocked without actual flag")
    assert_true(report["blocked_reasons"] == ["allow_actual_private_test_reply_flag_missing"], "Only actual flag missing")
    assert_true(report["gates_ready_but_actual_flag_missing"] is True, "Gates ready flag")
    assert_true(report["ready_for_phase41b_actual_private_test_reply_retry_manual_gate"] is True, "Ready for retry manual gate")
    assert_no_send(report)


def test_no_sensitive_values() -> None:
    report = build_phase41b_private_test_reply_one_shot(ready_env(), allow_actual_private_test_reply=True)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sensitive_token_value_do_not_log" not in text, "No token value")
    assert_true("sensitive_channel_value_do_not_log" not in text, "No channel value")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true(report["raw_discord_session_id_logged"] is False, "No raw session ID")
    assert_true(report["raw_content_logged"] is False, "No raw content")
    assert_true(report["send_result_error_value_logged"] is False, "No error value")


def main() -> int:
    for test in (test_default_blocked, test_gate_blocks, test_public_self_bot_duplicate_and_lock_blocks, test_process_env_gate_checks_true_without_actual_flag, test_no_sensitive_values):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 41B tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
