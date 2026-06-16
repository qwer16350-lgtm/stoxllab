from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_session_idempotency_lock import build_phase40_session_idempotency_lock, render_phase40_session_idempotency_lock_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40f_idempotency_guards_enabled() -> None:
    report = build_phase40_session_idempotency_lock()
    assert_true(report["dedupe_key_strategy"] == "message_id", "Message id dedupe")
    assert_true(report["one_reply_per_human_message"] is True, "One reply")
    assert_true(report["duplicate_message_id_guard"] is True, "Duplicate guard")
    assert_true(report["self_message_guard"] is True, "Self guard")
    assert_true(report["bot_message_guard"] is True, "Bot guard")
    assert_true(report["duplicate_send_prevented"] is True, "Duplicate prevented")


def test_phase40f_no_repeat_or_send() -> None:
    report = build_phase40_session_idempotency_lock()
    for key in ("repeat_send_allowed", "automatic_retry_allowed", "manual_retry_allowed", "unattended_auto_reply_allowed", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase40f_markdown() -> None:
    assert_true("Phase 40F" in render_phase40_session_idempotency_lock_markdown(build_phase40_session_idempotency_lock()), "Markdown")


def main() -> int:
    for test in (test_phase40f_idempotency_guards_enabled, test_phase40f_no_repeat_or_send, test_phase40f_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40F session idempotency lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
