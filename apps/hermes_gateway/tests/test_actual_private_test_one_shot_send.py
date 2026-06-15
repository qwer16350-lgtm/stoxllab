from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_private_test_one_shot_send import build_actual_private_test_one_shot_send, render_actual_private_test_one_shot_send_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_one_shot_send_default_blocked_report() -> None:
    report = build_actual_private_test_one_shot_send(env={})
    assert_true(report["actual_send_path_available"] is True, "Path available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase39a_implementation_only"] is True, "Implementation only")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true("allow_flag_missing" in report["blocked_reasons"], "Allow flag missing")
    assert_true("phase39a_no_execution_policy" in report["blocked_reasons"], "Policy reason")


def test_one_shot_send_missing_conditions_block() -> None:
    report = build_actual_private_test_one_shot_send(env={})
    assert_true(report["allow_flag_present"] is False, "Allow false")
    assert_true(report["manual_approval_actualized"] is False, "Manual false")
    assert_true(report["discord_send_messages_enabled"] is False, "Send disabled")
    assert_true(report["private_test_reply_enabled"] is False, "Private reply disabled")
    assert_true(report["reply_mode_private_test_only"] is False, "Reply mode false")
    assert_true(report["discord_token_present"] is False, "Token missing")
    assert_true(report["private_test_channel_id_present"] is False, "Channel missing")


def test_one_shot_send_no_execution_or_readiness() -> None:
    report = build_actual_private_test_one_shot_send(env={})
    for key in ("actual_private_test_send_executed", "actual_send_executed", "discord_live_runtime_executed", "discord_api_send_called", "discord_message_sent", "ready_for_actual_private_test_send", "ready_for_discord_send", "ready_for_phase39b_manual_one_shot_send", "llm_api_call_attempted", "llm_api_called", "embedding_api_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_one_shot_send_no_sensitive_values_and_markdown() -> None:
    report = build_actual_private_test_one_shot_send(
        allow_flag_present=True,
        env={
            "DISCORD_BOT_TOKEN": "token-value",
            "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "123456789012345678",
            "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE": "I_APPROVE_STOXL_PRIVATE_TEST_DRAFT_SEND",
        },
    )
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("token-value" not in text, "Token value hidden")
    assert_true("123456789012345678" not in text, "Channel value hidden")
    assert_true("i_approve_" not in text, "Approval value hidden")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Actual Private-test One-shot Send Path" in render_actual_private_test_one_shot_send_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_one_shot_send_default_blocked_report,
        test_one_shot_send_missing_conditions_block,
        test_one_shot_send_no_execution_or_readiness,
        test_one_shot_send_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual private-test one-shot send tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
