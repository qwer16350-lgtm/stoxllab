from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase51_readonly_event_guard import build_phase51_readonly_event_guard, guard_readonly_event
from phase51_readonly_event_schema import normalize_readonly_event


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase51_guard_contract() -> None:
    report = build_phase51_readonly_event_guard()
    assert_true(report["report_type"] == "phase51_readonly_event_guard", "Report type")
    assert_true(report["event_allowed_for_review_packet"] is True, "Review packet allowed")
    assert_true(report["event_allowed_for_reply"] is False, "No reply")
    assert_true(report["discord_send_allowed"] is False, "No send")
    assert_true(report["self_message_ignored"] is True, "Self ignored")
    assert_true(report["bot_message_ignored"] is True, "Bot ignored")
    assert_true(report["duplicate_message_ignored"] is True, "Duplicate ignored")
    assert_true(report["operator_command_detected"] is True, "Command detected")


def test_phase51_guard_blocks_public_high() -> None:
    normalized = normalize_readonly_event(
        {
            "event_ref": "evt_public_synthetic",
            "source": "discord",
            "channel_scope": "public",
            "author_kind": "human",
            "content": "public request",
        }
    )
    guard = guard_readonly_event(normalized)
    assert_true(guard["event_allowed_for_review_packet"] is False, "Public high blocked from packet automation")
    assert_true(guard["public_high_risk_detected"] is True, "Public high detected")
    assert_true(guard["event_allowed_for_reply"] is False, "No reply")
    assert_true(guard["discord_send_allowed"] is False, "No send")


def test_phase51_guard_no_sensitive_values() -> None:
    text = json.dumps(build_phase51_readonly_event_guard(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase51_guard_contract, test_phase51_guard_blocks_public_high, test_phase51_guard_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase51 read-only event guard tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
