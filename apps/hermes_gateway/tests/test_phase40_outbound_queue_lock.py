from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_outbound_queue_lock import build_phase40_outbound_queue_lock, render_phase40_outbound_queue_lock_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40e_outbound_queue_disabled() -> None:
    report = build_phase40_outbound_queue_lock()
    assert_true(report["outbound_queue_enabled"] is False, "Queue off")
    assert_true(report["queued_message_count"] == 0, "No queue")
    assert_true(report["send_worker_enabled"] is False, "Worker off")
    assert_true(report["send_worker_started"] is False, "Worker not started")
    assert_true(report["manual_retry_requires_new_phase"] is True, "Retry requires new phase")


def test_phase40e_no_send_or_retry() -> None:
    report = build_phase40_outbound_queue_lock()
    for key in ("discord_api_send_called", "discord_message_sent", "repeat_send_allowed", "automatic_retry_allowed", "unattended_auto_reply_allowed", "llm_api_call_attempted", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")


def test_phase40e_markdown() -> None:
    assert_true("Phase 40E" in render_phase40_outbound_queue_lock_markdown(build_phase40_outbound_queue_lock()), "Markdown")


def main() -> int:
    for test in (test_phase40e_outbound_queue_disabled, test_phase40e_no_send_or_retry, test_phase40e_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40E outbound queue lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
