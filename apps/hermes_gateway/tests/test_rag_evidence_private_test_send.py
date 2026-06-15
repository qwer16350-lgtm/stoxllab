"""Phase 34J-1 one private-test Discord send gate tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_private_test_send.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_private_test_send import build_rag_evidence_private_test_send_report, render_rag_evidence_private_test_send_markdown
from rag_evidence_private_test_send_preflight import APPROVAL_PHRASE
from rag_evidence_would_send_preview import build_rag_evidence_would_send_preview


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env(**overrides: str) -> dict[str, str]:
    env = {
        "HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVED": "true",
        "HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
    }
    env.update(overrides)
    return env


def mock_sender(channel_id: str, content: str) -> dict:
    assert_true(channel_id == "private_test_channel", "Mock sender should receive private channel only")
    assert_true("[PRIVATE TEST SEND / REVIEW ONLY]" in content, "Sent content should include sent-review marker")
    assert_true("No external action has been taken." in content, "Sent content should include safety disclaimer")
    return {"sent": True, "message_id": "redacted_message_id"}


def test_default_blocks_send() -> None:
    report = build_rag_evidence_private_test_send_report()
    assert_true(report["blocked"] is True, "Default should block")
    assert_true(report["discord_message_sent"] is False, "Default should not send")


def test_allow_flag_missing_blocks_send() -> None:
    report = build_rag_evidence_private_test_send_report(env=ready_env(), sender=mock_sender)
    assert_true("allow_rag_evidence_private_test_discord_send_required" in report["blocked_reasons"], "Allow flag should be required")
    assert_true(report["message_sent_count"] == 0, "No send without allow flag")


def test_approval_flag_true_but_phrase_missing_blocks() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVAL_PHRASE=""), sender=mock_sender)
    assert_true("manual_approval_required" in report["blocked_reasons"], "Missing phrase should block")


def test_approval_phrase_correct_but_flag_false_blocks() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVED="false"), sender=mock_sender)
    assert_true("manual_approval_required" in report["blocked_reasons"], "Approval flag false should block")


def test_approved_flag_and_exact_phrase_allow_send_path() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(), sender=mock_sender)
    assert_true(report["ready"] is True, "Ready env and allow flag should allow mock send")
    assert_true(report["discord_api_send_called"] is True, "Mock send should be called")
    assert_true(report["discord_message_sent"] is True, "Mock send should mark sent")
    assert_true(report["message_sent_count"] == 1, "Message sent count should be one")


def test_send_messages_false_blocks_send() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(HERMES_DISCORD_SEND_MESSAGES="false"), sender=mock_sender)
    assert_true("discord_send_messages_disabled" in report["blocked_reasons"], "send_messages false should block")


def test_private_test_reply_false_blocks_send() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(HERMES_DISCORD_PRIVATE_TEST_REPLY="false"), sender=mock_sender)
    assert_true("discord_private_test_reply_disabled" in report["blocked_reasons"], "private test reply false should block")


def test_reply_mode_not_private_test_only_blocks_send() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(HERMES_DISCORD_REPLY_MODE="public"), sender=mock_sender)
    assert_true("reply_mode_not_private_test_only" in report["blocked_reasons"], "Wrong reply mode should block")


def test_missing_private_test_channel_id_blocks_send() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=""), sender=mock_sender)
    assert_true("private_test_channel_id_missing" in report["blocked_reasons"], "Missing channel should block")


def test_would_send_preview_required() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(), preview={"would_send_preview_created": False}, sender=mock_sender)
    assert_true("would_send_preview_required" in report["blocked_reasons"], "Would-send preview should be required")


def test_output_safety_required() -> None:
    preview = build_rag_evidence_would_send_preview()
    preview["output_safety_allowed"] = False
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(), preview=preview, sender=mock_sender)
    assert_true("output_safety_required" in report["blocked_reasons"], "Output safety should be required")


def test_public_team_channel_blocked() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(), sender=mock_sender)
    assert_true(report["public_channel_send_allowed"] is False, "Public channel send should be false")
    assert_true(report["team_channel_send_allowed"] is False, "Team channel send should be false")


def test_duplicate_send_prevention() -> None:
    state = {"sent_message_keys": [], "message_sent_count": 0}
    first = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(), sender=mock_sender, state=state)
    second = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(), sender=mock_sender, state=state)
    assert_true(first["message_sent_count"] == 1, "First send should count once")
    assert_true("duplicate_send_prevented" in second["blocked_reasons"], "Duplicate send should be blocked")
    assert_true(second["message_sent_count"] == 0, "Duplicate should not send")


def test_no_llm_embedding_external() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(), sender=mock_sender)
    assert_true(report["llm_api_called"] is False, "LLM should not be called")
    assert_true(report["embedding_api_called"] is False, "Embedding should not be called")
    assert_true(report["external_execution"] is False, "External execution should be false")


def test_sensitive_values_not_logged() -> None:
    report = build_rag_evidence_private_test_send_report(allow_send=True, env=ready_env(), sender=mock_sender)
    text = json.dumps(report, ensure_ascii=False)
    assert_true(APPROVAL_PHRASE not in text, "Approval phrase should not be logged")
    assert_true("sk-" not in text.lower() and "xoxb-" not in text.lower(), "Token markers should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_send_markdown(build_rag_evidence_private_test_send_report())
    assert_true("Private-test Send" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_default_blocks_send,
        test_allow_flag_missing_blocks_send,
        test_approval_flag_true_but_phrase_missing_blocks,
        test_approval_phrase_correct_but_flag_false_blocks,
        test_approved_flag_and_exact_phrase_allow_send_path,
        test_send_messages_false_blocks_send,
        test_private_test_reply_false_blocks_send,
        test_reply_mode_not_private_test_only_blocks_send,
        test_missing_private_test_channel_id_blocks_send,
        test_would_send_preview_required,
        test_output_safety_required,
        test_public_team_channel_blocked,
        test_duplicate_send_prevention,
        test_no_llm_embedding_external,
        test_sensitive_values_not_logged,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence private-test send tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
