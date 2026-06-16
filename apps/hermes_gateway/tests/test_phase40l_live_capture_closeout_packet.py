from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40l_live_capture_closeout_packet import build_phase40l_live_capture_closeout_packet, render_phase40l_live_capture_closeout_packet_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40l_closeout_available_before_capture() -> None:
    report = build_phase40l_live_capture_closeout_packet()
    assert_true(report["capture_closeout_available"] is True, "Closeout available")
    assert_true(report["live_capture_observed"] is False, "No capture yet")
    assert_true(report["captured_event_count"] == 0, "No events")
    assert_true(report["captured_private_test_human_message_count"] == 0, "No human messages")
    assert_true(report["captured_public_team_message_count"] == 0, "No public/team")
    assert_true(report["ready_for_capture_closeout_after_manual_runtime"] is False, "Not ready")


def test_phase40l_no_send_or_live_side_effects() -> None:
    report = build_phase40l_live_capture_closeout_packet()
    for key in ("discord_gateway_connected", "discord_api_send_called", "discord_message_sent", "reply_send_allowed", "llm_api_call_attempted", "rag_called", "external_execution", "unattended_auto_reply_allowed"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase40l_markdown() -> None:
    assert_true("Phase 40L" in render_phase40l_live_capture_closeout_packet_markdown(build_phase40l_live_capture_closeout_packet()), "Markdown")


def main() -> int:
    for test in (test_phase40l_closeout_available_before_capture, test_phase40l_no_send_or_live_side_effects, test_phase40l_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40L capture closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
