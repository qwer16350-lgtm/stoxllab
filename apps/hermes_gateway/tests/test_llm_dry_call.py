"""Phase 32B private test LLM dry call tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_dry_call.py
"""

from __future__ import annotations

import json
import contextlib
import io
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import cli
import llm_dry_call
from llm_dry_call import (
    assert_llm_dry_call_report_safe,
    build_llm_dry_call_request,
    render_llm_dry_call_markdown,
    run_llm_dry_call,
    write_llm_dry_call_artifact,
)
from llm_safety_policy import build_llm_safety_policy, check_llm_output_allowed


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_default_dry_call_uses_mock_response() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request())
    assert_true("[Mock LLM dry call]" in report["client_result"]["response_text"], "Default dry call should use mock response")


def test_default_dry_call_actual_api_not_attempted() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request())
    assert_true(report["client_result"]["api_call_attempted"] is False, "Default dry call should not attempt API")


def test_allow_api_call_false_no_api_call() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(), allow_api_call=False)
    assert_true(report["client_result"]["api_call_attempted"] is False, "allow_api_call=false should not call API")


def test_allow_api_call_true_env_incomplete_blocks() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(), allow_api_call=True)
    assert_true(report["client_result"]["api_call_attempted"] is False, "Incomplete env should block before API call")
    assert_true(report["client_result"]["error_type"] == "api_call_gate_blocked", "Blocked actual call should be explicit")


def test_discord_send_enabled_blocks() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(), env={"HERMES_LLM_DISCORD_SEND_ENABLED": "true"}, allow_api_call=True)
    assert_true(report["client_result"]["api_call_attempted"] is False, "Discord send enabled should block")
    assert_true(report["message_sent"] is False, "Discord send must remain false")


def test_rag_enabled_blocks() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(), env={"HERMES_DISCORD_RAG_ENABLED": "true"}, allow_api_call=True)
    assert_true(report["client_result"]["api_call_attempted"] is False, "RAG enabled should block")
    assert_true(report["rag_called"] is False, "RAG should not be called")


def test_external_execution_enabled_blocks() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(), env={"HERMES_DISCORD_EXTERNAL_EXECUTION": "true"}, allow_api_call=True)
    assert_true(report["client_result"]["api_call_attempted"] is False, "External execution enabled should block")
    assert_true(report["external_execution"] is False, "External execution should stay false")


def test_prompt_envelope_included() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(agent_route_candidate="reze"))
    assert_true(report["prompt_envelope"]["agent_route_candidate"] == "reze", "Report should include prompt envelope")


def test_output_safety_empty_output_block() -> None:
    decision = check_llm_output_allowed("", build_llm_safety_policy({}))
    assert_true("empty_output" in decision["blocked_reasons"], "Empty output should block")


def test_output_too_long_block() -> None:
    policy = build_llm_safety_policy({})
    policy["max_output_chars"] = 3
    decision = check_llm_output_allowed("abcd", policy)
    assert_true("output_too_long" in decision["blocked_reasons"], "Too-long output should block")


def test_external_action_claim_block() -> None:
    decision = check_llm_output_allowed("I will submit the application now.", build_llm_safety_policy({}))
    assert_true("external_action_claim" in decision["blocked_reasons"], "External action claim should block")


def test_approval_claim_block() -> None:
    decision = check_llm_output_allowed("Final approval complete.", build_llm_safety_policy({}))
    assert_true("approval_claim" in decision["blocked_reasons"], "Approval claim should block")


def test_price_contract_delivery_claim_block() -> None:
    policy = build_llm_safety_policy({})
    assert_true("price_confirmation_claim" in check_llm_output_allowed("Price confirmed.", policy)["blocked_reasons"], "Price claim should block")
    assert_true("contract_confirmation_claim" in check_llm_output_allowed("Contract confirmed.", policy)["blocked_reasons"], "Contract claim should block")
    assert_true("delivery_confirmation_claim" in check_llm_output_allowed("Delivery confirmed.", policy)["blocked_reasons"], "Delivery claim should block")


def test_normal_private_test_draft_output_allowed() -> None:
    decision = check_llm_output_allowed("Review-only draft. Please route this to a human reviewer.", build_llm_safety_policy({}))
    assert_true(decision["allowed"] is True, "Normal private test draft should be allowed")


def test_artifact_write_possible() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request())
    with tempfile.TemporaryDirectory() as temp:
        result = write_llm_dry_call_artifact(report, root=temp)
        assert_true(len(result["artifact_paths"]) == 2, "Artifact writer should create JSON and Markdown paths")
        for path in result["artifact_paths"]:
            assert_true(Path(path).exists(), "Artifact path should exist")


def test_markdown_render_possible() -> None:
    markdown = render_llm_dry_call_markdown(run_llm_dry_call(build_llm_dry_call_request()))
    assert_true("# LLM Dry Call Report" in markdown, "Markdown renderer should work")


def test_report_has_message_sent_false() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request())
    assert_true(report["message_sent"] is False, "Report should not mark message sent")


def test_report_has_discord_send_attempted_false() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request())
    assert_true(report["discord_send_attempted"] is False, "Report should not attempt Discord send")


def test_api_key_value_not_logged() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(), env={"HERMES_LLM_API_KEY": "sk-secret"})
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-secret" not in text and "sk-" not in text, "API key should not be logged")
    assert_llm_dry_call_report_safe(report)


def test_raw_discord_id_not_logged() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(user_content_preview="123456789012345678"))
    text = json.dumps(report, ensure_ascii=False)
    assert_true("123456789012345678" not in text, "Raw Discord ID should not appear")
    assert_llm_dry_call_report_safe(report)


def complete_env() -> dict[str, str]:
    return {
        "HERMES_LLM_ENABLED": "true",
        "HERMES_LLM_API_CALL_ENABLED": "true",
        "HERMES_LLM_PROVIDER": "openrouter",
        "HERMES_LLM_MODEL": "openai/gpt-5.4-mini",
        "HERMES_LLM_API_KEY": "present",
        "HERMES_LLM_DRY_CALL_MODE": "private_test_only",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_DISCORD_SEND_MESSAGES": "false",
        "HERMES_LLM_PRIVATE_TEST_ONLY": "true",
        "HERMES_LLM_COST_GUARD_ENABLED": "true",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
    }


def provider_error_result() -> dict:
    return {
        "result_type": "llm_client_result",
        "version": "phase32b_private_test_dry_call",
        "provider": "openrouter",
        "model": "openai/gpt-5.4-mini",
        "api_call_attempted": True,
        "api_call_succeeded": False,
        "api_call_failed": True,
        "error_type": "provider_error",
        "provider_status_code": 400,
        "provider_error_code": "model_not_found",
        "provider_error_message": "model not found",
        "provider_response_redacted": True,
        "response_text": "",
        "usage": {"input_chars": 0, "output_chars": 0, "estimated_cost_krw": None, "provider_usage": {}},
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def provider_success_with_disclaimer() -> dict:
    return {
        "result_type": "llm_client_result",
        "version": "phase32b_private_test_dry_call",
        "provider": "openrouter",
        "model": "openai/gpt-5.4-mini",
        "api_call_attempted": True,
        "api_call_succeeded": True,
        "api_call_failed": False,
        "error_type": None,
        "provider_status_code": None,
        "provider_error_code": None,
        "provider_error_message": None,
        "provider_response_redacted": False,
        "response_text": "Review-only draft. No final publishing or external delivery has been made.",
        "usage": {"input_chars": 10, "output_chars": 72, "estimated_cost_krw": None, "provider_usage": {"prompt_tokens": 10}},
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def test_run_allow_api_call_true_updates_request_field() -> None:
    original = llm_dry_call.call_llm_once
    try:
        llm_dry_call.call_llm_once = lambda envelope, config: provider_error_result()
        report = llm_dry_call.run_llm_dry_call(build_llm_dry_call_request(), env=complete_env(), allow_api_call=True)
    finally:
        llm_dry_call.call_llm_once = original
    assert_true(report["request"]["allow_api_call"] is True, "Report request should reflect allow_api_call=true")


def test_cli_allow_flag_updates_request_field() -> None:
    original = llm_dry_call.call_llm_once
    buffer = io.StringIO()
    try:
        llm_dry_call.call_llm_once = lambda envelope, config: provider_error_result()
        with contextlib.redirect_stdout(buffer):
            code = cli.main(["--llm-dry-call-report", "--json", "--allow-llm-api-call"])
    finally:
        llm_dry_call.call_llm_once = original
    output = json.loads(buffer.getvalue())
    assert_true(code == 0, "CLI should complete")
    assert_true(output["request"]["allow_api_call"] is True, "CLI flag should be reflected in report request")


def test_allow_api_call_false_still_not_attempted() -> None:
    report = run_llm_dry_call(build_llm_dry_call_request(), env=complete_env(), allow_api_call=False)
    assert_true(report["request"]["allow_api_call"] is False, "False flag should remain false")
    assert_true(report["client_result"]["api_call_attempted"] is False, "False flag should use mock path")


def test_allow_api_call_true_provider_error_attempted_failed() -> None:
    original = llm_dry_call.call_llm_once
    try:
        llm_dry_call.call_llm_once = lambda envelope, config: provider_error_result()
        report = llm_dry_call.run_llm_dry_call(build_llm_dry_call_request(), env=complete_env(), allow_api_call=True)
    finally:
        llm_dry_call.call_llm_once = original
    assert_true(report["client_result"]["api_call_attempted"] is True, "Provider error should show attempted")
    assert_true(report["client_result"]["api_call_failed"] is True, "Provider error should show failed")


def test_provider_error_keeps_all_execution_flags_false() -> None:
    original = llm_dry_call.call_llm_once
    try:
        llm_dry_call.call_llm_once = lambda envelope, config: provider_error_result()
        report = llm_dry_call.run_llm_dry_call(build_llm_dry_call_request(), env=complete_env(), allow_api_call=True)
    finally:
        llm_dry_call.call_llm_once = original
    assert_true(report["message_sent"] is False, "Provider error should not send messages")
    assert_true(report["discord_send_attempted"] is False, "Provider error should not attempt Discord send")
    assert_true(report["rag_called"] is False, "Provider error should not call RAG")
    assert_true(report["external_execution"] is False, "Provider error should not execute externally")


def test_openrouter_success_review_only_disclaimer_passes_output_safety() -> None:
    original = llm_dry_call.call_llm_once
    try:
        llm_dry_call.call_llm_once = lambda envelope, config: provider_success_with_disclaimer()
        report = llm_dry_call.run_llm_dry_call(build_llm_dry_call_request(), env=complete_env(), allow_api_call=True)
    finally:
        llm_dry_call.call_llm_once = original
    assert_true(report["client_result"]["api_call_succeeded"] is True, "Provider success should be represented")
    assert_true(report["output_safety"]["allowed"] is True, "Review-only disclaimer should pass output safety")
    assert_true(report["output_safety"]["blocked"] is False, "Review-only disclaimer should not be blocked")


def test_openrouter_success_disclaimer_keeps_execution_flags_false() -> None:
    original = llm_dry_call.call_llm_once
    try:
        llm_dry_call.call_llm_once = lambda envelope, config: provider_success_with_disclaimer()
        report = llm_dry_call.run_llm_dry_call(build_llm_dry_call_request(), env=complete_env(), allow_api_call=True)
    finally:
        llm_dry_call.call_llm_once = original
    assert_true(report["message_sent"] is False, "Successful LLM response should not send Discord message")
    assert_true(report["discord_send_attempted"] is False, "Successful LLM response should not attempt Discord send")
    assert_true(report["rag_called"] is False, "Successful LLM response should not call RAG")
    assert_true(report["external_execution"] is False, "Successful LLM response should not execute externally")


def test_openrouter_success_disclaimer_has_no_secret_or_raw_id() -> None:
    original = llm_dry_call.call_llm_once
    try:
        llm_dry_call.call_llm_once = lambda envelope, config: provider_success_with_disclaimer()
        report = llm_dry_call.run_llm_dry_call(
            build_llm_dry_call_request(user_content_preview="token=abc 123456789012345678"),
            env={**complete_env(), "HERMES_LLM_API_KEY": "sk-secret"},
            allow_api_call=True,
        )
    finally:
        llm_dry_call.call_llm_once = original
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-secret" not in text and "token=abc" not in text, "API key and token-like text should not be logged")
    assert_true("123456789012345678" not in text, "Raw Discord-like ID should not be logged")


def main() -> int:
    tests = [
        test_default_dry_call_uses_mock_response,
        test_default_dry_call_actual_api_not_attempted,
        test_allow_api_call_false_no_api_call,
        test_allow_api_call_true_env_incomplete_blocks,
        test_discord_send_enabled_blocks,
        test_rag_enabled_blocks,
        test_external_execution_enabled_blocks,
        test_prompt_envelope_included,
        test_output_safety_empty_output_block,
        test_output_too_long_block,
        test_external_action_claim_block,
        test_approval_claim_block,
        test_price_contract_delivery_claim_block,
        test_normal_private_test_draft_output_allowed,
        test_artifact_write_possible,
        test_markdown_render_possible,
        test_report_has_message_sent_false,
        test_report_has_discord_send_attempted_false,
        test_api_key_value_not_logged,
        test_raw_discord_id_not_logged,
        test_run_allow_api_call_true_updates_request_field,
        test_cli_allow_flag_updates_request_field,
        test_allow_api_call_false_still_not_attempted,
        test_allow_api_call_true_provider_error_attempted_failed,
        test_provider_error_keeps_all_execution_flags_false,
        test_openrouter_success_review_only_disclaimer_passes_output_safety,
        test_openrouter_success_disclaimer_keeps_execution_flags_false,
        test_openrouter_success_disclaimer_has_no_secret_or_raw_id,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM dry call tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
