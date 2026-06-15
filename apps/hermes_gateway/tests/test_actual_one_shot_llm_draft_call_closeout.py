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


def test_closeout_success_fixture() -> None:
    report = build_actual_one_shot_llm_draft_call_closeout()
    assert_true(report["closeout_available"] is True, "Closeout available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase36d_actual_call_observed"] is True, "Phase 36D observed")
    assert_true(report["agent"] == "kasumi", "Kasumi")
    assert_true(report["allowed_sources"] == ["operation"], "Operation only")
    assert_true(report["evidence_citations"] == ["knowledge/operation/stoxl_operation_tone_sample.md"], "Citation")
    assert_true(report["provider"] == "openrouter", "Provider")
    assert_true(report["model"] == "openai/gpt-5.4-mini", "Model")


def test_closeout_no_new_execution() -> None:
    report = build_actual_one_shot_llm_draft_call_closeout()
    assert_true(report["additional_llm_api_call"] is False, "No additional LLM")
    assert_true(report["discord_live_runtime_executed_by_closeout"] is False, "No Discord runtime")
    assert_true(report["discord_api_send_called"] is False, "No Discord API send")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["message_sent_count"] == 0, "No messages")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")


def test_closeout_counts_and_safety() -> None:
    report = build_actual_one_shot_llm_draft_call_closeout()
    assert_true(report["llm_api_call_attempted_count"] == 1, "Attempt count one")
    assert_true(report["llm_api_called_count"] == 1, "Call count one")
    assert_true(report["llm_response_packet_created"] is True, "Packet created")
    assert_true(report["llm_response_review_only"] is True, "Review only")
    assert_true(report["output_safety_checked"] is True, "Safety checked")
    assert_true(report["output_safety_allowed"] is True, "Safety allowed")
    assert_true(report["output_safety_blocked"] is False, "Safety not blocked")
    assert_true(report["ready_for_discord_send"] is False, "Discord send false")
    assert_true(report["public_channel_send_called"] is False, "No public send")
    assert_true(report["team_channel_send_called"] is False, "No team send")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["full_content_included"] is False, "No full content")
    assert_true(report["response_preview_only"] is True, "Preview only")
    assert_true(report["phase36e_closeout_passed"] is True, "Closeout passed")
    assert_true(report["ready_for_phase36f_no_send_final_lock"] is True, "Ready for 36F")


def test_closeout_fails_bad_counts_and_send() -> None:
    assert_raises(lambda item: item.update({"llm_api_call_attempted_count": 0}), "Attempt count 0 fails")
    assert_raises(lambda item: item.update({"llm_api_called_count": 2}), "Call count 2 fails")
    assert_raises(lambda item: item.update({"discord_message_sent": True}), "Discord sent fails")
    assert_raises(lambda item: item.update({"message_sent_count": 1}), "Message count fails")


def test_closeout_fails_bad_safety() -> None:
    assert_raises(lambda item: item.update({"output_safety_allowed": False}), "Output safety blocked")
    assert_raises(lambda item: item.update({"output_safety_blocked": True}), "Output safety blocked true")
    assert_raises(lambda item: item.update({"full_content_included": True}), "Full content fails")
    assert_raises(lambda item: item.update({"embedding_api_called": True}), "Embedding fails")
    assert_raises(lambda item: item.update({"external_execution": True}), "External fails")


def test_sensitive_values_not_logged_and_markdown() -> None:
    report = build_actual_one_shot_llm_draft_call_closeout()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text, "No key marker")
    assert_true("bearer " not in text, "No bearer")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    markdown = render_actual_one_shot_llm_draft_call_closeout_markdown(report)
    assert_true("Actual One-shot LLM Draft Call Closeout" in markdown, "Markdown")


def test_sensitive_fixture_fails() -> None:
    assert_raises(lambda item: item.update({"response_preview": "secret sk-test-value"}), "Secret fails")
    assert_raises(lambda item: item.update({"response_preview": "raw id 123456789012345678"}), "Raw ID fails")
    assert_raises(lambda item: item.update({"response_preview": "I_APPROVE_BAD_VALUE"}), "Approval phrase fails")


def main() -> int:
    tests = [
        test_closeout_success_fixture,
        test_closeout_no_new_execution,
        test_closeout_counts_and_safety,
        test_closeout_fails_bad_counts_and_send,
        test_closeout_fails_bad_safety,
        test_sensitive_values_not_logged_and_markdown,
        test_sensitive_fixture_fails,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual one-shot LLM draft call closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
