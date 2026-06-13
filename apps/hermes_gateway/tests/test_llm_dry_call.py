"""Phase 32B private test LLM dry call tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_dry_call.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

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
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM dry call tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
