from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase47_human_review_closeout import build_phase47_human_review_closeout


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase47_human_review_closeout_status() -> None:
    report = build_phase47_human_review_closeout()
    assert_true(report["report_type"] == "phase47_human_review_closeout", "Report type")
    assert_true(report["metadata_only"] is True, "Metadata only")
    assert_true(report["phase45_actual_llm_call_completed"] is True, "Phase45 complete")
    assert_true(report["phase45_llm_call_count"] == 1, "Exactly one historical Phase45 call")
    assert_true(report["output_safety_blocked"] is True, "Output blocked")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["human_review_required"] is True, "Human review")
    assert_true(report["automatic_retry_allowed"] is False, "No auto retry")
    assert_true(report["automatic_send_allowed"] is False, "No auto send")
    assert_true(report["raw_output_included"] is False, "No raw output")


def test_phase47_human_review_closeout_no_execution() -> None:
    report = build_phase47_human_review_closeout()
    assert_true(report["full_content_included"] is False, "No full content")
    assert_true(report["retry_execution_available"] is False, "No retry execution")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_called"] is False, "No LLM call")
    assert_true(report["additional_llm_api_call"] is False, "No extra LLM")
    assert_true(report["discord_api_send_called"] is False, "No Discord API")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["phase47_executes_option_b"] is False, "Option B not executed")
    assert_true(report["phase47_executes_option_c"] is False, "Option C not executed")


def test_phase47_human_review_closeout_next_options() -> None:
    report = build_phase47_human_review_closeout()
    assert_true("Option A: human-review-only project closeout" in report["next_options"], "Option A")
    assert_true("Option B: Phase48 new retry Manual Gate design" in report["next_options"], "Option B")
    assert_true("Option C: Phase48 Discord send review gate design" in report["next_options"], "Option C")


def test_phase47_human_review_closeout_no_sensitive_values() -> None:
    text = json.dumps(build_phase47_human_review_closeout(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase47_human_review_closeout_status,
        test_phase47_human_review_closeout_no_execution,
        test_phase47_human_review_closeout_next_options,
        test_phase47_human_review_closeout_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase47 human-review closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
