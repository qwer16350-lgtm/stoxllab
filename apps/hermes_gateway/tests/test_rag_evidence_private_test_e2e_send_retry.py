"""Phase 34L-1E no-LLM E2E send retry tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_private_test_e2e_send_retry.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import rag_evidence_private_test_e2e_send_retry as retry_module
from rag_evidence_private_test_e2e_send_retry import (
    APPROVAL_PHRASE,
    build_rag_evidence_private_test_e2e_send_retry_report,
    build_sample_partial_success_artifact,
    render_rag_evidence_private_test_e2e_send_retry_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env(**overrides: str) -> dict[str, str]:
    env = {
        "HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVED": "true",
        "HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
        "DISCORD_BOT_TOKEN": "",
    }
    env.update(overrides)
    return env


def mock_sender(channel_id: str, content: str) -> dict:
    assert_true(channel_id == "private_test_channel", "Only private test channel should be used")
    assert_true("[PRIVATE TEST E2E RETRY / REVIEW ONLY]" in content, "Retry marker should be present")
    assert_true("No LLM recall is allowed" in content, "Retry should state no LLM recall")
    return {"sent": True, "message_id": "redacted_message_id"}


def test_default_is_blocked_without_llm_or_discord_send() -> None:
    report = build_rag_evidence_private_test_e2e_send_retry_report()
    assert_true(report["partial_success_available"] is True, "Sample partial success should be available")
    assert_true(report["blocked"] is True, "Default should be blocked")
    assert_true("allow_rag_evidence_private_test_e2e_send_retry_required" in report["blocked_reasons"], "Allow flag should be required")
    assert_true(report["llm_recall_allowed"] is False, "LLM recall should never be allowed")
    assert_true(report["llm_api_called"] is False, "Retry must not call LLM")
    assert_true(report["llm_api_call_count"] == 0, "Retry LLM call count should be zero")
    assert_true(report["discord_api_send_called"] is False, "Default should not send")
    assert_true(report["discord_message_sent"] is False, "Default should not mark sent")
    assert_true(report["actual_send_retry_sender_available"] is False, "Default should not expose actual sender")


def test_manual_approval_required() -> None:
    report = build_rag_evidence_private_test_e2e_send_retry_report(
        allow_send_retry=True,
        env=ready_env(HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVAL_PHRASE=""),
        sender=mock_sender,
    )
    assert_true(report["blocked"] is True, "Missing approval should block")
    assert_true("manual_approval_required" in report["blocked_reasons"], "Manual approval reason should be present")
    assert_true(report["discord_message_sent"] is False, "Blocked retry should not send")


def test_approval_phrase_mismatch_blocks() -> None:
    report = build_rag_evidence_private_test_e2e_send_retry_report(
        allow_send_retry=True,
        env=ready_env(HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVAL_PHRASE="wrong"),
        sender=mock_sender,
    )
    assert_true("manual_approval_required" in report["blocked_reasons"], "Phrase mismatch should block")
    assert_true(report["discord_message_sent"] is False, "Phrase mismatch should not send")


def test_token_missing_blocks_actual_retry_without_sender() -> None:
    report = build_rag_evidence_private_test_e2e_send_retry_report(
        allow_send_retry=True,
        env=ready_env(DISCORD_BOT_TOKEN=""),
    )
    assert_true("discord_token_missing" in report["blocked_reasons"], "Actual retry should require token")
    assert_true("actual_send_retry_sender_not_provided" not in report["blocked_reasons"], "Auto sender path should avoid sender-not-provided")
    assert_true(report["actual_send_retry_sender_not_provided"] is False, "Sender-not-provided flag should stay false")
    assert_true(report["discord_message_sent"] is False, "Missing token should not send")


def test_env_gate_blocks() -> None:
    cases = [
        ("HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "", "private_test_channel_id_missing"),
        ("HERMES_DISCORD_SEND_MESSAGES", "false", "discord_send_messages_disabled"),
        ("HERMES_DISCORD_PRIVATE_TEST_REPLY", "false", "discord_private_test_reply_disabled"),
        ("HERMES_DISCORD_REPLY_MODE", "public", "reply_mode_not_private_test_only"),
    ]
    for key, value, reason in cases:
        report = build_rag_evidence_private_test_e2e_send_retry_report(
            allow_send_retry=True,
            env=ready_env(**{key: value}),
            sender=mock_sender,
        )
        assert_true(reason in report["blocked_reasons"], f"{reason} should block")
        assert_true(report["discord_message_sent"] is False, f"{reason} should not send")


def test_public_team_channel_stays_blocked_by_policy() -> None:
    report = build_rag_evidence_private_test_e2e_send_retry_report(allow_send_retry=True, env=ready_env(), sender=mock_sender)
    assert_true(report["private_test_channel_only"] is True, "Private test only")
    assert_true(report["public_channel_send_allowed"] is False, "Public channel send stays blocked")
    assert_true(report["team_channel_send_allowed"] is False, "Team channel send stays blocked")


def test_bad_partial_success_blocks_retry() -> None:
    partial = build_sample_partial_success_artifact()
    partial["output_safety_allowed"] = False
    report = build_rag_evidence_private_test_e2e_send_retry_report(
        allow_send_retry=True,
        env=ready_env(),
        partial_success=partial,
        sender=mock_sender,
    )
    assert_true("partial_success_not_ready_for_retry" in report["blocked_reasons"], "Bad partial should block")
    assert_true(report["discord_message_sent"] is False, "Bad partial should not send")


def test_partial_success_missing_blocks_retry() -> None:
    report = build_rag_evidence_private_test_e2e_send_retry_report(
        allow_send_retry=True,
        env=ready_env(),
        partial_success={},
        sender=mock_sender,
    )
    assert_true("partial_success_artifact_required" in report["blocked_reasons"], "Missing partial success should block")
    assert_true(report["discord_message_sent"] is False, "Missing partial should not send")


def test_mock_success_sends_once_without_llm() -> None:
    report = build_rag_evidence_private_test_e2e_send_retry_report(
        allow_send_retry=True,
        env=ready_env(),
        partial_success=build_sample_partial_success_artifact(),
        sender=mock_sender,
    )
    assert_true(report["blocked"] is False, "Approved mock retry should pass")
    assert_true(report["ready_for_actual_send_retry"] is True, "Ready for actual send retry should be true in mock")
    assert_true(report["actual_send_retry_sender_available"] is True, "Mock sender should count as available")
    assert_true(report["actual_send_retry_sender_not_provided"] is False, "Sender-not-provided should stay false")
    assert_true(report["llm_recall_allowed"] is False, "LLM recall should be false")
    assert_true(report["llm_api_called"] is False, "No LLM call in retry")
    assert_true(report["llm_api_call_count"] == 0, "No LLM call count in retry")
    assert_true(report["safety_assertions"]["llm_call_count"] == 0, "Safety LLM count should be zero")
    assert_true(report["discord_api_send_called"] is True, "Mock sender should be called")
    assert_true(report["discord_message_sent"] is True, "Mock report should mark sent")
    assert_true(report["message_sent_count"] == 1, "Mock retry should send exactly once")
    assert_true(report["sent_channel_scope"] == "private_test_only", "Sent scope should be private-test only")
    assert_true(report["ready_for_phase34l2_e2e_live_reply_closeout"] is True, "Phase 34L-2 should be ready after mock send")


def test_auto_built_sender_available_when_all_gates_pass(monkeypatch: object | None = None) -> None:
    original = retry_module._actual_discord_sender_with_token

    def fake_sender(token: str, channel_id: str, content: str) -> dict:
        assert_true(token == "token_redacted", "Token should be passed internally only")
        assert_true(channel_id == "private_test_channel", "Private test channel only")
        assert_true("No LLM recall is allowed" in content, "Retry should not recall LLM")
        return {"sent": True, "message_id": "redacted_message_id"}

    retry_module._actual_discord_sender_with_token = fake_sender
    try:
        report = build_rag_evidence_private_test_e2e_send_retry_report(
            allow_send_retry=True,
            env=ready_env(DISCORD_BOT_TOKEN="token_redacted"),
            partial_success=build_sample_partial_success_artifact(),
        )
    finally:
        retry_module._actual_discord_sender_with_token = original
    assert_true(report["actual_send_retry_sender_available"] is True, "Auto-built sender should be available")
    assert_true(report["actual_send_retry_sender_not_provided"] is False, "Auto-built sender should avoid not-provided")
    assert_true("actual_send_retry_sender_not_provided" not in report["blocked_reasons"], "Not-provided reason should not appear")
    assert_true(report["discord_message_sent"] is True, "Patched auto sender should send exactly once")
    assert_true(report["llm_api_called"] is False, "Auto sender retry should not call LLM")


def test_sensitive_values_not_logged() -> None:
    report = build_rag_evidence_private_test_e2e_send_retry_report(
        allow_send_retry=True,
        env=ready_env(),
        sender=mock_sender,
    )
    text = json.dumps(report, ensure_ascii=False)
    assert_true(APPROVAL_PHRASE not in text, "Approval phrase value should not be logged")
    assert_true("sk-" not in text.lower() and "xoxb-" not in text.lower(), "Secret markers should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_e2e_send_retry_markdown(build_rag_evidence_private_test_e2e_send_retry_report())
    assert_true("E2E Send Retry" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_default_is_blocked_without_llm_or_discord_send,
        test_manual_approval_required,
        test_approval_phrase_mismatch_blocks,
        test_token_missing_blocks_actual_retry_without_sender,
        test_env_gate_blocks,
        test_public_team_channel_stays_blocked_by_policy,
        test_bad_partial_success_blocks_retry,
        test_partial_success_missing_blocks_retry,
        test_mock_success_sends_once_without_llm,
        test_auto_built_sender_available_when_all_gates_pass,
        test_sensitive_values_not_logged,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence private-test E2E send retry tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
