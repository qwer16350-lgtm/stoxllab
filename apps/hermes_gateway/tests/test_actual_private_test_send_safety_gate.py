from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_private_test_send_safety_gate import build_actual_private_test_send_safety_gate, render_actual_private_test_send_safety_gate_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_safety_gate_success_fixture_default_blocked() -> None:
    report = build_actual_private_test_send_safety_gate(env={})
    assert_true(report["safety_gate_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["required_conditions"][0] == "allow_flag_present", "Conditions listed")
    assert_true(report["conditions_met"] is False, "Conditions false")
    assert_true(report["actual_send_allowed"] is False, "Actual send not allowed")
    assert_true(report["actual_send_executed"] is False, "Actual send not executed")


def test_safety_gate_blocks_missing_inputs() -> None:
    report = build_actual_private_test_send_safety_gate(env={})
    values = report["condition_values"]
    assert_true(values["allow_flag_present"] is False, "Allow flag missing")
    assert_true(values["manual_approval_flag_true"] is False, "Manual approval missing")
    assert_true(values["discord_send_messages_true"] is False, "Send disabled")
    assert_true(values["reply_mode_private_test_only"] is False, "Reply mode missing")
    assert_true(values["discord_token_present"] is False, "Token missing")
    assert_true(values["private_test_channel_id_present"] is False, "Channel missing")


def test_safety_gate_no_send_or_llm_or_external() -> None:
    report = build_actual_private_test_send_safety_gate(env={})
    for key in ("discord_api_send_called", "discord_message_sent", "actual_send_executed", "actual_private_test_send_executed", "llm_api_call_attempted", "llm_api_called", "embedding_api_called", "external_execution", "ready_for_discord_send", "ready_for_phase39b_manual_one_shot_send"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_safety_gate_no_sensitive_values_and_markdown() -> None:
    report = build_actual_private_test_send_safety_gate(
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
    assert_true("i_approve_" not in text, "Approval phrase value hidden")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Actual Private-test Send Safety Gate" in render_actual_private_test_send_safety_gate_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_safety_gate_success_fixture_default_blocked,
        test_safety_gate_blocks_missing_inputs,
        test_safety_gate_no_send_or_llm_or_external,
        test_safety_gate_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual private-test send safety gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
