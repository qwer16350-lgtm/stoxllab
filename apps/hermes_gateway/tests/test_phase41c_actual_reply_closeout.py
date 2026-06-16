from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase41c_actual_reply_closeout import build_phase41c_actual_reply_closeout


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_closeout_fixtures() -> None:
    success = build_phase41c_actual_reply_closeout()
    assert_true(success["actual_private_test_reply_verified"] is True, "Single private success")
    assert_true(success["message_sent_count"] == 1, "Observed count 1")
    assert_true(success["sent_scope"] == "private_test_only", "Private-test scope")
    assert_true(success["phase41b_message_sent_count_locked"] == 1, "Locked count")
    assert_true(success["ready_for_repeat_send"] is False, "No repeat")
    assert_true(success["ready_for_supervised_session"] is False, "No direct supervised session")
    assert_true(success["ready_for_phase42_supervised_deterministic_session_manual_gate"] is True, "Ready for Phase 42 manual gate")
    assert_true(success["discord_api_send_called"] is False, "No Phase 41C API send")
    assert_true(success["discord_message_sent"] is False, "No Phase 41C message")
    assert_true(success["discord_api_send_called_during_phase41c"] is False, "No API during 41C")
    assert_true(success["discord_message_sent_during_phase41c"] is False, "No message during 41C")
    assert_true(success["failed_previous_attempt_message_sent_count"] == 0, "Failed attempt count 0")
    assert_true(success["final_success_attempt_counted_as_success"] is True, "Final success counted")
    no_send = build_phase41c_actual_reply_closeout({})
    assert_true(no_send["no_send_closeout"] is True, "No-send closeout")
    assert_true(no_send["ready_for_supervised_session"] is False, "No send not ready")
    multi = build_phase41c_actual_reply_closeout({"message_sent_count": 2, "sent_channel_scope": "private_test"})
    assert_true(multi["failure"] is True, "Multi-send failure")
    public = build_phase41c_actual_reply_closeout({"message_sent_count": 1, "sent_channel_scope": "public"})
    assert_true(public["failure"] is True, "Public failure")
    repeat = build_phase41c_actual_reply_closeout({"message_sent_count": 1, "sent_channel_scope": "private_test", "repeat_send_attempted": True})
    assert_true(repeat["repeat_send_blocked"] is True, "Repeat blocked")


def test_ignored_and_redacted() -> None:
    report = build_phase41c_actual_reply_closeout({"self_loop_message": True, "bot_message": True, "duplicate_message": True})
    assert_true(report["self_loop_ignored"] is True, "Self-loop ignored")
    assert_true(report["bot_message_ignored"] is True, "Bot ignored")
    assert_true(report["duplicate_message_ignored"] is True, "Duplicate ignored")
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true(report["raw_discord_session_id_logged"] is False, "No session ID")
    assert_true(report["raw_content_logged"] is False, "No raw content")


def main() -> int:
    for test in (test_closeout_fixtures, test_ignored_and_redacted):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 41C tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
