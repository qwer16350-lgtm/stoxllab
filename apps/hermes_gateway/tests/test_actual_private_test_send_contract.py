from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_private_test_send_contract import build_actual_private_test_send_contract, render_actual_private_test_send_contract_markdown


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


def test_contract_success_fixture() -> None:
    report = build_actual_private_test_send_contract()
    assert_true(report["contract_available"] is True, "Contract available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase37f_no_send_lock_passed"] is True, "37F source")
    assert_true(report["send_scope"] == "private_test_only", "Private scope")
    assert_true(report["ready_for_payload_freeze"] is True, "Ready for freeze")


def test_contract_no_live_or_send_paths() -> None:
    report = build_actual_private_test_send_contract()
    for key in ("new_llm_api_call_attempted", "new_llm_api_called", "llm_api_call_attempted", "llm_api_called", "actual_send_implementation_executed", "discord_live_runtime_executed", "discord_api_send_called", "discord_message_sent", "ready_for_actual_private_test_send", "ready_for_discord_send", "ready_for_phase38_live_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_contract_blocks_unsafe_source() -> None:
    assert_raises(lambda: build_actual_private_test_send_contract({"phase37f_no_send_lock_passed": False}), "Missing 37F source should fail")


def test_contract_no_sensitive_values_and_markdown() -> None:
    report = build_actual_private_test_send_contract()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Actual Private-test Send Contract" in render_actual_private_test_send_contract_markdown(report), "Markdown")


def main() -> int:
    tests = [test_contract_success_fixture, test_contract_no_live_or_send_paths, test_contract_blocks_unsafe_source, test_contract_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual private-test send contract tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
