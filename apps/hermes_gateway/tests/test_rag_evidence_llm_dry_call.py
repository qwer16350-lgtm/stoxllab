"""Phase 34H-1 approved RAG evidence LLM dry-call tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_llm_dry_call.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_llm_dry_call import (
    APPROVAL_PHRASE,
    build_rag_evidence_llm_dry_call_report,
    render_rag_evidence_llm_dry_call_markdown,
)


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def approved_env() -> dict[str, str]:
    return {
        "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED": "true",
        "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_LLM_PROVIDER": "openrouter",
        "HERMES_LLM_MODEL": "openai/gpt-5.4-mini",
        "HERMES_LLM_API_KEY": "sk-test-value-that-must-not-appear",
        "HERMES_LLM_ENABLED": "true",
        "HERMES_LLM_API_CALL_ENABLED": "true",
        "HERMES_LLM_DRY_CALL_MODE": "private_test_only",
        "HERMES_LLM_PRIVATE_TEST_ONLY": "true",
        "HERMES_LLM_COST_GUARD_ENABLED": "true",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_DISCORD_SEND_MESSAGES": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
    }


def success_runner(envelope: dict, config: dict) -> dict:
    return {
        "result_type": "llm_client_result",
        "version": "phase32b_private_test_dry_call",
        "provider": config.get("provider", "openrouter"),
        "model": config.get("model", "openai/gpt-5.4-mini"),
        "api_call_attempted": True,
        "api_call_succeeded": True,
        "api_call_failed": False,
        "error_type": None,
        "provider_status_code": None,
        "provider_error_code": None,
        "provider_error_message": None,
        "provider_response_redacted": False,
        "response_text": "This is a review-only draft. No external action has been taken. Evidence is sufficient for human review.",
        "usage": {
            "input_chars": len(json.dumps(envelope.get("messages_preview", []), ensure_ascii=False)),
            "output_chars": 98,
            "estimated_cost_krw": 0,
            "provider_usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        },
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def provider_error_runner(envelope: dict, config: dict) -> dict:
    return dict(success_runner(envelope, config), api_call_succeeded=False, api_call_failed=True, error_type="provider_error", response_text="")


def unsafe_output_runner(envelope: dict, config: dict) -> dict:
    return dict(success_runner(envelope, config), response_text="I published it.")


def test_default_blocks_actual_api_call() -> None:
    report = build_rag_evidence_llm_dry_call_report(ROOT)
    assert_true(report["blocked"] is True, "Default report should block")
    assert_true(report["actual_llm_api_call"] is False, "Default should not perform actual API call")
    assert_true(report["api_call_attempted"] is False, "Default should not attempt API call")


def test_allow_flag_missing_blocks() -> None:
    report = build_rag_evidence_llm_dry_call_report(ROOT, env=approved_env(), client_runner=success_runner)
    assert_true("allow_rag_evidence_llm_api_call_required" in report["blocked_reasons"], "Allow flag should be required")
    assert_true(report["api_call_attempted"] is False, "Blocked allow gate should not attempt")


def test_approval_flag_true_phrase_missing_blocks() -> None:
    env = approved_env()
    env["HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE"] = ""
    report = build_rag_evidence_llm_dry_call_report(ROOT, allow_api_call=True, env=env, client_runner=success_runner)
    assert_true("manual_approval_required" in report["blocked_reasons"], "Approval phrase should be required")
    assert_true(report["manual_approval"]["approval_phrase_present"] is False, "Phrase presence should be false")


def test_phrase_correct_but_flag_false_blocks() -> None:
    env = approved_env()
    env["HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED"] = "false"
    report = build_rag_evidence_llm_dry_call_report(ROOT, allow_api_call=True, env=env, client_runner=success_runner)
    assert_true(report["manual_approval"]["approved"] is False, "Flag false should block")
    assert_true("manual_approval_required" in report["blocked_reasons"], "Manual approval should be required")


def test_approved_flag_and_phrase_allow_mock_dry_call_path() -> None:
    report = build_rag_evidence_llm_dry_call_report(ROOT, allow_api_call=True, env=approved_env(), client_runner=success_runner)
    assert_true(report["ready"] is True, "Approved mock path should be ready")
    assert_true(report["api_call_attempted"] is True, "Mock provider should be attempted")
    assert_true(report["actual_llm_api_call"] is False, "Mock provider is not an actual API call")


def test_mock_provider_success_creates_response_packet() -> None:
    report = build_rag_evidence_llm_dry_call_report(ROOT, allow_api_call=True, env=approved_env(), client_runner=success_runner)
    assert_true(report["llm_response_packet_created"] is True, "Successful safe response should create packet")
    assert_true(report["output_safety_allowed"] is True, "Safe output should pass")


def test_mock_provider_error_blocks_response_packet() -> None:
    report = build_rag_evidence_llm_dry_call_report(ROOT, allow_api_call=True, env=approved_env(), client_runner=provider_error_runner)
    assert_true(report["ready"] is False, "Provider error should not be ready")
    assert_true(report["llm_response_packet_created"] is False, "Provider error should not create packet")


def test_output_safety_block_prevents_ready() -> None:
    report = build_rag_evidence_llm_dry_call_report(ROOT, allow_api_call=True, env=approved_env(), client_runner=unsafe_output_runner)
    assert_true(report["ready"] is False, "Unsafe output should not be ready")
    assert_true(report["output_safety_allowed"] is False, "Unsafe output should be blocked")
    assert_true(report["llm_response_packet_created"] is False, "Unsafe output should not create packet")


def test_safety_flags_always_false() -> None:
    report = build_rag_evidence_llm_dry_call_report(ROOT, allow_api_call=True, env=approved_env(), client_runner=success_runner)
    assert_true(report["ready_for_discord_send"] is False, "Discord send readiness must remain false")
    assert_true(report["discord_message_sent"] is False, "Discord message sent must remain false")
    assert_true(report["embedding_api_called"] is False, "Embedding API must remain false")
    assert_true(report["external_execution"] is False, "External execution must remain false")


def test_sensitive_values_not_logged() -> None:
    report = build_rag_evidence_llm_dry_call_report(ROOT, allow_api_call=True, env=approved_env(), client_runner=success_runner)
    text = json.dumps(report, ensure_ascii=False)
    assert_true(APPROVAL_PHRASE not in text, "Approval phrase value must not be logged")
    assert_true("sk-test-value" not in text, "API key value must not be logged")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like ID must not be logged")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_llm_dry_call_markdown(build_rag_evidence_llm_dry_call_report(ROOT))
    assert_true("RAG Evidence LLM Dry Call" in markdown, "Markdown should render")
    assert_true(APPROVAL_PHRASE not in markdown, "Markdown should not include approval phrase")


def main() -> int:
    tests = [
        test_default_blocks_actual_api_call,
        test_allow_flag_missing_blocks,
        test_approval_flag_true_phrase_missing_blocks,
        test_phrase_correct_but_flag_false_blocks,
        test_approved_flag_and_phrase_allow_mock_dry_call_path,
        test_mock_provider_success_creates_response_packet,
        test_mock_provider_error_blocks_response_packet,
        test_output_safety_block_prevents_ready,
        test_safety_flags_always_false,
        test_sensitive_values_not_logged,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence LLM dry call tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
