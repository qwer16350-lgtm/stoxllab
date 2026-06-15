from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_private_test_send_blocked_report import build_actual_private_test_send_blocked_report, render_actual_private_test_send_blocked_report_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_blocked_report_success_fixture() -> None:
    report = build_actual_private_test_send_blocked_report()
    assert_true(report["blocked_report_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["phase39a_no_execution_policy"] is True, "No execution policy")
    assert_true("phase39a_no_execution_policy" in report["blocked_reason_categories"], "Policy reason")


def test_blocked_report_no_send_or_readiness() -> None:
    report = build_actual_private_test_send_blocked_report()
    for key in ("actual_send_executed", "actual_private_test_send_executed", "discord_live_runtime_executed", "discord_api_send_called", "discord_message_sent", "ready_for_actual_private_test_send", "ready_for_discord_send", "ready_for_phase39b_manual_one_shot_send"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_blocked_report_no_sensitive_values_and_markdown() -> None:
    report = build_actual_private_test_send_blocked_report()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Actual Private-test Send Blocked Report" in render_actual_private_test_send_blocked_report_markdown(report), "Markdown")


def main() -> int:
    tests = [test_blocked_report_success_fixture, test_blocked_report_no_send_or_readiness, test_blocked_report_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual private-test send blocked report tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
