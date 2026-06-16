from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase41_private_test_reply_preflight import build_phase41_private_test_reply_preflight


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase41_preflight_default_blocked_no_send() -> None:
    report = build_phase41_private_test_reply_preflight()
    assert_true(report["report_type"] == "phase41_private_test_reply_preflight", "Report type")
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["actual_reply_send_executed"] is False, "No actual reply")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "Count 0")
    assert_true(report["ready_for_manual_private_test_reply"] is False, "Not ready")


def main() -> int:
    test_phase41_preflight_default_blocked_no_send()
    print("PASS test_phase41_preflight_default_blocked_no_send")
    print("All Phase 41 private-test reply preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
