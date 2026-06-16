from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase45_actual_llm_one_shot_preflight import build_phase45_actual_llm_one_shot_preflight


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase45_default_blocked_no_api_no_send() -> None:
    report = build_phase45_actual_llm_one_shot_preflight()
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true(report["actual_llm_api_call"] is False, "No API call")
    assert_true(report["llm_api_call_attempted"] is False, "No API attempt")
    assert_true(report["discord_send_allowed"] is False, "Discord send false")
    assert_true(report["discord_message_sent"] is False, "No Discord message")


def test_phase45_guards_and_redaction() -> None:
    report = build_phase45_actual_llm_one_shot_preflight({"OPENROUTER_API_KEY": "SENSITIVE_KEY_VALUE_DO_NOT_LOG"})
    assert_true("cost_guard_present" in report["blocked_reasons"], "Cost guard required")
    assert_true("SENSITIVE_KEY_VALUE_DO_NOT_LOG" not in json.dumps(report, ensure_ascii=False), "No key value")
    assert_true("I_APPROVE_" not in json.dumps(report, ensure_ascii=False), "No phrase")


def main() -> int:
    for test in (test_phase45_default_blocked_no_api_no_send, test_phase45_guards_and_redaction):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 45A tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
