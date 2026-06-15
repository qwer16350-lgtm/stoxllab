from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase39c_actual_send_closeout import build_phase39c_actual_send_closeout, render_phase39c_actual_send_closeout_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase39c_closeout_observes_actual_send_once() -> None:
    report = build_phase39c_actual_send_closeout()
    assert_true(report["phase39b_actual_send_observed"] is True, "Observed")
    assert_true(report["phase39b_actual_send_success"] is True, "Success")
    assert_true(report["actual_discord_send_count"] == 1, "Send count 1")
    assert_true(report["discord_api_send_called_in_phase39b"] is True, "Phase39B API called")
    assert_true(report["discord_message_sent_in_phase39b"] is True, "Phase39B message sent")
    assert_true(report["message_sent_count_in_phase39b"] == 1, "Phase39B message count")
    assert_true(report["send_scope"] == "private_test_only", "Private scope")
    assert_true(report["phase39c_closeout_completed"] is True, "Closeout complete")


def test_phase39c_closeout_no_additional_send() -> None:
    report = build_phase39c_actual_send_closeout()
    assert_true(report["additional_discord_send_called_in_phase39c"] is False, "No extra API")
    assert_true(report["additional_discord_message_sent_in_phase39c"] is False, "No extra message")
    assert_true(report["additional_message_sent_count_in_phase39c"] == 0, "No extra count")
    assert_true(report["repeat_send_allowed"] is False, "Repeat false")
    assert_true(report["automatic_retry_allowed"] is False, "Auto retry false")
    assert_true(report["manual_retry_allowed"] is False, "Manual retry false")
    assert_true(report["ready_for_repeat_send"] is False, "Ready repeat false")


def test_phase39c_closeout_no_llm_rag_external_or_public_team() -> None:
    report = build_phase39c_actual_send_closeout()
    for key in ("new_llm_api_call_attempted", "new_llm_api_called", "llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "public_channel_send_allowed", "team_channel_send_allowed", "public_channel_reply_allowed", "team_channel_reply_allowed", "unattended_auto_reply_allowed"):
        assert_true(report[key] is False, f"{key} false")


def test_phase39c_closeout_no_sensitive_values_and_markdown() -> None:
    report = build_phase39c_actual_send_closeout()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Phase 39C Actual Send Closeout" in render_phase39c_actual_send_closeout_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_phase39c_closeout_observes_actual_send_once,
        test_phase39c_closeout_no_additional_send,
        test_phase39c_closeout_no_llm_rag_external_or_public_team,
        test_phase39c_closeout_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39C actual send closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
