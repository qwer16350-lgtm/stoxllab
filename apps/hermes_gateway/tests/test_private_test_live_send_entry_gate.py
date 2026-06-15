from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_live_send_entry_gate import build_private_test_live_send_entry_gate, render_private_test_live_send_entry_gate_markdown


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


def test_live_send_entry_gate_success_fixture() -> None:
    report = build_private_test_live_send_entry_gate()
    assert_true(report["live_send_entry_gate_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["actual_private_test_send_not_started"] is True, "Actual send not started")
    assert_true(report["phase39_not_started"] is True, "Phase 39 not started")
    assert_true(report["requires_explicit_user_approval"] is True, "Approval required")
    assert_true(report["future_send_scope"] == "private_test_only", "Private scope")


def test_live_send_entry_gate_no_live_or_send_readiness() -> None:
    report = build_private_test_live_send_entry_gate()
    for key in ("ready_for_actual_private_test_send", "ready_for_discord_send", "ready_for_phase39_live_execution", "ready_for_unattended_auto_reply", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "llm_api_called", "embedding_api_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_live_send_entry_gate_blocks_bad_sources() -> None:
    assert_raises(lambda: build_private_test_live_send_entry_gate(contract={"contract_available": False}), "Missing contract should fail")
    assert_raises(lambda: build_private_test_live_send_entry_gate(payload_freeze={"would_send_payload_frozen": False}), "Missing freeze should fail")
    assert_raises(lambda: build_private_test_live_send_entry_gate(rollback_gate={"rollback_gate_available": False}), "Missing rollback should fail")
    assert_raises(lambda: build_private_test_live_send_entry_gate(operator_checklist={"operator_checklist_available": False}), "Missing checklist should fail")


def test_live_send_entry_gate_no_sensitive_values_and_markdown() -> None:
    report = build_private_test_live_send_entry_gate()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase value")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Live Send Entry Gate" in render_private_test_live_send_entry_gate_markdown(report), "Markdown")


def main() -> int:
    tests = [test_live_send_entry_gate_success_fixture, test_live_send_entry_gate_no_live_or_send_readiness, test_live_send_entry_gate_blocks_bad_sources, test_live_send_entry_gate_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test live send entry gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
