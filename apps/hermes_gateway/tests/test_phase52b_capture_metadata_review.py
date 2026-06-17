from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase52b_capture_metadata_review import build_phase52b_capture_metadata_review


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase52b_metadata_review_contract() -> None:
    report = build_phase52b_capture_metadata_review()
    assert_true(report["report_type"] == "phase52b_capture_metadata_review", "Report type")
    assert_true(report["capture_file_present"] is True, "Capture present")
    assert_true(report["capture_file_read_attempted"] is False, "No read")
    assert_true(report["raw_capture_dumped"] is False, "No dump")
    assert_true(report["captured_event_count"] == 0, "Count 0")
    assert_true(report["empty_capture_valid"] is True, "Empty valid")
    assert_true(report["metadata_review_passed"] is True, "Passed")


def test_phase52b_metadata_review_no_raw_or_external() -> None:
    report = build_phase52b_capture_metadata_review()
    for key in ("raw_content_included", "raw_discord_ids_logged", "secret_values_logged", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        assert_true(report[key] is False, key)


def test_phase52b_metadata_review_no_sensitive_values() -> None:
    text = json.dumps(build_phase52b_capture_metadata_review(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase52b_metadata_review_contract, test_phase52b_metadata_review_no_raw_or_external, test_phase52b_metadata_review_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase52B capture metadata review tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
