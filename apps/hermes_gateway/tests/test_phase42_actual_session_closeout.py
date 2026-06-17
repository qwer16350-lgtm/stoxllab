from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase42_actual_session_closeout import build_phase42_actual_session_closeout


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase42_closeout_records_exactly_once_success() -> None:
    report = build_phase42_actual_session_closeout()
    assert_true(report["phase42_actual_supervised_private_test_session_succeeded"] is True, "Success recorded")
    assert_true(report["phase42_exactly_once_supervised_success_recorded"] is True, "Exactly once")
    assert_true(report["message_sent_count"] == 1, "One observed message")
    assert_true(report["sent_scope"] == "private_test_only", "Private-test scope")
    assert_true(report["runtime_adapter_type"] == "real_discord", "Observed real adapter")
    assert_true(report["events_observed_count"] == 2, "Observed events")
    assert_true(report["eligible_private_test_human_message_found"] is True, "Eligible event")
    assert_true(report["session_lock_consumed"] is True, "Lock consumed")


def test_phase42_closeout_locks_repeats_and_adds_no_send() -> None:
    report = build_phase42_actual_session_closeout()
    assert_true(report["phase42_repeat_supervised_session_locked"] is True, "Phase 42 repeat locked")
    assert_true(report["phase42_repeat_supervised_session_allowed"] is False, "Phase 42 repeat disallowed")
    assert_true(report["phase41b_repeat_send_locked"] is True, "Phase 41B repeat still locked")
    assert_true(report["ready_for_phase42_repeat_supervised_session"] is False, "No Phase 42 repeat readiness")
    assert_true(report["ready_for_phase41b_repeat_send"] is False, "No Phase 41B repeat")
    assert_true(report["actual_discord_runtime_executed_during_closeout"] is False, "No runtime in closeout")
    assert_true(report["discord_api_send_called_during_closeout"] is False, "No API in closeout")
    assert_true(report["discord_message_sent_during_closeout"] is False, "No message in closeout")
    assert_true(report["additional_message_sent_count_during_closeout"] == 0, "No additional send")


def test_phase42_closeout_negative_fixtures() -> None:
    cases = [
        {"message_sent_count": 0},
        {"message_sent_count": 2},
        {"sent_scope": "public"},
        {"session_lock_consumed": False},
    ]
    for case in cases:
        report = build_phase42_actual_session_closeout(case)
        assert_true(report["phase42_actual_supervised_private_test_session_succeeded"] is False, "Invalid success blocked")
        assert_true(report["message_sent_count"] == 0, "Invalid count redacted to zero")
        assert_true(report["phase42_repeat_supervised_session_locked"] is False, "Invalid success does not lock")


def test_phase42_closeout_no_sensitive_values_or_external_calls() -> None:
    report = build_phase42_actual_session_closeout()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("i_approve_" not in text, "No phrase")
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    for key in ("llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")


def main() -> int:
    tests = [
        test_phase42_closeout_records_exactly_once_success,
        test_phase42_closeout_locks_repeats_and_adds_no_send,
        test_phase42_closeout_negative_fixtures,
        test_phase42_closeout_no_sensitive_values_or_external_calls,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 42 actual session closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
