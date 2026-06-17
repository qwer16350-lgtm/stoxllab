from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from output_safety import (
    NEGATED_EXTERNAL_ACTION_FIXTURES,
    POSITIVE_EXTERNAL_ACTION_FIXTURES,
    build_output_safety_calibration_report,
    check_output_safety_fixture,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_negated_external_action_fixtures_do_not_block() -> None:
    for fixture in NEGATED_EXTERNAL_ACTION_FIXTURES:
        result = check_output_safety_fixture(fixture)
        assert_true(result["allowed"] is True, f"Allowed negated fixture: {fixture}")
        assert_true(result["blocked"] is False, f"Not blocked negated fixture: {fixture}")
        assert_true("external_action_claim" not in result["blocked_reasons"], "No external action false positive")
        assert_true(result["safe_disclaimer_detected"] is True, "Safe disclaimer detected")


def test_positive_external_action_fixtures_still_block() -> None:
    for fixture in POSITIVE_EXTERNAL_ACTION_FIXTURES:
        result = check_output_safety_fixture(fixture)
        assert_true(result["blocked"] is True, f"Blocked positive fixture: {fixture}")


def test_output_safety_calibration_report_safe() -> None:
    report = build_output_safety_calibration_report()
    assert_true(report["fixture_based_only"] is True, "Fixture only")
    assert_true(report["negated_external_action_false_positive_count"] == 0, "No false positives")
    assert_true(report["positive_external_action_blocked_count"] == len(POSITIVE_EXTERNAL_ACTION_FIXTURES), "Positive blocked")
    assert_true(report["raw_output_included"] is False, "No raw output")
    assert_true(report["full_content_included"] is False, "No full content")
    assert_true(report["llm_api_called"] is False, "No LLM")
    assert_true(report["discord_message_sent"] is False, "No Discord")


def test_output_safety_no_sensitive_values() -> None:
    text = json.dumps(build_output_safety_calibration_report(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_negated_external_action_fixtures_do_not_block,
        test_positive_external_action_fixtures_still_block,
        test_output_safety_calibration_report_safe,
        test_output_safety_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase46 output safety calibration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
