from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40q_capture_review_closeout import build_phase40q_capture_review_closeout, render_phase40q_capture_review_closeout_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40q_missing_capture_file_graceful() -> None:
    report = build_phase40q_capture_review_closeout()
    assert_true(report["capture_file_present"] is False, "No file")
    assert_true(report["capture_review_completed"] is False, "No review")
    assert_true(report["live_capture_observed"] is False, "No capture")
    assert_true(report["captured_event_count"] == 0, "No events")
    assert_true(report["ready_for_phase41_reply_runtime"] is False, "No phase41")


def test_phase40q_redacted_capture_file_summary_only() -> None:
    path = Path(tempfile.gettempdir()) / "stoxl_phase40q_capture.json"
    path.write_text(
        json.dumps(
            {
                "events": [
                    {"event_id_hash": "hash_event", "message_id_hash": "hash_msg", "channel_scope": "private_test", "author_kind": "human", "is_self": False, "is_bot": False, "is_duplicate": False, "decision": "accepted", "timestamp_iso": "2026-06-16T00:00:00Z"}
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    report = build_phase40q_capture_review_closeout(path)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true(report["capture_file_present"] is True, "File present")
    assert_true(report["capture_review_completed"] is True, "Review completed")
    assert_true(report["captured_event_count"] == 1, "One event")
    assert_true(report["private_test_human_message_count"] == 1, "One private human")
    assert_true("raw_message_content" not in text, "No raw content field output")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_phase40q_no_send_or_side_effects() -> None:
    report = build_phase40q_capture_review_closeout()
    for key in ("discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "rag_called", "external_execution", "raw_content_logged", "raw_discord_ids_logged", "secret_values_logged"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message")
    assert_true("Phase 40Q" in render_phase40q_capture_review_closeout_markdown(report), "Markdown")


def main() -> int:
    for test in (test_phase40q_missing_capture_file_graceful, test_phase40q_redacted_capture_file_summary_only, test_phase40q_no_send_or_side_effects):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40Q capture closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
