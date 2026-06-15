from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_send_operator_checklist import build_private_test_send_operator_checklist, render_private_test_send_operator_checklist_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def test_operator_checklist_success_fixture() -> None:
    report = build_private_test_send_operator_checklist()
    assert_true(report["operator_checklist_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase38c_rollback_gate_available"] is True, "38C source")
    assert_true(report["operator_checklist_ready"] is True, "Ready")
    assert_true("working_tree_clean" in report["required_manual_checks"], "Working tree check")
    assert_true("final_send_command_not_run" in report["required_manual_checks"], "No final send command")


def test_operator_checklist_no_approval_or_send() -> None:
    report = build_private_test_send_operator_checklist()
    for key in ("approval_phrase_generated", "approval_phrase_value_logged", "manual_approval_actualized", "discord_api_send_called", "discord_message_sent", "ready_for_actual_private_test_send", "ready_for_discord_send"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["final_send_command_not_run"] is True, "Final send not run")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_operator_checklist_blocks_bad_source() -> None:
    assert_raises(lambda: build_private_test_send_operator_checklist({"rollback_gate_available": False}), "Missing rollback gate should fail")


def test_operator_checklist_no_sensitive_values_and_markdown() -> None:
    report = build_private_test_send_operator_checklist()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Operator Checklist" in render_private_test_send_operator_checklist_markdown(report), "Markdown")


def main() -> int:
    tests = [test_operator_checklist_success_fixture, test_operator_checklist_no_approval_or_send, test_operator_checklist_blocks_bad_source, test_operator_checklist_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test send operator checklist tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
