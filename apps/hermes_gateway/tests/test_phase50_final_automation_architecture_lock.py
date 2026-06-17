from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase50_final_automation_architecture_lock import REQUIRED_MODULES, build_phase50_final_automation_architecture_lock


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase50_architecture_contract() -> None:
    report = build_phase50_final_automation_architecture_lock()
    assert_true(report["report_type"] == "phase50_final_automation_architecture_lock", "Report type")
    assert_true(report["target_system"] == "STOXL_Discord_Agent_OS", "Target")
    assert_true(report["final_goal_is_operation_automation"] is True, "Automation goal")
    assert_true(report["human_review_only_is_not_final_goal"] is True, "Not archive")
    assert_true(report["production_unattended_ready_now"] is False, "No production unattended")
    assert_true(report["architecture_locked"] is True, "Locked")
    assert_true(report["required_modules_defined"] is True, "Modules")
    assert_true(report["manual_gate_boundary_defined"] is True, "Manual gate")
    assert_true(report["automation_levels_defined"] is True, "Levels")
    assert_true(report["next_safe_bundle"] == "continuous_readonly_runtime_foundation", "Next")


def test_phase50_required_modules() -> None:
    report = build_phase50_final_automation_architecture_lock()
    assert_true(report["required_modules"] == REQUIRED_MODULES, "Modules exact")
    assert_true("Discord Event Listener" in report["required_modules"], "Listener")
    assert_true("Forbidden Behavior Sentinel" in report["required_modules"], "Sentinel")


def test_phase50_architecture_no_execution() -> None:
    report = build_phase50_final_automation_architecture_lock()
    for key in ("scheduler_cron_live_execution", "unattended_auto_reply_implemented", "llm_api_call_attempted", "llm_api_called", "discord_api_send_called", "discord_message_sent", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        assert_true(report[key] is False, key)


def test_phase50_architecture_no_sensitive_values() -> None:
    text = json.dumps(build_phase50_final_automation_architecture_lock(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase50_architecture_contract, test_phase50_required_modules, test_phase50_architecture_no_execution, test_phase50_architecture_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase50 final automation architecture lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
