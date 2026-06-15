from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_private_test_send_manual_preflight import build_actual_private_test_send_manual_preflight, render_actual_private_test_send_manual_preflight_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_manual_preflight_success_fixture() -> None:
    report = build_actual_private_test_send_manual_preflight(env={})
    assert_true(report["preflight_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase37a_review_packet_available"] is True, "37A")
    assert_true(report["source_phase37b_send_preflight_preview_available"] is True, "37B")
    assert_true(report["source_phase37c_approval_rehearsal_available"] is True, "37C")
    assert_true(report["preflight_ready_for_future_send_rehearsal"] is True, "Ready for rehearsal")


def test_manual_preflight_presence_and_no_send() -> None:
    report = build_actual_private_test_send_manual_preflight(env={"DISCORD_BOT_TOKEN": "token-value", "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "123456789012345678"})
    assert_true(report["discord_token_present"] is True, "Token presence")
    assert_true(report["private_test_channel_id_present"] is True, "Channel presence")
    assert_true(report["discord_token_value_logged"] is False, "No token value")
    assert_true(report["private_test_channel_id_value_logged"] is False, "No channel value")
    assert_true(report["manual_approval_required"] is True, "Manual required")
    assert_true(report["manual_approval_actualized"] is False, "No approval")
    assert_true(report["approval_phrase_generated"] is False, "No phrase")
    assert_true(report["discord_api_send_called"] is False, "No send API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")
    assert_true(report["ready_for_actual_private_test_send"] is False, "No actual send")
    assert_true(report["ready_for_discord_send"] is False, "No Discord send")


def test_manual_preflight_no_sensitive_values_and_markdown() -> None:
    report = build_actual_private_test_send_manual_preflight(env={"DISCORD_BOT_TOKEN": "token-value", "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "123456789012345678"})
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("token-value" not in text, "Token hidden")
    assert_true("123456789012345678" not in text, "Channel hidden")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Manual Preflight" in render_actual_private_test_send_manual_preflight_markdown(report), "Markdown")


def main() -> int:
    tests = [test_manual_preflight_success_fixture, test_manual_preflight_presence_and_no_send, test_manual_preflight_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual private-test send manual preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
