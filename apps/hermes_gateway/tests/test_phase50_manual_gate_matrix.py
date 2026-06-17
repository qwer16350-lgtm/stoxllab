from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase50_manual_gate_matrix import build_phase50_manual_gate_matrix


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase50_manual_gate_matrix_contract() -> None:
    report = build_phase50_manual_gate_matrix()
    assert_true(report["report_type"] == "phase50_manual_gate_matrix", "Report type")
    assert_true(report["manual_gate_matrix_available"] is True, "Available")
    assert_true(report["gate_count"] == 6, "Gate count")
    assert_true(report["manual_gate_execution_available_now"] is False, "No execution")
    for gate in report["gates"]:
        assert_true(gate["approval_phrase_required"] is True, "Phrase")
        assert_true(gate["cost_count_guard_required_when_llm_involved"] is True, "Cost")
        assert_true(gate["channel_allowlist_required_when_discord_send_involved"] is True, "Channel")
        assert_true(gate["rate_limit_required"] is True, "Rate")
        assert_true(gate["cooldown_required"] is True, "Cooldown")
        assert_true(gate["no_repeat_or_bounded_repeat_lock_required"] is True, "Repeat")
        assert_true(gate["secret_raw_log_forbidden"] is True, "Raw")
        assert_true(gate["execution_available_now"] is False, "No gate execution")


def test_phase50_manual_gate_matrix_names_and_no_execution() -> None:
    report = build_phase50_manual_gate_matrix()
    names = [gate["gate_name"] for gate in report["gates"]]
    assert_true("Read-only live runtime gate" in names, "Read-only")
    assert_true("Production unattended limited launch gate" in names, "Production")
    for key in ("llm_api_call_attempted", "llm_api_called", "discord_api_send_called", "discord_message_sent", "scheduler_cron_live_execution", "external_execution"):
        assert_true(report[key] is False, key)


def test_phase50_manual_gate_matrix_no_sensitive_values() -> None:
    text = json.dumps(build_phase50_manual_gate_matrix(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase50_manual_gate_matrix_contract, test_phase50_manual_gate_matrix_names_and_no_execution, test_phase50_manual_gate_matrix_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase50 manual gate matrix tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
