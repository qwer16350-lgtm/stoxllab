from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_send_approval_rehearsal import build_private_test_send_approval_rehearsal, render_private_test_send_approval_rehearsal_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_approval_rehearsal_success_fixture() -> None:
    report = build_private_test_send_approval_rehearsal()
    assert_true(report["approval_rehearsal_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase37a_review_packet_available"] is True, "37A source")
    assert_true(report["source_phase37b_send_preflight_preview_available"] is True, "37B source")
    assert_true(report["future_send_scope"] == "private_test_only", "Private scope")


def test_approval_rehearsal_gates_and_no_send() -> None:
    report = build_private_test_send_approval_rehearsal()
    assert_true(report["approval_phrase_generated"] is False, "No phrase generated")
    assert_true(report["approval_phrase_value_logged"] is False, "No phrase value")
    assert_true(report["manual_approval_actualized"] is False, "No manual actualized")
    assert_true("HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED" in report["future_manual_gate_names"], "Gate listed")
    assert_true("DISCORD_BOT_TOKEN" in report["future_manual_gate_names"], "Token gate listed")
    assert_true(report["ready_for_phase37d_actual_private_test_send"] is False, "No 37D readiness")
    assert_true(report["ready_for_discord_send"] is False, "No send readiness")
    assert_true(report["ready_for_phase37_live_execution"] is False, "No live")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_approval_rehearsal_no_sensitive_values_and_markdown() -> None:
    report = build_private_test_send_approval_rehearsal()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval value")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Send Approval Rehearsal" in render_private_test_send_approval_rehearsal_markdown(report), "Markdown")


def main() -> int:
    tests = [test_approval_rehearsal_success_fixture, test_approval_rehearsal_gates_and_no_send, test_approval_rehearsal_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test send approval rehearsal tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
