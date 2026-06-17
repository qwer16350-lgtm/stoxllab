from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase46_blocked_llm_output_review import build_phase46_blocked_llm_output_review


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase46_blocked_output_review_metadata_only() -> None:
    report = build_phase46_blocked_llm_output_review()
    assert_true(report["report_type"] == "phase46_blocked_llm_output_review", "Report type")
    assert_true(report["metadata_only"] is True, "Metadata only")
    assert_true(report["phase45_actual_llm_call_completed"] is True, "Phase45 completed")
    assert_true(report["phase45_llm_call_count"] == 1, "Phase45 exactly one")
    assert_true(report["phase45_repeat_llm_call_allowed"] is False, "No repeat")
    assert_true(report["phase45_no_repeat_lock_active"] is True, "No-repeat lock")
    assert_true(report["output_safety_checked"] is True, "Safety checked")
    assert_true(report["output_safety_blocked"] is True, "Safety blocked")
    assert_true(report["blocked_reasons"] == ["external_action_claim"], "External action claim")
    assert_true(report["safe_disclaimer_detected"] is True, "Safe disclaimer")
    assert_true(report["safe_disclaimer_reasons"] == ["negated_external_action", "review_only"], "Disclaimer reasons")


def test_phase46_review_forbids_unblock_retry_send_or_packet() -> None:
    report = build_phase46_blocked_llm_output_review()
    assert_true(report["human_review_only"] is True, "Human review")
    assert_true(report["raw_output_included"] is False, "No raw output")
    assert_true(report["full_content_included"] is False, "No full content")
    assert_true(report["ready_for_retry"] is False, "No retry ready")
    assert_true(report["automatic_retry_allowed"] is False, "No auto retry")
    assert_true(report["automatic_send_allowed"] is False, "No auto send")
    assert_true(report["automatic_output_packet_creation_allowed"] is False, "No auto packet")
    assert_true(report["retry_requires_new_manual_gate"] is True, "New gate required")
    assert_true(report["llm_api_call_attempted"] is False, "No new LLM attempt")
    assert_true(report["llm_api_called"] is False, "No new LLM call")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")


def test_phase46_review_classifier_calibration() -> None:
    report = build_phase46_blocked_llm_output_review()
    assert_true(report["classifier_calibration_fixture_based_only"] is True, "Fixture only")
    assert_true(report["classifier_negated_external_action_false_positive_count"] == 0, "No false positives")
    assert_true(report["classifier_positive_external_action_blocked_count"] >= 1, "Positive blocked")


def test_phase46_review_no_sensitive_values() -> None:
    text = json.dumps(build_phase46_blocked_llm_output_review(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase46_blocked_output_review_metadata_only,
        test_phase46_review_forbids_unblock_retry_send_or_packet,
        test_phase46_review_classifier_calibration,
        test_phase46_review_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase46 blocked LLM output review tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
