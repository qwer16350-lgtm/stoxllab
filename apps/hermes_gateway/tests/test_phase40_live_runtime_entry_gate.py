from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_live_runtime_entry_gate import build_phase40_live_runtime_entry_gate, render_phase40_live_runtime_entry_gate_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40h_entry_gate_blocked_by_default() -> None:
    report = build_phase40_live_runtime_entry_gate()
    assert_true(report["live_runtime_entry_gate_available"] is True, "Gate available")
    assert_true(report["live_runtime_start_allowed"] is False, "Start blocked")
    assert_true(report["ready_for_live_runtime_execution"] is False, "Not live ready")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_message_sent"] is False, "No message")


def test_phase40h_future_flags_are_names_only() -> None:
    report = build_phase40_live_runtime_entry_gate()
    text = " ".join(report["required_future_flags"])
    assert_true("HERMES_PHASE40_PRIVATE_TEST_LIVE_RUNTIME_APPROVED=true" in text, "Approval flag name")
    assert_true(" exact" in text, "Phrase value omitted")
    assert_true(report["approval_phrase_value_logged"] is False, "No phrase value")
    assert_true(report["private_test_channel_id_value_logged"] is False, "No channel id")


def test_phase40h_markdown() -> None:
    assert_true("Phase 40H" in render_phase40_live_runtime_entry_gate_markdown(build_phase40_live_runtime_entry_gate()), "Markdown")


def main() -> int:
    for test in (test_phase40h_entry_gate_blocked_by_default, test_phase40h_future_flags_are_names_only, test_phase40h_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40H live runtime entry gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
