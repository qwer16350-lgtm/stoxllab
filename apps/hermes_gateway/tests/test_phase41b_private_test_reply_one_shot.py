from __future__ import annotations

import json
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
        "HERMES_PHASE41B_MANUAL_APPROVAL": "true",
        "HERMES_PHASE41B_APPROVAL_PHRASE": "I_APPROVE_PHASE41B_PRIVATE_TEST_REPLY_ONE_SHOT",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
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
    assert_no_send(report)


def test_gate_blocks() -> None:
    cases = [
        ({}, "token_present"),
        ({"DISCORD_BOT_TOKEN": "SENSITIVE_TOKEN_VALUE_DO_NOT_LOG"}, "private_test_channel_id_present"),
        ({**ready_env(), "HERMES_PHASE41B_MANUAL_APPROVAL": "false"}, "manual_approval_true"),
        ({**ready_env(), "HERMES_PHASE41B_APPROVAL_PHRASE": "wrong"}, "approval_phrase_match"),
        ({**ready_env(), "HERMES_DISCORD_SEND_MESSAGES": "false"}, "send_messages_enabled"),
        ({**ready_env(), "HERMES_DISCORD_PRIVATE_TEST_REPLY": "false"}, "private_test_reply_enabled"),
        ({**ready_env(), "HERMES_DISCORD_REPLY_MODE": "team"}, "reply_mode_private_test_only"),
    ]
    for env, failed_check in cases:
        report = build_phase41b_private_test_reply_one_shot(env, allow_actual_private_test_reply=True)
        assert_true(failed_check in report["blocked_reasons"], failed_check)
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
    assert_true("one_shot_lock_not_consumed" in locked["blocked_reasons"], "Lock consumed")


def test_no_sensitive_values() -> None:
    report = build_phase41b_private_test_reply_one_shot(ready_env(), allow_actual_private_test_reply=True)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sensitive_token_value_do_not_log" not in text, "No token value")
    assert_true("sensitive_channel_value_do_not_log" not in text, "No channel value")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    for test in (test_default_blocked, test_gate_blocks, test_public_self_bot_duplicate_and_lock_blocks, test_no_sensitive_values):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 41B tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
