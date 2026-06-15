from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from no_live_rehearsal_packet import build_no_live_rehearsal_packet, render_no_live_rehearsal_packet_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_no_live_rehearsal_packet_success_fixture() -> None:
    report = build_no_live_rehearsal_packet()
    assert_true(report["rehearsal_available"] is True, "Rehearsal available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["operator_checklist_available"] is True, "Checklist available")
    assert_true(report["manual_approval_packet_preview_available"] is True, "Approval preview available")


def test_no_live_rehearsal_packet_all_runtime_flags_false() -> None:
    report = build_no_live_rehearsal_packet()
    for key in ("live_runtime_executed", "llm_called", "discord_message_sent", "approval_phrase_generated", "ready_for_actual_approval", "ready_for_live_runtime", "ready_for_llm_call", "ready_for_discord_send", "ready_for_unattended_auto_reply"):
        assert_true(report[key] is False, f"{key} false")


def test_no_live_rehearsal_packet_no_sensitive_values() -> None:
    text = json.dumps(build_no_live_rehearsal_packet(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_no_live_rehearsal_packet_markdown() -> None:
    assert_true("No-live Rehearsal Packet" in render_no_live_rehearsal_packet_markdown(build_no_live_rehearsal_packet()), "Markdown")


def main() -> int:
    tests = [
        test_no_live_rehearsal_packet_success_fixture,
        test_no_live_rehearsal_packet_all_runtime_flags_false,
        test_no_live_rehearsal_packet_no_sensitive_values,
        test_no_live_rehearsal_packet_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All no-live rehearsal packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
