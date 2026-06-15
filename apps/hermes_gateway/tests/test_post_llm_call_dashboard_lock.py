from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from post_llm_call_dashboard_lock import build_post_llm_call_dashboard_lock, render_post_llm_call_dashboard_lock_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises_with_sentinel(overrides: dict, message: str) -> None:
    try:
        build_post_llm_call_dashboard_lock(sentinel_overrides=overrides)
    except ValueError:
        return
    raise AssertionError(message)


def test_dashboard_lock_success_fixture() -> None:
    report = build_post_llm_call_dashboard_lock()
    assert_true(report["dashboard_lock_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase36d_actual_llm_draft_call_complete"] is True, "36D complete")
    assert_true(report["phase36e_closeout_passed"] is True, "36E passed")
    assert_true(report["phase36f_no_send_final_lock_passed"] is True, "36F passed")
    assert_true(report["forbidden_behavior_sentinel_passed"] is True, "Sentinel passed")
    assert_true(report["ready_for_phase37_entry_gate"] is True, "Ready for 37")


def test_dashboard_lock_counts_and_no_execution() -> None:
    report = build_post_llm_call_dashboard_lock()
    assert_true(report["new_llm_api_call_attempted"] is False, "No new attempt")
    assert_true(report["new_llm_api_called"] is False, "No new call")
    assert_true(report["total_phase36_llm_call_count"] == 1, "One LLM")
    assert_true(report["total_phase36_discord_message_sent_count"] == 0, "Zero Discord")
    assert_true(report["sent_channel_scope"] == "none", "No sent channel")
    assert_true(report["output_safety_allowed"] is True, "Output allowed")
    assert_true(report["ready_for_discord_send"] is False, "No send ready")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_dashboard_sentinel_fails_bad_values() -> None:
    assert_raises_with_sentinel({"total_phase36_llm_call_count": 2}, "LLM count >1 fails")
    assert_raises_with_sentinel({"total_phase36_discord_message_sent_count": 1}, "Discord count fails")
    assert_raises_with_sentinel({"phase36_discord_message_sent": True}, "Discord sent true fails")
    assert_raises_with_sentinel({"embedding_api_called": True}, "Embedding fails")
    assert_raises_with_sentinel({"external_execution": True}, "External fails")
    assert_raises_with_sentinel({"api_key_value_logged": True}, "Secret logged fails")
    assert_raises_with_sentinel({"full_content_included": True}, "Full content fails")


def test_dashboard_no_sensitive_values_and_markdown() -> None:
    report = build_post_llm_call_dashboard_lock()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Post-LLM-call Dashboard Lock" in render_post_llm_call_dashboard_lock_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_dashboard_lock_success_fixture,
        test_dashboard_lock_counts_and_no_execution,
        test_dashboard_sentinel_fails_bad_values,
        test_dashboard_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All post-LLM-call dashboard lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
