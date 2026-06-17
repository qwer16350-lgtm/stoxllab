from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_one_shot_llm_draft_call_closeout import (
    build_actual_one_shot_llm_draft_call_closeout,
    build_success_fixture,
    render_actual_one_shot_llm_draft_call_closeout_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(mutator, message: str) -> None:
    fixture = build_success_fixture()
    mutator(fixture)
    try:
        build_actual_one_shot_llm_draft_call_closeout(fixture)
    except ValueError:
        return
    raise AssertionError(message)


def test_phase45_closeout_records_exactly_once_actual_call() -> None:
    report = build_actual_one_shot_llm_draft_call_closeout()
    assert_true(report["report_type"] == "phase45_actual_llm_call_closeout", "Phase45 report type")
    assert_true(report["closeout_available"] is True, "Closeout available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_manual_gate3_actual_llm_call_observed"] is True, "Manual Gate 3 observed")
    assert_true(report["phase45_actual_llm_one_shot_completed"] is True, "Phase45 completed")
    assert_true(report["phase45_actual_llm_call_count"] == 1, "Phase45 call count one")
    assert_true(report["llm_api_call_attempted"] is True, "Attempted")
    assert_true(report["llm_api_called"] is True, "Called")
    assert_true(report["llm_api_call_count"] == 1, "LLM count one")
    assert_true(report["actual_llm_api_call_attempted"] is True, "Actual attempt")
    assert_true(report["actual_llm_api_called"] is True, "Actual called")
    assert_true(report["real_llm_api_call_count"] == 1, "Real count one")
    assert_true(report["provider"] == "openrouter", "Provider")
    assert_true(report["model_present"] is True, "Model present")
    assert_true(report["model_value_logged"] is False, "Model value not logged")
    assert_true(report["provider_usage_present"] is True, "Usage present")


def test_phase45_closeout_no_repeat_lock_and_no_new_execution() -> None:
    report = build_actual_one_shot_llm_draft_call_closeout()
    assert_true(report["phase45_ready_for_repeat_llm_call"] is False, "No repeat")
    assert_true(report["phase45_actual_llm_one_shot_repeat_locked"] is True, "Repeat locked")
    assert_true(report["phase45_actual_llm_one_shot_already_consumed"] is True, "Consumed")
    assert_true(report["additional_llm_api_call"] is False, "No additional LLM")
    assert_true(report["discord_live_runtime_executed_by_closeout"] is False, "No Discord runtime")
    assert_true(report["discord_api_send_called"] is False, "No Discord API send")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["message_sent_count"] == 0, "No messages")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")


def test_phase45_output_safety_blocked_closeout() -> None:
    report = build_actual_one_shot_llm_draft_call_closeout()
    assert_true(report["output_safety_checked"] is True, "Safety checked")
    assert_true(report["output_safety_allowed"] is False, "Safety not allowed")
    assert_true(report["output_safety_blocked"] is True, "Safety blocked")
    assert_true("external_action_claim" in report["output_safety"]["blocked_reasons"], "External action claim")
    assert_true(report["output_safety"]["safe_disclaimer_detected"] is True, "Safe disclaimer")
    assert_true(report["llm_response_packet_created"] is False, "No packet")
    assert_true(report["ready_for_discord_send"] is False, "Discord send false")
    assert_true(report["output_safety_false_positive_possible"] is True, "False-positive review noted")
    assert_true(report["output_safety_requires_phase46_review"] is True, "Phase46 review required")
    assert_true(report["phase45_closeout_passed"] is True, "Closeout passed")


def test_phase45_closeout_rejects_bad_counts_send_or_safety() -> None:
    assert_raises(lambda item: item.update({"llm_api_call_count": 0}), "LLM count 0 fails")
    assert_raises(lambda item: item.update({"phase45_actual_llm_call_count": 2}), "Phase45 count 2 fails")
    assert_raises(lambda item: item.update({"actual_llm_api_called": False}), "Actual false fails")
    assert_raises(lambda item: item.update({"real_llm_api_call_count": 0}), "Real count 0 fails")
    assert_raises(lambda item: item.update({"phase45_ready_for_repeat_llm_call": True}), "Repeat ready fails")
    assert_raises(lambda item: item.update({"llm_response_packet_created": True}), "Packet fails")
    assert_raises(lambda item: item.update({"output_safety_allowed": True}), "Safety allowed fails")
    assert_raises(lambda item: item.update({"output_safety_blocked": False}), "Safety not blocked fails")
    assert_raises(lambda item: item.update({"discord_message_sent": True}), "Discord sent fails")
    assert_raises(lambda item: item.update({"message_sent_count": 1}), "Message count fails")


def test_phase45_closeout_no_sensitive_values_and_markdown() -> None:
    report = build_actual_one_shot_llm_draft_call_closeout()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text, "No key marker")
    assert_true("bearer " not in text, "No bearer")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true("openai/gpt-5.4-mini" not in text, "No raw model value")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    markdown = render_actual_one_shot_llm_draft_call_closeout_markdown(report)
    assert_true("Phase45 Actual LLM One-shot Call Closeout" in markdown, "Markdown")


def test_phase45_sensitive_fixture_fails() -> None:
    assert_raises(lambda item: item.update({"response_preview": "secret sk-test-value"}), "Secret fails")
    assert_raises(lambda item: item.update({"response_preview": "raw id 123456789012345678"}), "Raw ID fails")
    assert_raises(lambda item: item.update({"response_preview": "I_APPROVE_BAD_VALUE"}), "Approval phrase fails")


def main() -> int:
    tests = [
        test_phase45_closeout_records_exactly_once_actual_call,
        test_phase45_closeout_no_repeat_lock_and_no_new_execution,
        test_phase45_output_safety_blocked_closeout,
        test_phase45_closeout_rejects_bad_counts_send_or_safety,
        test_phase45_closeout_no_sensitive_values_and_markdown,
        test_phase45_sensitive_fixture_fails,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 45 actual LLM call closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
