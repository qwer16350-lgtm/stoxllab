from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase53_next_readonly_capture_canary_plan import build_phase53_next_readonly_capture_canary_plan


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase53_canary_plan_contract() -> None:
    report = build_phase53_next_readonly_capture_canary_plan()
    assert_true(report["report_type"] == "phase53_next_readonly_capture_canary_plan", "Report type")
    assert_true(report["next_manual_gate_required"] is True, "Manual gate")
    assert_true(report["canary_goal"] == "capture_one_private_test_human_message_readonly", "Goal")
    assert_true(report["recommended_timeout_seconds"] == 120, "Timeout")
    assert_true(report["recommended_max_events"] == 5, "Max")
    assert_true(report["ready_for_next_manual_gate"] is True, "Ready")


def test_phase53_canary_plan_no_execution_allowed() -> None:
    report = build_phase53_next_readonly_capture_canary_plan()
    for key in ("discord_send_allowed", "reply_allowed", "llm_allowed", "rag_allowed", "embedding_vector_allowed", "external_execution_allowed", "scheduler_live_execution_allowed", "raw_content_dump_allowed", "raw_discord_ids_dump_allowed"):
        assert_true(report[key] is False, key)


def test_phase53_canary_plan_no_sensitive_values() -> None:
    text = json.dumps(build_phase53_next_readonly_capture_canary_plan(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase53_canary_plan_contract, test_phase53_canary_plan_no_execution_allowed, test_phase53_canary_plan_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase53 next read-only capture canary plan tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
