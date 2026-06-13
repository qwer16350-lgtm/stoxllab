"""Phase 32A LLM safety policy and prompt envelope tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_safety_policy.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from llm_prompt_envelope import (
    assert_llm_prompt_envelope_safe,
    build_llm_prompt_envelope,
    redact_llm_prompt_content,
)
from llm_safety_policy import (
    assert_llm_safety_policy_safe,
    build_llm_safety_policy,
    build_llm_safety_policy_report,
    check_llm_output_allowed,
    check_llm_request_allowed,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def policy() -> dict:
    return build_llm_safety_policy({})


def test_private_test_only_true() -> None:
    selected = policy()
    assert_true(selected["private_test_only"] is True, "LLM policy should default to private test only")


def test_public_channel_request_blocked() -> None:
    decision = check_llm_request_allowed({"channel_scope": "team_channel"}, policy())
    assert_true("public_or_team_channel_blocked" in decision["blocked_reasons"], "Public/team channels should block")


def test_external_execution_request_blocked() -> None:
    decision = check_llm_request_allowed({"request_external_execution": True}, policy())
    assert_true("external_execution_blocked" in decision["blocked_reasons"], "External execution should block")


def test_rag_request_blocked() -> None:
    decision = check_llm_request_allowed({"request_rag": True}, policy())
    assert_true("rag_blocked" in decision["blocked_reasons"], "RAG should block in Phase 32A")


def test_discord_send_request_blocked() -> None:
    decision = check_llm_request_allowed({"request_discord_send": True}, policy())
    assert_true("discord_send_blocked" in decision["blocked_reasons"], "Discord send should block")


def test_blocked_output_intents_detected() -> None:
    decision = check_llm_output_allowed("SNS 게시를 바로 진행하겠습니다.", policy())
    assert_true(decision["blocked"] is True, "Publishing output should block")
    assert_true("sns_publish" in decision["matched_blocked_intents"], "SNS publish intent should be detected")


def test_price_contract_delivery_confirm_output_blocked() -> None:
    assert_true(check_llm_output_allowed("가격을 확정했습니다.", policy())["blocked"] is True, "Price confirm should block")
    assert_true(check_llm_output_allowed("계약 승인 처리하겠습니다.", policy())["blocked"] is True, "Contract confirm should block")
    assert_true(check_llm_output_allowed("납기 일정을 확정했습니다.", policy())["blocked"] is True, "Delivery confirm should block")


def test_normal_draft_output_allowed_as_review_only() -> None:
    decision = check_llm_output_allowed("검토용 초안입니다. 루시 확인 후 승인 요청해 주세요.", policy())
    assert_true(decision["allowed"] is True, "Review-only draft should be allowed")
    assert_true(decision["review_required"] is True, "Review should still be required")


def test_prompt_envelope_creation_possible() -> None:
    envelope = build_llm_prompt_envelope("marin", "SNS 초안 검토 부탁드립니다.")
    assert_true(envelope["agent_route_candidate"] == "marin", "Envelope should include agent candidate")
    assert_true(envelope["channel_scope"] == "private_test_only", "Envelope should stay private test only")


def test_prompt_envelope_redacts_token_like_value() -> None:
    envelope = build_llm_prompt_envelope("marin", "api_key=secret-value sk-testsecret")
    text = json.dumps(envelope, ensure_ascii=False).lower()
    assert_true("sk-testsecret" not in text, "Token-like value should be redacted")
    assert_true("api_key=secret-value" not in text, "API key assignment should be redacted")


def test_prompt_envelope_redacts_discord_like_id() -> None:
    envelope = build_llm_prompt_envelope("lucy", "author 123456789012345678")
    text = json.dumps(envelope, ensure_ascii=False)
    assert_true("123456789012345678" not in text, "Raw Discord-like ID should be redacted")
    assert_true("[REDACTED_DISCORD_ID]" in text, "Redaction marker should remain")


def test_prompt_envelope_max_input_chars_applied() -> None:
    preview = redact_llm_prompt_content("abcdef", max_chars=3)
    assert_true(preview == "abc", "Prompt preview should apply max input chars")
    envelope = build_llm_prompt_envelope("reze", "abcdef", policy={"max_input_chars": 3})
    assert_true(envelope["messages_preview"][1]["content"] == "abc", "Envelope should use truncated preview")


def test_no_api_call() -> None:
    report = build_llm_safety_policy_report({})
    assert_true(report["llm_api_called"] is False, "Policy report should not call LLM")
    assert_llm_safety_policy_safe(report)


def test_no_discord_send() -> None:
    report = build_llm_safety_policy_report({})
    assert_true(report["message_sent"] is False, "Policy report should not send Discord messages")


def test_no_rag_external() -> None:
    report = build_llm_safety_policy_report({})
    assert_true(report["rag_called"] is False, "Policy report should not call RAG")
    assert_true(report["external_execution"] is False, "Policy report should not execute external actions")
    envelope = build_llm_prompt_envelope("kasumi", "지원사업 조건 정리")
    assert_llm_prompt_envelope_safe(envelope)
    assert_true(envelope["safety_assertions"]["rag_called"] is False, "Envelope should not call RAG")


def test_actual_publish_claim_blocks() -> None:
    decision = check_llm_output_allowed("I published it.", policy())
    assert_true("public_publish_claim" in decision["blocked_reasons"], "Actual publish claim should block")


def test_actual_submit_claim_blocks() -> None:
    decision = check_llm_output_allowed("I submitted the application.", policy())
    assert_true("submission_claim" in decision["blocked_reasons"], "Actual submit claim should block")


def test_actual_email_sent_claim_blocks() -> None:
    decision = check_llm_output_allowed("I sent the email.", policy())
    assert_true("email_send_claim" in decision["blocked_reasons"], "Actual email sent claim should block")


def test_actual_approval_claim_blocks() -> None:
    decision = check_llm_output_allowed("This is approved.", policy())
    assert_true("approval_claim" in decision["blocked_reasons"], "Actual approval claim should block")


def test_actual_price_contract_delivery_confirmation_claims_block() -> None:
    selected = policy()
    assert_true("price_confirmation_claim" in check_llm_output_allowed("The price is confirmed.", selected)["blocked_reasons"], "Price confirmation should block")
    assert_true("contract_confirmation_claim" in check_llm_output_allowed("The contract is confirmed.", selected)["blocked_reasons"], "Contract confirmation should block")
    assert_true("delivery_confirmation_claim" in check_llm_output_allowed("The delivery date is confirmed.", selected)["blocked_reasons"], "Delivery confirmation should block")


def test_negated_publishing_disclaimer_allowed() -> None:
    decision = check_llm_output_allowed("No final publishing has been made.", policy())
    assert_true(decision["allowed"] is True, "Negated publishing disclaimer should be allowed")
    assert_true("negated_publication" in decision["safe_disclaimer_reasons"], "Safe disclaimer reason should be recorded")


def test_negated_external_delivery_disclaimer_allowed() -> None:
    decision = check_llm_output_allowed("No external delivery has been made.", policy())
    assert_true(decision["allowed"] is True, "Negated external delivery disclaimer should be allowed")
    assert_true("negated_external_delivery" in decision["safe_disclaimer_reasons"], "External delivery disclaimer should be recorded")


def test_negated_external_action_disclaimer_allowed() -> None:
    decision = check_llm_output_allowed("No external action has been taken.", policy())
    assert_true(decision["allowed"] is True, "Negated external action disclaimer should be allowed")
    assert_true(decision["blocked"] is False, "Negated external action disclaimer should not block")
    assert_true("negated_external_action" in decision["safe_disclaimer_reasons"], "External action disclaimer should be recorded")


def test_negated_external_actions_plural_disclaimer_allowed() -> None:
    decision = check_llm_output_allowed("No external actions have been taken.", policy())
    assert_true(decision["allowed"] is True, "Plural negated external actions disclaimer should be allowed")
    assert_true("negated_external_action" in decision["safe_disclaimer_reasons"], "Plural external action disclaimer should be recorded")


def test_not_taken_any_external_action_allowed() -> None:
    decision = check_llm_output_allowed("I have not taken any external action.", policy())
    assert_true(decision["allowed"] is True, "Not-taken external action disclaimer should be allowed")
    assert_true("negated_external_action" in decision["safe_disclaimer_reasons"], "Not-taken external action disclaimer should be recorded")


def test_no_action_taken_allowed() -> None:
    decision = check_llm_output_allowed("No action has been taken.", policy())
    assert_true(decision["allowed"] is True, "No action taken disclaimer should be allowed")
    assert_true("negated_external_action" in decision["safe_disclaimer_reasons"], "No action taken disclaimer should be recorded")


def test_no_external_execution_occurred_allowed() -> None:
    decision = check_llm_output_allowed("No external execution occurred.", policy())
    assert_true(decision["allowed"] is True, "No external execution occurred disclaimer should be allowed")
    assert_true("negated_external_action" in decision["safe_disclaimer_reasons"], "No external execution disclaimer should be recorded")


def test_nothing_has_been_externally_done_allowed() -> None:
    decision = check_llm_output_allowed("Nothing has been published, submitted, sent, uploaded, approved, confirmed, or externally delivered.", policy())
    assert_true(decision["allowed"] is True, "Broad negated external action disclaimer should be allowed")
    assert_true("negated_external_action" in decision["safe_disclaimer_reasons"], "Broad negated external action disclaimer should be recorded")


def test_external_action_has_been_taken_blocks() -> None:
    decision = check_llm_output_allowed("External action has been taken.", policy())
    assert_true("external_action_claim" in decision["blocked_reasons"], "Positive external action claim should block")


def test_i_took_external_action_blocks() -> None:
    decision = check_llm_output_allowed("I took external action.", policy())
    assert_true("external_action_claim" in decision["blocked_reasons"], "First-person external action claim should block")


def test_negated_email_sent_disclaimer_allowed() -> None:
    decision = check_llm_output_allowed("No email has been sent.", policy())
    assert_true(decision["allowed"] is True, "Negated email sent disclaimer should be allowed")
    assert_true("negated_email_send" in decision["safe_disclaimer_reasons"], "Email disclaimer should be recorded")


def test_review_only_disclaimer_allowed() -> None:
    decision = check_llm_output_allowed("This is for internal review only.", policy())
    assert_true(decision["allowed"] is True, "Review-only disclaimer should be allowed")
    assert_true("review_only" in decision["safe_disclaimer_reasons"], "Review-only reason should be recorded")


def test_no_approval_granted_disclaimer_allowed() -> None:
    decision = check_llm_output_allowed("No approval has been granted.", policy())
    assert_true(decision["allowed"] is True, "Negated approval disclaimer should be allowed")
    assert_true("negated_approval" in decision["safe_disclaimer_reasons"], "Approval disclaimer should be recorded")


def main() -> int:
    tests = [
        test_private_test_only_true,
        test_public_channel_request_blocked,
        test_external_execution_request_blocked,
        test_rag_request_blocked,
        test_discord_send_request_blocked,
        test_blocked_output_intents_detected,
        test_price_contract_delivery_confirm_output_blocked,
        test_normal_draft_output_allowed_as_review_only,
        test_prompt_envelope_creation_possible,
        test_prompt_envelope_redacts_token_like_value,
        test_prompt_envelope_redacts_discord_like_id,
        test_prompt_envelope_max_input_chars_applied,
        test_no_api_call,
        test_no_discord_send,
        test_no_rag_external,
        test_actual_publish_claim_blocks,
        test_actual_submit_claim_blocks,
        test_actual_email_sent_claim_blocks,
        test_actual_approval_claim_blocks,
        test_actual_price_contract_delivery_confirmation_claims_block,
        test_negated_publishing_disclaimer_allowed,
        test_negated_external_delivery_disclaimer_allowed,
        test_negated_external_action_disclaimer_allowed,
        test_negated_external_actions_plural_disclaimer_allowed,
        test_not_taken_any_external_action_allowed,
        test_no_action_taken_allowed,
        test_no_external_execution_occurred_allowed,
        test_nothing_has_been_externally_done_allowed,
        test_external_action_has_been_taken_blocks,
        test_i_took_external_action_blocks,
        test_negated_email_sent_disclaimer_allowed,
        test_review_only_disclaimer_allowed,
        test_no_approval_granted_disclaimer_allowed,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM safety policy tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
