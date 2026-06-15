from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from mock_private_test_send_rehearsal import build_mock_private_test_send_rehearsal, render_mock_private_test_send_rehearsal_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def test_mock_rehearsal_success_fixture() -> None:
    report = build_mock_private_test_send_rehearsal()
    assert_true(report["mock_rehearsal_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase37d_manual_preflight_available"] is True, "37D")
    assert_true(report["private_test_scope_only"] is True, "Private")
    assert_true(report["would_send_payload_created"] is True, "Payload")
    assert_true(report["ready_for_phase37f_no_send_lock"] is True, "Ready for lock")


def test_mock_rehearsal_counts_and_no_send() -> None:
    report = build_mock_private_test_send_rehearsal()
    assert_true(report["mock_send_rehearsal_count"] == 1, "Mock count")
    assert_true(report["actual_discord_api_send_called"] is False, "No API send")
    assert_true(report["actual_discord_message_sent"] is False, "No message")
    assert_true(report["actual_message_sent_count"] == 0, "No count")
    assert_true(report["would_send_review_only"] is True, "Review only")
    assert_true(report["would_send_external_action_claim"] is False, "No external claim")
    assert_true(report["would_send_full_content_included"] is False, "No full content")
    assert_true(report["public_channel_send_allowed"] is False, "No public")
    assert_true(report["team_channel_send_allowed"] is False, "No team")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")


def test_mock_rehearsal_fails_bad_scope() -> None:
    assert_raises(lambda: build_mock_private_test_send_rehearsal(scope="public"), "Public scope fails")


def test_mock_rehearsal_no_sensitive_values_and_markdown() -> None:
    report = build_mock_private_test_send_rehearsal()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Mock Private-test Send Rehearsal" in render_mock_private_test_send_rehearsal_markdown(report), "Markdown")


def main() -> int:
    tests = [test_mock_rehearsal_success_fixture, test_mock_rehearsal_counts_and_no_send, test_mock_rehearsal_fails_bad_scope, test_mock_rehearsal_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All mock private-test send rehearsal tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
