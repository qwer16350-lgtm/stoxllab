from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_one_shot_llm_draft_call import build_actual_one_shot_llm_draft_call, render_actual_one_shot_llm_draft_call_markdown


APPROVED_ENV = {
    "OPENROUTER_API_KEY": "sk-test-never-logged",
    "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVED": "true",
    "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVAL_PHRASE": "I_APPROVE_ONE_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_NO_SEND",
}
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_success(envelope: dict, config: dict) -> dict:
    assert_true(envelope["agent_route_candidate"] == "kasumi", "kasumi envelope")
    assert_true(envelope["allowed_sources"] == ["operation"], "operation envelope")
    assert_true(config["provider"] == "openrouter", "openrouter config")
    return {
        "result_type": "llm_client_result",
        "provider": "openrouter",
        "model": "openai/gpt-5.4-mini",
        "api_call_attempted": True,
        "api_call_succeeded": True,
        "api_call_failed": False,
        "error_type": None,
        "response_text": (
            "This is a review-only draft. No external action has been taken. "
            "Citation: knowledge/operation/stoxl_operation_tone_sample.md. "
            "Confirmed checks and uncertainty should be reviewed by a human before any next step."
        ),
        "usage": {"input_chars": 100, "output_chars": 180, "provider_usage": {"total_tokens": 42}},
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def mock_unsafe(envelope: dict, config: dict) -> dict:
    result = mock_success(envelope, config)
    result["response_text"] = "I sent this to the team channel. Citation: knowledge/operation/stoxl_operation_tone_sample.md"
    return result


def test_default_blocks_with_no_llm_call() -> None:
    report = build_actual_one_shot_llm_draft_call(env={})
    assert_true(report["blocked"] is True, "Default blocked")
    assert_true(report["ready"] is False, "Default not ready")
    assert_true(report["llm_api_call_attempted"] is False, "No API attempt")
    assert_true(report["llm_api_call_count"] == 0, "No API count")
    assert_true("manual_approval_not_approved" in report["blocked_reasons"], "Manual approval blocks")
    assert_true("allow_flag_missing" in report["blocked_reasons"], "Allow flag blocks")
    assert_true("openrouter_api_key_missing" in report["blocked_reasons"], "Key missing blocks")


def test_manual_approval_and_phrase_gates() -> None:
    missing = build_actual_one_shot_llm_draft_call(env={"OPENROUTER_API_KEY": "sk-x"}, allow_actual_call=True)
    assert_true(missing["manual_approval"]["approved"] is False, "Approval missing")
    mismatch = build_actual_one_shot_llm_draft_call(
        env={
            "OPENROUTER_API_KEY": "sk-x",
            "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVED": "true",
            "HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVAL_PHRASE": "WRONG",
        },
        allow_actual_call=True,
    )
    assert_true(mismatch["manual_approval"]["approval_phrase_exact_match"] is False, "Phrase mismatch")
    assert_true(mismatch["llm_api_call_attempted"] is False, "Mismatch blocks call")


def test_kasumi_only_and_operation_only() -> None:
    marin = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, allow_actual_call=True, candidate_agent="marin")
    assert_true(marin["candidate_agent_allowed"] is False, "Marin blocked")
    assert_true(marin["llm_api_call_attempted"] is False, "Marin no call")
    decision = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, allow_actual_call=True, candidate_agent="decision_maker_review")
    assert_true(decision["llm_api_call_attempted"] is False, "Decision maker review no call")
    operation = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, allow_actual_call=True, llm_caller=mock_success)
    assert_true(operation["allowed_sources"] == ["operation"], "Operation allowed")
    operations = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, allow_actual_call=True, source="operations")
    assert_true("operations_source_forbidden" in operations["blocked_reasons"], "operations forbidden")


def test_mock_success_creates_safe_packet() -> None:
    report = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, allow_actual_call=True, llm_caller=mock_success)
    assert_true(report["ready"] is True, "Ready")
    assert_true(report["blocked"] is False, "Not blocked")
    assert_true(report["llm_api_call_attempted"] is True, "API attempted")
    assert_true(report["llm_api_call_count"] == 1, "One call")
    assert_true(report["llm_response_packet_created"] is True, "Packet created")
    assert_true(report["output_safety_checked"] is True, "Safety checked")
    assert_true(report["output_safety_allowed"] is True, "Safety allowed")
    assert_true(report["ready_for_phase36e_closeout"] is True, "Closeout ready")
    assert_true(report["ready_for_discord_send"] is False, "Discord send false")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "No unattended")
    assert_true(report["llm_response_packet"]["full_content_included"] is False, "No full content")


def test_output_safety_failure_prevents_closeout() -> None:
    report = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, allow_actual_call=True, llm_caller=mock_unsafe)
    assert_true(report["llm_api_call_count"] == 1, "One call")
    assert_true(report["output_safety_checked"] is True, "Safety checked")
    assert_true(report["output_safety_allowed"] is False, "Safety blocked")
    assert_true(report["llm_response_packet_created"] is False, "No packet")
    assert_true(report["ready_for_phase36e_closeout"] is False, "Closeout false")
    assert_true(report["discord_message_sent"] is False, "No Discord")


def test_secret_values_not_logged_and_markdown() -> None:
    report = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, allow_actual_call=True, llm_caller=mock_success)
    text = json.dumps(report, ensure_ascii=False).lower()
    markdown = render_actual_one_shot_llm_draft_call_markdown(report)
    assert_true("sk-test-never-logged" not in text, "Key not logged")
    assert_true("i_approve_one_private_test" not in text, "Approval phrase not logged")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Actual One-shot LLM Draft Call" in markdown, "Markdown")


def main() -> int:
    tests = [
        test_default_blocks_with_no_llm_call,
        test_manual_approval_and_phrase_gates,
        test_kasumi_only_and_operation_only,
        test_mock_success_creates_safe_packet,
        test_output_safety_failure_prevents_closeout,
        test_secret_values_not_logged_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual one-shot LLM draft call tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
