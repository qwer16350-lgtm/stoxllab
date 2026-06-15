"""Phase 34H-2 RAG evidence LLM dry-call closeout tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_llm_dry_call_closeout.py
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_llm_dry_call_closeout import (
    EMBEDDED_SANITIZED_DRY_CALL_FIXTURE,
    build_rag_evidence_llm_dry_call_closeout,
    render_rag_evidence_llm_dry_call_closeout_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(func, message: str) -> None:
    try:
        func()
    except ValueError:
        return
    raise AssertionError(message)


def fixture() -> dict:
    return copy.deepcopy(EMBEDDED_SANITIZED_DRY_CALL_FIXTURE)


def test_actual_dry_call_observed() -> None:
    closeout = build_rag_evidence_llm_dry_call_closeout()
    assert_true(closeout["actual_dry_call_observed"] is True, "Actual dry call should be observed")


def test_api_call_counts_exactly_one() -> None:
    closeout = build_rag_evidence_llm_dry_call_closeout()
    assert_true(closeout["api_call_attempted_count"] == 1, "Attempt count should be one")
    assert_true(closeout["api_call_succeeded_count"] == 1, "Success count should be one")


def test_response_packet_and_output_safety() -> None:
    closeout = build_rag_evidence_llm_dry_call_closeout()
    assert_true(closeout["llm_response_packet_created"] is True, "Response packet should be created")
    assert_true(closeout["output_safety_allowed"] is True, "Output safety should be allowed")
    assert_true(closeout["review_only_response"] is True, "Review-only response should be detected")


def test_relative_evidence_paths_only() -> None:
    closeout = build_rag_evidence_llm_dry_call_closeout()
    assert_true(closeout["relative_evidence_paths_only"] is True, "Evidence paths should be relative-only")
    assert_true(closeout["evidence_paths"] == [
        "knowledge/operation/stoxl_operation_tone_sample.md",
        "knowledge/operation/stoxl_private_test_workflow_sample.md",
    ], "Expected evidence paths should be preserved")


def test_provider_model_usage_and_cost_preserved() -> None:
    closeout = build_rag_evidence_llm_dry_call_closeout()
    assert_true(closeout["provider"] == "openrouter", "Provider should be preserved")
    assert_true(closeout["model"] == "openai/gpt-5.4-mini", "Model should be preserved")
    assert_true(closeout["prompt_tokens"] == 335, "Prompt tokens should be preserved")
    assert_true(closeout["completion_tokens"] == 101, "Completion tokens should be preserved")
    assert_true(closeout["total_tokens"] == 436, "Total tokens should be preserved")
    assert_true(closeout["provider_cost_usd"] == 0.00070575, "Provider cost should be preserved")


def test_safety_flags_false() -> None:
    closeout = build_rag_evidence_llm_dry_call_closeout()
    assert_true(closeout["ready_for_discord_send"] is False, "Ready for Discord send should be false")
    assert_true(closeout["discord_message_sent"] is False, "Discord message sent should be false")
    assert_true(closeout["discord_send_attempted"] is False, "Discord send attempted should be false")
    assert_true(closeout["embedding_api_called"] is False, "Embedding should be false")
    assert_true(closeout["external_execution"] is False, "External execution should be false")
    assert_true(closeout["additional_llm_api_call"] is False, "Additional LLM call should be false")


def test_sensitive_values_not_logged() -> None:
    closeout = build_rag_evidence_llm_dry_call_closeout()
    text = json.dumps(closeout, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "bearer " not in text, "Secret markers should be absent")
    assert_true("token=" not in text and "api_key=" not in text, "Token/API key labels should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_closeout_passed_and_phase34i_ready() -> None:
    closeout = build_rag_evidence_llm_dry_call_closeout()
    assert_true(closeout["closeout_passed"] is True, "Closeout should pass")
    assert_true(closeout["ready_for_phase34i_private_test_would_send_preview"] is True, "Phase 34I preview should be ready")


def test_fails_if_discord_message_sent_true() -> None:
    bad = fixture()
    bad["discord_message_sent"] = True
    assert_raises(lambda: build_rag_evidence_llm_dry_call_closeout(bad), "Discord sent fixture should fail")


def test_fails_if_ready_for_discord_send_true() -> None:
    bad = fixture()
    bad["ready_for_discord_send"] = True
    assert_raises(lambda: build_rag_evidence_llm_dry_call_closeout(bad), "Discord ready fixture should fail")


def test_fails_if_output_safety_false() -> None:
    bad = fixture()
    bad["output_safety_allowed"] = False
    bad["output_safety"]["allowed"] = False
    assert_raises(lambda: build_rag_evidence_llm_dry_call_closeout(bad), "Unsafe output fixture should fail")


def test_fails_if_raw_discord_id_appears() -> None:
    bad = fixture()
    bad["client_result"]["response_text"] += " 123456789012345678"
    assert_raises(lambda: build_rag_evidence_llm_dry_call_closeout(bad), "Raw Discord ID fixture should fail")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_llm_dry_call_closeout_markdown(build_rag_evidence_llm_dry_call_closeout())
    assert_true("RAG Evidence LLM Dry Call Closeout" in markdown, "Markdown should render")
    assert_true("Additional LLM API call: false" in markdown, "Markdown should state no additional LLM API call")


def main() -> int:
    tests = [
        test_actual_dry_call_observed,
        test_api_call_counts_exactly_one,
        test_response_packet_and_output_safety,
        test_relative_evidence_paths_only,
        test_provider_model_usage_and_cost_preserved,
        test_safety_flags_false,
        test_sensitive_values_not_logged,
        test_closeout_passed_and_phase34i_ready,
        test_fails_if_discord_message_sent_true,
        test_fails_if_ready_for_discord_send_true,
        test_fails_if_output_safety_false,
        test_fails_if_raw_discord_id_appears,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence LLM dry call closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
