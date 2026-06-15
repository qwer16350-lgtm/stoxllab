from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_send_rollback_gate import build_private_test_send_rollback_gate, render_private_test_send_rollback_gate_markdown


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


def test_rollback_gate_success_fixture() -> None:
    report = build_private_test_send_rollback_gate()
    assert_true(report["rollback_gate_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase38b_payload_frozen"] is True, "38B source")
    assert_true(report["rollback_checklist_ready"] is True, "Checklist")
    assert_true(report["emergency_disable_gates_listed"] is True, "Gates listed")


def test_rollback_gate_no_delete_edit_or_send() -> None:
    report = build_private_test_send_rollback_gate()
    for key in ("post_send_delete_or_edit_api_implemented", "post_send_delete_or_edit_api_called", "discord_api_send_called", "discord_message_sent", "ready_for_actual_private_test_send", "ready_for_discord_send", "embedding_api_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_rollback_gate_blocks_bad_source() -> None:
    assert_raises(lambda: build_private_test_send_rollback_gate({"would_send_payload_frozen": False}), "Unfrozen source should fail")


def test_rollback_gate_no_sensitive_values_and_markdown() -> None:
    report = build_private_test_send_rollback_gate()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase value")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Private-test Send Rollback Gate" in render_private_test_send_rollback_gate_markdown(report), "Markdown")


def main() -> int:
    tests = [test_rollback_gate_success_fixture, test_rollback_gate_no_delete_edit_or_send, test_rollback_gate_blocks_bad_source, test_rollback_gate_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test send rollback gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
