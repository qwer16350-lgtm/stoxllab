from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase41b_private_test_reply_one_shot import build_phase41b_env_diagnostics


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


def test_phase41b_env_diagnostics_process_env_booleans_only() -> None:
    env = ready_env()
    original = {key: os.environ.get(key) for key in env}
    try:
        os.environ.update(env)
        report = build_phase41b_env_diagnostics()
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    assert_true(report["report_type"] == "phase41b_env_diagnostics", "Report type")
    assert_true(report["token_present"] is True, "Token presence")
    assert_true(report["private_test_channel_id_present"] is True, "Channel presence")
    assert_true(report["manual_approval_present"] is True, "Approval presence")
    assert_true(report["manual_approval_true"] is True, "Approval true")
    assert_true(report["approval_phrase_present"] is True, "Phrase presence")
    assert_true(report["approval_phrase_exact_match"] is True, "Phrase match")
    assert_true(report["send_messages_enabled"] is True, "Send enabled")
    assert_true(report["private_test_reply_enabled"] is True, "Reply enabled")
    assert_true(report["reply_mode_private_test_only"] is True, "Reply mode")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No message count")
    text = json.dumps(report, ensure_ascii=False)
    assert_true("SENSITIVE_TOKEN_VALUE_DO_NOT_LOG" not in text, "No token value")
    assert_true("SENSITIVE_CHANNEL_VALUE_DO_NOT_LOG" not in text, "No channel value")
    assert_true("I_APPROVE_" not in text, "No phrase value")


def main() -> int:
    test_phase41b_env_diagnostics_process_env_booleans_only()
    print("PASS test_phase41b_env_diagnostics_process_env_booleans_only")
    print("All Phase 41B env diagnostics tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
