from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_send_no_send_lock import build_private_test_send_no_send_lock, render_private_test_send_no_send_lock_markdown


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


def test_no_send_lock_success_fixture() -> None:
    report = build_private_test_send_no_send_lock()
    assert_true(report["no_send_lock_available"] is True, "Lock available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase37d_manual_preflight_available"] is True, "37D source")
    assert_true(report["source_phase37e_mock_rehearsal_available"] is True, "37E source")
    assert_true(report["phase37f_no_send_lock_passed"] is True, "Lock passed")
    assert_true(report["phase38_not_started"] is True, "Phase 38 not started")
    assert_true(report["requires_explicit_user_approval_for_phase38"] is True, "Phase 38 approval required")


def test_no_send_lock_counts_and_disabled_paths() -> None:
    report = build_private_test_send_no_send_lock()
    assert_true(report["mock_send_rehearsal_count_locked"] == 1, "Mock rehearsal locked at one")
    assert_true(report["actual_discord_send_count_locked"] == 0, "Actual Discord send locked at zero")
    assert_true(report["actual_discord_api_send_called"] is False, "No Discord API send")
    assert_true(report["actual_discord_message_sent"] is False, "No Discord message")
    assert_true(report["actual_message_sent_count"] == 0, "No actual message count")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_called"] is False, "No LLM call")
    assert_true(report["discord_live_runtime_executed"] is False, "No live runtime")
    assert_true(report["ready_for_actual_private_test_send"] is False, "No actual send readiness")
    assert_true(report["ready_for_phase38_actual_private_test_send_path"] is False, "No Phase 38 path")
    assert_true(report["ready_for_discord_send"] is False, "No Discord send readiness")


def test_no_send_lock_blocks_unsafe_overrides() -> None:
    assert_raises(
        lambda: build_private_test_send_no_send_lock(
            rehearsal={
                "mock_rehearsal_available": True,
                "mock_send_rehearsal_count": 1,
                "actual_message_sent_count": 1,
            }
        ),
        "Actual send count should fail",
    )
    assert_raises(
        lambda: build_private_test_send_no_send_lock(
            rehearsal={
                "mock_rehearsal_available": True,
                "mock_send_rehearsal_count": 1,
                "actual_message_sent_count": 0,
                "actual_discord_api_send_called": True,
            }
        ),
        "Actual API send should fail",
    )
    assert_raises(
        lambda: build_private_test_send_no_send_lock(
            rehearsal={
                "mock_rehearsal_available": True,
                "mock_send_rehearsal_count": 2,
                "actual_message_sent_count": 0,
            }
        ),
        "Mock rehearsal count other than one should fail",
    )


def test_no_send_lock_no_sensitive_values_and_markdown() -> None:
    report = build_private_test_send_no_send_lock()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Private-test Send No-send Lock" in render_private_test_send_no_send_lock_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_no_send_lock_success_fixture,
        test_no_send_lock_counts_and_disabled_paths,
        test_no_send_lock_blocks_unsafe_overrides,
        test_no_send_lock_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test send no-send lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
