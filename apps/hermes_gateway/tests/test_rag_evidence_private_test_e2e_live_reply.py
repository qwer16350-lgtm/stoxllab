"""Phase 34L-1 manual private-test E2E live reply tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_private_test_e2e_live_reply.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_llm_dry_call import APPROVAL_PHRASE as LLM_APPROVAL_PHRASE
from rag_evidence_private_test_e2e_live_reply import (
    APPROVAL_PHRASE,
    build_legacy_invalid_safety_ordering_report,
    build_legacy_llm_allowed_noop_report,
    build_legacy_openrouter_key_detection_failure_report,
    build_rag_evidence_private_test_e2e_live_reply_report,
    render_rag_evidence_private_test_e2e_live_reply_markdown,
)


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env(**overrides: str) -> dict[str, str]:
    env = {
        "HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVED": "true",
        "HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED": "true",
        "HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE": LLM_APPROVAL_PHRASE,
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
        "HERMES_LLM_PROVIDER": "openrouter",
        "HERMES_LLM_MODEL": "openai/gpt-5.4-mini",
        "HERMES_LLM_ENABLED": "true",
        "HERMES_LLM_API_CALL_ENABLED": "true",
        "HERMES_LLM_DRY_CALL_MODE": "private_test_only",
        "HERMES_LLM_PRIVATE_TEST_ONLY": "true",
        "HERMES_LLM_COST_GUARD_ENABLED": "true",
        "HERMES_LLM_API_KEY": "",
    }
    env.update(overrides)
    return env


def private_event(**overrides: object) -> dict[str, object]:
    event = {
        "message_id": "message_redacted_0001",
        "channel_id": "private_test_channel",
        "channel_name": "hermes-private-test",
        "channel_scope": "private_test_only",
        "author_is_bot": False,
        "is_self": False,
        "content": "카스미 operation evidence를 검토해줘",
    }
    event.update(overrides)
    return event


def mock_client_runner(envelope: dict, config: dict) -> dict:
    assert_true(config["provider"] == "openrouter", "Provider should be OpenRouter")
    return {
        "result_type": "llm_client_result",
        "version": "phase32b_private_test_dry_call",
        "provider": config.get("provider", ""),
        "model": config.get("model", ""),
        "api_call_attempted": True,
        "api_call_succeeded": True,
        "api_call_failed": False,
        "error_type": None,
        "provider_status_code": None,
        "provider_error_code": None,
        "provider_error_message": None,
        "provider_response_redacted": False,
        "response_text": "This is a review-only draft. No external action has been taken.",
        "usage": {"input_chars": 10, "output_chars": 64, "estimated_cost_krw": None, "provider_usage": {}},
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def mock_sender(channel_id: str, content: str) -> dict:
    assert_true(channel_id == "private_test_channel", "Only private test channel should be used")
    assert_true("[PRIVATE TEST E2E / REVIEW ONLY]" in content, "Review-only E2E marker should be present")
    assert_true("No external action has been taken." in content, "Safety disclaimer should be present")
    return {"sent": True, "message_id": "redacted_message_id"}


def disconnecting_sender(channel_id: str, content: str) -> dict:
    assert_true(channel_id == "private_test_channel", "Only private test channel should be used")
    assert_true(content, "Content should be prepared before send disconnect")
    return {"sent": False, "error_type": "ServerDisconnectedError"}


def test_default_blocks_live_e2e() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(root=ROOT)
    assert_true(report["blocked"] is True, "Default should block")
    assert_true(report["discord_live_runtime_executed"] is False, "Default should not run live runtime")
    assert_true(report["llm_api_called"] is False, "Default should not call LLM")
    assert_true(report["llm_stage_reached"] is False, "Default should not reach LLM stage")
    assert_true(report["llm_call_allowed"] is False, "Default should not allow LLM call")
    assert_true(report["llm_api_call_attempted"] is False, "Default should not attempt LLM call")
    assert_true(report["prompt_safety_checked"] is False, "Default should not check prompt safety")
    assert_true(report["output_safety_checked"] is False, "Default should not check output safety")
    assert_true(report["discord_message_sent"] is False, "Default should not send")


def test_allow_flag_missing_blocks_live_e2e() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(root=ROOT, env=ready_env(), event=private_event(), client_runner=mock_client_runner, sender=mock_sender)
    assert_true("allow_rag_evidence_private_test_e2e_live_reply_required" in report["blocked_reasons"], "Allow flag should be required")


def test_approval_flag_true_but_phrase_missing_blocks() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVAL_PHRASE=""),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("manual_approval_required" in report["blocked_reasons"], "Missing approval phrase should block")


def test_approval_phrase_correct_but_flag_false_blocks() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVED="false"),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("manual_approval_required" in report["blocked_reasons"], "Approval flag false should block")


def test_llm_approval_missing_blocks_llm_call() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED="false"),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("llm_manual_approval_required" in report["blocked_reasons"], "LLM manual approval should be required")
    assert_true(report["llm_api_called"] is False, "LLM should not be called")
    assert_true(report["llm_stage_reached"] is False, "LLM stage should not be reached")


def test_send_messages_false_blocks_send() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(HERMES_DISCORD_SEND_MESSAGES="false"),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("discord_send_messages_disabled" in report["blocked_reasons"], "send_messages false should block")


def test_private_test_reply_false_blocks_send() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(HERMES_DISCORD_PRIVATE_TEST_REPLY="false"),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("discord_private_test_reply_disabled" in report["blocked_reasons"], "private test reply false should block")


def test_reply_mode_not_private_test_only_blocks() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(HERMES_DISCORD_REPLY_MODE="public"),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("reply_mode_not_private_test_only" in report["blocked_reasons"], "Reply mode should be private-test only")


def test_missing_private_test_channel_id_blocks() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=""),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("private_test_channel_id_missing" in report["blocked_reasons"], "Private channel id should be required")


def test_public_team_channel_event_rejected() -> None:
    public = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(),
        event=private_event(channel_id="public_channel", channel_scope="public"),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    team = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(),
        event=private_event(channel_id="team_channel", channel_scope="team"),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("public_channel_event_rejected" in public["blocked_reasons"], "Public channel event should be rejected")
    assert_true("team_channel_event_rejected" in team["blocked_reasons"], "Team channel event should be rejected")


def test_private_test_event_accepted_and_sends_once() -> None:
    state = {"processed_message_ids": [], "sent_message_keys": [], "message_sent_count": 0, "llm_api_call_count": 0}
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
        state=state,
    )
    assert_true(report["accepted_private_test_channel"] is True, "Private test channel should be accepted")
    assert_true(report["knowledge_dry_chain_executed"] is True, "Knowledge dry chain should run")
    assert_true(report["prompt_envelope_created"] is True, "Prompt envelope should be created")
    assert_true(report["prompt_safety_checked"] is True, "Prompt safety should be checked before LLM")
    assert_true(report["prompt_safety_allowed"] is True, "Prompt safety should pass")
    assert_true(report["llm_stage_reached"] is True, "Prompt safety allowed should reach LLM stage")
    assert_true(report["llm_call_allowed"] is True, "LLM call should be allowed in approved mock success")
    assert_true(report["llm_dispatch_invoked"] is True, "LLM dispatch should be invoked in approved mock success")
    assert_true(report["llm_dispatch_mode"] == "mock_openrouter_once", "Mock dispatch mode should be explicit")
    assert_true(report["llm_dispatch_blocked_reason"] == "", "Allowed LLM call should not have blocked reason")
    assert_true(report["llm_api_call_attempted"] is True, "Mock success should attempt LLM call")
    assert_true(report["llm_api_called"] is True, "Mock LLM should be called")
    assert_true(report["llm_api_call_count"] == 1, "LLM call count should be exactly one")
    assert_true(report["llm_response_packet_created"] is True, "LLM response packet stage should be created")
    assert_true(report["output_safety_checked"] is True, "Output safety should be checked after response packet")
    assert_true(report["output_safety_allowed"] is True, "Output safety should pass")
    assert_true(report["discord_message_sent"] is True, "Mock Discord send should happen")
    assert_true(report["message_sent_count"] == 1, "Message sent count should be exactly one")
    assert_true(report["ready_for_phase34l2_e2e_live_reply_closeout"] is True, "Closeout should be ready")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "Unattended auto reply stays false")


def test_server_disconnected_creates_partial_success_artifact() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=disconnecting_sender,
    )
    partial = report["partial_success_artifact"]
    assert_true(report["llm_api_called"] is True, "LLM should have succeeded before send failure")
    assert_true(report["llm_api_call_count"] == 1, "Top-level LLM call count should be one")
    assert_true(report["safety_assertions"]["llm_call_count"] == 1, "Safety LLM call count should match top-level")
    assert_true(report["output_safety_allowed"] is True, "Output safety should pass before send failure")
    assert_true(report["discord_send_stage_reached"] is True, "Send stage should be reached")
    assert_true(report["discord_api_send_allowed"] is True, "Send should be allowed before disconnect")
    assert_true(report["discord_api_send_attempted"] is False, "Server disconnect before client send should not count as attempted")
    assert_true(report["discord_api_send_called"] is False, "Server disconnect before client send should not count as called")
    assert_true(report["discord_send_failed"] is True, "Send failure should be explicit")
    assert_true(report["discord_send_failure_reason"] == "ServerDisconnectedError", "Failure reason should be classified")
    assert_true(report["discord_message_sent"] is False, "No message should be sent")
    assert_true(report["message_sent_count"] == 0, "Sent count should be zero")
    assert_true(report["llm_response_available_for_send_retry"] is True, "Response should be available for retry")
    assert_true(report["ready_for_phase34l1e_send_retry_without_llm"] is True, "No-LLM retry should be prepared")
    assert_true(partial["report_type"] == "rag_evidence_private_test_e2e_partial_success", "Partial artifact should be embedded")
    assert_true(partial["send_retry_allowed_without_llm"] is True, "Partial should allow no-LLM retry")
    assert_true(partial["ready_for_manual_send_retry_without_llm"] is True, "Partial should be retry-ready")


def test_self_bot_message_skipped() -> None:
    self_report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(),
        event=private_event(is_self=True, author_is_bot=True),
        client_runner=mock_client_runner,
        sender=mock_sender,
    )
    assert_true("self_or_bot_message_skipped" in self_report["blocked_reasons"], "Self/bot message should be skipped")
    assert_true(self_report["discord_message_sent"] is False, "Self/bot message should not send")


def test_duplicate_message_and_send_blocked() -> None:
    state = {"processed_message_ids": [], "sent_message_keys": [], "message_sent_count": 0, "llm_api_call_count": 0}
    first = build_rag_evidence_private_test_e2e_live_reply_report(root=ROOT, allow_live_reply=True, env=ready_env(), event=private_event(), client_runner=mock_client_runner, sender=mock_sender, state=state)
    second = build_rag_evidence_private_test_e2e_live_reply_report(root=ROOT, allow_live_reply=True, env=ready_env(), event=private_event(), client_runner=mock_client_runner, sender=mock_sender, state=state)
    assert_true(first["message_sent_count"] == 1, "First event should send once")
    assert_true("duplicate_message_skipped" in second["blocked_reasons"], "Duplicate message should be skipped")
    assert_true(second["discord_message_sent"] is False, "Duplicate should not send")


def test_output_safety_blocked_prevents_send() -> None:
    def unsafe_runner(envelope: dict, config: dict) -> dict:
        result = mock_client_runner(envelope, config)
        result["response_text"] = "I published it."
        return result

    report = build_rag_evidence_private_test_e2e_live_reply_report(root=ROOT, allow_live_reply=True, env=ready_env(), event=private_event(), client_runner=unsafe_runner, sender=mock_sender)
    assert_true(report["llm_api_called"] is True, "LLM should be called before output safety")
    assert_true(report["llm_response_packet_created"] is True, "Response packet stage should exist before output safety")
    assert_true(report["output_safety_checked"] is True, "Output safety should be checked")
    assert_true(report["output_safety_blocked"] is True, "Output safety should block unsafe response")
    assert_true("output_safety_blocked" in report["blocked_reasons"], "Unsafe output should block")
    assert_true(report["discord_message_sent"] is False, "Unsafe output should not send")


def test_prompt_safety_blocked_prevents_llm_call() -> None:
    prompt = {
        "prompt_envelope_created": True,
        "ready_for_prompt_preview": False,
        "review_only": True,
    }
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(),
        event=private_event(),
        client_runner=mock_client_runner,
        sender=mock_sender,
        prompt_envelope=prompt,
    )
    assert_true("prompt_safety_blocked" in report["blocked_reasons"], "Prompt safety should block before LLM")
    assert_true(report["prompt_safety_checked"] is True, "Prompt safety should be checked")
    assert_true(report["prompt_safety_blocked"] is True, "Prompt safety should be blocked")
    assert_true(report["llm_api_called"] is False, "LLM should not be called after prompt block")
    assert_true(report["llm_stage_reached"] is False, "Prompt safety block should not reach LLM stage")
    assert_true(report["output_safety_checked"] is False, "Output safety should not be checked before LLM response")


def test_output_safety_not_checked_before_llm_response_exists() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(),
        event=private_event(),
        sender=mock_sender,
    )
    assert_true(report["llm_api_called"] is False, "No API key path should not call LLM")
    assert_true(report["llm_stage_reached"] is True, "Approved path should reach LLM stage")
    assert_true(report["llm_call_allowed"] is False, "Missing API key should not allow actual LLM dispatch")
    assert_true(report["llm_dispatch_invoked"] is False, "Missing API key should not invoke dispatch")
    assert_true(report["llm_dispatch_blocked_reason"] == "openrouter_api_key_missing", "Missing API key should be explicit")
    assert_true(report["llm_api_call_attempted"] is False, "No API key path should not attempt LLM call")
    assert_true(report["llm_response_packet_created"] is False, "No response packet should exist")
    assert_true(report["output_safety_checked"] is False, "Output safety should not be checked")
    assert_true(report["output_safety_blocked"] is False, "Output safety should not be blocked")
    assert_true("output_safety_blocked" not in report["blocked_reasons"], "Output safety block should not appear early")


def test_openrouter_api_key_missing_blocks_dispatch_with_reason() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(HERMES_LLM_API_KEY=""),
        event=private_event(),
        sender=mock_sender,
    )
    assert_true(report["llm_stage_reached"] is True, "Prompt safety pass should reach LLM stage")
    assert_true(report["llm_call_allowed"] is False, "Missing API key should make LLM call not allowed")
    assert_true(report["llm_dispatch_invoked"] is False, "Missing API key should not invoke dispatch")
    assert_true(report["llm_api_call_attempted"] is False, "Missing API key should not attempt call")
    assert_true(report["llm_dispatch_blocked_reason"] == "openrouter_api_key_missing", "Blocked reason should be explicit")
    assert_true("openrouter_api_key_missing" in report["blocked_reasons"], "Blocked reasons should include missing key")


def test_openrouter_api_key_alias_alone_is_accepted() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(OPENROUTER_API_KEY="sk-test-redacted", HERMES_OPENROUTER_API_KEY="", HERMES_LLM_API_KEY=""),
        event=private_event(),
        sender=mock_sender,
        client_runner=mock_client_runner,
    )
    assert_true(report["openrouter_api_key_present"] is True, "OPENROUTER_API_KEY should be accepted")
    assert_true(report["llm_call_allowed"] is True, "Alias should allow LLM dispatch")
    assert_true(report["llm_dispatch_invoked"] is True, "Dispatch should be invoked")
    assert_true(report["llm_api_call_attempted"] is True, "Call should be attempted")
    assert_true(report["llm_api_call_count"] == 1, "Call count should be one")
    assert_true(report["llm_dispatch_blocked_reason"] == "", "Blocked reason should be empty")


def test_hermes_openrouter_api_key_alias_alone_is_accepted() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(OPENROUTER_API_KEY="", HERMES_OPENROUTER_API_KEY="sk-test-redacted", HERMES_LLM_API_KEY=""),
        event=private_event(),
        sender=mock_sender,
        client_runner=mock_client_runner,
    )
    assert_true(report["openrouter_api_key_present"] is True, "HERMES_OPENROUTER_API_KEY should be accepted")
    assert_true(report["llm_call_allowed"] is True, "Alias should allow LLM dispatch")
    assert_true(report["llm_dispatch_invoked"] is True, "Dispatch should be invoked")
    assert_true(report["llm_api_call_attempted"] is True, "Call should be attempted")
    assert_true(report["llm_api_call_count"] == 1, "Call count should be one")


def test_llm_failure_prevents_discord_send() -> None:
    def failing_runner(envelope: dict, config: dict) -> dict:
        result = mock_client_runner(envelope, config)
        result["api_call_succeeded"] = False
        result["api_call_failed"] = True
        result["response_text"] = ""
        return result

    report = build_rag_evidence_private_test_e2e_live_reply_report(
        root=ROOT,
        allow_live_reply=True,
        env=ready_env(),
        event=private_event(),
        client_runner=failing_runner,
        sender=mock_sender,
    )
    assert_true(report["llm_stage_reached"] is True, "LLM stage should be reached")
    assert_true(report["llm_call_allowed"] is True, "LLM call should be allowed")
    assert_true(report["llm_dispatch_invoked"] is True, "LLM dispatch should be invoked")
    assert_true(report["llm_api_call_attempted"] is True, "LLM call should be attempted")
    assert_true(report["llm_api_call_count"] == 1, "LLM call count should still be one")
    assert_true(report["llm_response_packet_created"] is False, "Failed LLM should not create response packet")
    assert_true(report["output_safety_checked"] is False, "No response packet means no output safety")
    assert_true(report["discord_message_sent"] is False, "LLM failure should not send Discord")
    assert_true("llm_api_call_failed" in report["blocked_reasons"], "LLM failure reason should be explicit")


def test_legacy_invalid_ordering_fixture_detected() -> None:
    legacy = {
        "discord_live_runtime_executed": True,
        "discord_event_received": True,
        "accepted_private_test_channel": True,
        "prompt_envelope_created": True,
        "blocked": True,
        "blocked_reasons": ["output_safety_blocked"],
        "llm_api_called": False,
        "llm_response_packet_created": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
    }
    audit = build_legacy_invalid_safety_ordering_report(legacy)
    assert_true(audit["legacy_invalid_safety_ordering_detected"] is True, "Legacy invalid ordering should be detected")
    assert_true(audit["recommended_next_action"] == "retry_phase34l1_after_hotfix", "Retry should be recommended")


def test_legacy_llm_allowed_noop_fixture_detected() -> None:
    legacy = {
        "llm_stage_reached": True,
        "llm_call_allowed": True,
        "llm_dispatch_invoked": False,
        "llm_api_call_attempted": False,
        "llm_api_call_count": 0,
        "blocked_reasons": ["llm_api_call_not_attempted"],
        "discord_message_sent": False,
    }
    audit = build_legacy_llm_allowed_noop_report(legacy)
    assert_true(audit["legacy_llm_allowed_noop_detected"] is True, "Legacy allowed no-op should be detected")
    assert_true(audit["recommended_next_action"] == "retry_phase34l1_after_llm_dispatch_hotfix", "Retry after dispatch hotfix should be recommended")


def test_legacy_openrouter_key_detection_failure_fixture_detected() -> None:
    legacy = {
        "llm_stage_reached": True,
        "llm_call_allowed": False,
        "llm_dispatch_invoked": False,
        "llm_dispatch_blocked_reason": "openrouter_api_key_missing",
        "llm_api_called": False,
        "discord_message_sent": False,
    }
    audit = build_legacy_openrouter_key_detection_failure_report(legacy)
    assert_true(audit["legacy_openrouter_key_detection_failure_detected"] is True, "Legacy key detection failure should be detected")
    assert_true(audit["recommended_next_action"] == "retry_phase34l1_after_openrouter_key_alias_hotfix", "Retry after key alias hotfix should be recommended")


def test_mentions_escaped() -> None:
    def mention_runner(envelope: dict, config: dict) -> dict:
        result = mock_client_runner(envelope, config)
        result["response_text"] = "This is for review only. No external action has been taken. @everyone"
        return result

    report = build_rag_evidence_private_test_e2e_live_reply_report(root=ROOT, allow_live_reply=True, env=ready_env(), event=private_event(), client_runner=mention_runner, sender=mock_sender)
    assert_true(report["discord_message_sent"] is True, "Escaped mention response may send")


def test_sensitive_values_not_logged() -> None:
    report = build_rag_evidence_private_test_e2e_live_reply_report(root=ROOT, allow_live_reply=True, env=ready_env(), event=private_event(), client_runner=mock_client_runner, sender=mock_sender)
    text = json.dumps(report, ensure_ascii=False)
    assert_true(APPROVAL_PHRASE not in text and LLM_APPROVAL_PHRASE not in text, "Approval phrases should not be logged")
    assert_true("sk-" not in text.lower() and "xoxb-" not in text.lower(), "Secret markers should be absent")
    assert_true(report["openrouter_api_key_value_logged"] is False, "OpenRouter API key value should not be logged")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_e2e_live_reply_markdown(build_rag_evidence_private_test_e2e_live_reply_report(root=ROOT))
    assert_true("E2E Live Reply" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_default_blocks_live_e2e,
        test_allow_flag_missing_blocks_live_e2e,
        test_approval_flag_true_but_phrase_missing_blocks,
        test_approval_phrase_correct_but_flag_false_blocks,
        test_llm_approval_missing_blocks_llm_call,
        test_send_messages_false_blocks_send,
        test_private_test_reply_false_blocks_send,
        test_reply_mode_not_private_test_only_blocks,
        test_missing_private_test_channel_id_blocks,
        test_public_team_channel_event_rejected,
        test_private_test_event_accepted_and_sends_once,
        test_server_disconnected_creates_partial_success_artifact,
        test_self_bot_message_skipped,
        test_duplicate_message_and_send_blocked,
        test_output_safety_blocked_prevents_send,
        test_prompt_safety_blocked_prevents_llm_call,
        test_output_safety_not_checked_before_llm_response_exists,
        test_openrouter_api_key_missing_blocks_dispatch_with_reason,
        test_openrouter_api_key_alias_alone_is_accepted,
        test_hermes_openrouter_api_key_alias_alone_is_accepted,
        test_llm_failure_prevents_discord_send,
        test_legacy_invalid_ordering_fixture_detected,
        test_legacy_llm_allowed_noop_fixture_detected,
        test_legacy_openrouter_key_detection_failure_fixture_detected,
        test_mentions_escaped,
        test_sensitive_values_not_logged,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence private-test E2E live reply tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
