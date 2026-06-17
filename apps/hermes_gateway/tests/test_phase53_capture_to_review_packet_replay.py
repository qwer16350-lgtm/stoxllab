from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase53_capture_to_review_packet_replay import build_phase53_capture_to_review_packet_replay


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase53_replay_contract() -> None:
    report = build_phase53_capture_to_review_packet_replay()
    assert_true(report["report_type"] == "phase53_capture_to_review_packet_replay", "Report type")
    assert_true(report["source"] == "readonly_live_capture", "Source")
    assert_true(report["captured_event_count"] == 0, "Captured")
    assert_true(report["replayed_event_count"] == 0, "Replayed")
    assert_true(report["review_packet_count"] == 0, "Packets")
    assert_true(report["empty_capture_replay_handled"] is True, "Empty replay")
    assert_true(report["synthetic_fallback_used"] is False, "No synthetic fallback")
    assert_true(report["review_packet_pipeline_ready"] is True, "Pipeline")
    assert_true(report["ready_for_next_readonly_capture_canary"] is True, "Next canary")


def test_phase53_replay_no_send_or_external() -> None:
    report = build_phase53_capture_to_review_packet_replay()
    for key in ("discord_send_allowed", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "raw_content_included", "raw_content_logged", "raw_discord_ids_logged", "secret_values_logged"):
        assert_true(report[key] is False, key)


def test_phase53_replay_no_sensitive_values() -> None:
    text = json.dumps(build_phase53_capture_to_review_packet_replay(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase53_replay_contract, test_phase53_replay_no_send_or_external, test_phase53_replay_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase53 capture-to-review-packet replay tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
