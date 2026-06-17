from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase52b_readonly_live_capture_closeout import build_phase52b_readonly_live_capture_closeout


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase52b_closeout_contract() -> None:
    report = build_phase52b_readonly_live_capture_closeout()
    assert_true(report["report_type"] == "phase52b_readonly_live_capture_closeout", "Report type")
    assert_true(report["actual_readonly_runtime_executed"] is True, "Runtime observed")
    assert_true(report["discord_gateway_connected"] is True, "Gateway")
    assert_true(report["runtime_scope"] == "private_test_readonly", "Scope")
    assert_true(report["exit_reason"] == "timeout", "Timeout")
    assert_true(report["timeout_seconds"] == 60, "Timeout seconds")
    assert_true(report["max_events"] == 5, "Max events")
    assert_true(report["captured_event_count"] == 0, "Empty capture")
    assert_true(report["capture_file_written"] is True, "Capture file")
    assert_true(report["capture_file_metadata_available"] is True, "Metadata")
    assert_true(report["empty_capture_handled"] is True, "Empty handled")
    assert_true(report["ready_for_capture_to_review_packet_replay"] is True, "Replay ready")


def test_phase52b_closeout_no_external_actions_or_raw_values() -> None:
    report = build_phase52b_readonly_live_capture_closeout()
    for key in ("capture_file_read_attempted", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "scheduler_cron_live_execution", "raw_content_logged", "raw_discord_ids_logged", "secret_values_logged"):
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "No messages")


def test_phase52b_closeout_no_sensitive_values() -> None:
    text = json.dumps(build_phase52b_readonly_live_capture_closeout(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase52b_closeout_contract, test_phase52b_closeout_no_external_actions_or_raw_values, test_phase52b_closeout_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase52B read-only live capture closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
