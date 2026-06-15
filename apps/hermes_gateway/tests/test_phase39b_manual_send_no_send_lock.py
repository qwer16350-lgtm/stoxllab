from __future__ import annotations

import json
import re
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase39b_manual_send_no_send_lock import build_phase39b_manual_send_no_send_lock, render_phase39b_manual_send_no_send_lock_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase39b_no_send_lock_counts_zero() -> None:
    report = build_phase39b_manual_send_no_send_lock()
    assert_true(report["report_type"] == "phase39b_manual_send_no_send_lock", "Report type")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["actual_discord_send_count"] == 0, "Actual send count 0")
    assert_true(report["message_sent_count"] == 0, "Message count 0")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No message sent")
    assert_true(report["actual_private_test_send_executed"] is False, "No actual private send")


def test_phase39b_no_send_lock_phase39c_unavailable() -> None:
    report = build_phase39b_manual_send_no_send_lock()
    assert_true(report["phase39b_actual_send_not_executed_yet"] is True, "39B not executed")
    assert_true(report["phase39c_closeout_not_available"] is True, "39C unavailable")
    assert_true(report["phase39c_closeout_reason"] == "no_actual_discord_message_sent", "Reason")
    assert_true(report["ready_for_phase39b_actual_send_manual_attempt"] is False, "No manual ready")
    assert_true(report["ready_for_phase39c_send_closeout"] is False, "No closeout ready")


def test_phase39b_no_send_lock_safety_false() -> None:
    report = build_phase39b_manual_send_no_send_lock()
    for key in (
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "unattended_auto_reply_allowed",
        "public_team_send_allowed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
    ):
        assert_true(report[key] is False, f"{key} false")


def test_phase39b_no_send_lock_no_sensitive_values_and_markdown() -> None:
    report = build_phase39b_manual_send_no_send_lock()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("i_approve_" not in text, "No approval phrase value")
    assert_true("sk-" not in text, "No API key")
    assert_true("token:" not in text, "No token")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw long IDs")
    markdown = render_phase39b_manual_send_no_send_lock_markdown(report)
    assert_true("Phase 39B Manual Send No-send Lock" in markdown, "Markdown title")
    assert_true("Actual Discord send count: 0" in markdown, "Markdown no-send")


def main() -> int:
    tests = [
        test_phase39b_no_send_lock_counts_zero,
        test_phase39b_no_send_lock_phase39c_unavailable,
        test_phase39b_no_send_lock_safety_false,
        test_phase39b_no_send_lock_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39B manual send no-send lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
