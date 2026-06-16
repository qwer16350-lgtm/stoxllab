from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_readonly_runtime import (
    APPROVAL_PHRASE,
    build_private_test_readonly_runtime_preflight,
    render_private_test_readonly_runtime_preflight_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env(**overrides: str) -> dict[str, str]:
    env = {
        "DISCORD_BOT_TOKEN": "present",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "present",
        "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED": "true",
        "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_DISCORD_SEND_MESSAGES": "false",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "false",
        "HERMES_DISCORD_REPLY_MODE": "readonly_private_test_only",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_RAG_LLM_REPLY_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "HERMES_EMBEDDING_API_ENABLED": "false",
        "HERMES_VECTOR_INDEX_ENABLED": "false",
    }
    env.update(overrides)
    return env


def assert_no_live_or_send(report: dict[str, object]) -> None:
    for key in (
        "started",
        "live_runtime_started",
        "discord_gateway_connected",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_called",
        "llm_api_call_attempted",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
    ):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "message count 0")


def test_default_blocked_when_approval_missing() -> None:
    report = build_private_test_readonly_runtime_preflight(env={}, report_only=False)
    assert_true(report["blocked"] is True, "Default blocked")
    assert_true(report["reason"] == "private_test_readonly_preflight_failed:approval_missing_or_mismatch", "Approval reason")
    assert_true(report["approval_phrase_value_logged"] is False, "Phrase hidden")
    assert_no_live_or_send(report)


def test_blocked_when_token_or_channel_missing() -> None:
    missing_token = build_private_test_readonly_runtime_preflight(env=ready_env(DISCORD_BOT_TOKEN=""), report_only=False)
    missing_channel = build_private_test_readonly_runtime_preflight(env=ready_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=""), report_only=False)
    assert_true(missing_token["reason"] == "private_test_readonly_preflight_failed:discord_token_missing", "Token missing")
    assert_true(missing_channel["reason"] == "private_test_readonly_preflight_failed:private_test_channel_id_missing", "Channel missing")
    assert_true(missing_token["discord_token_value_logged"] is False, "Token hidden")
    assert_true(missing_channel["private_test_channel_id_value_logged"] is False, "Channel hidden")


def test_blocked_when_runtime_flags_unsafe() -> None:
    cases = [
        ("HERMES_DISCORD_SEND_MESSAGES", "true", "send_messages_enabled"),
        ("HERMES_DISCORD_PRIVATE_TEST_REPLY", "true", "private_test_reply_enabled"),
        ("HERMES_DISCORD_REPLY_MODE", "private_test_only", "reply_mode_not_readonly_private_test_only"),
        ("HERMES_LLM_DISCORD_SEND_ENABLED", "true", "llm_discord_send_enabled"),
        ("HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED", "true", "llm_private_test_reply_enabled"),
        ("HERMES_DISCORD_RAG_ENABLED", "true", "discord_rag_enabled"),
        ("HERMES_LLM_RAG_ENABLED", "true", "llm_rag_enabled"),
        ("HERMES_RAG_LLM_REPLY_ENABLED", "true", "rag_llm_reply_enabled"),
        ("HERMES_DISCORD_EXTERNAL_EXECUTION", "true", "external_execution_enabled"),
        ("HERMES_EMBEDDING_API_ENABLED", "true", "embedding_or_vector_enabled"),
    ]
    for key, value, reason in cases:
        report = build_private_test_readonly_runtime_preflight(env=ready_env(**{key: value}), report_only=False)
        assert_true(report["blocked"] is True, f"{key} blocked")
        assert_true(report["reason"] == f"private_test_readonly_preflight_failed:{reason}", f"{key} reason")
        assert_no_live_or_send(report)


def test_ready_report_still_does_not_connect_or_send() -> None:
    report = build_private_test_readonly_runtime_preflight(env=ready_env(), report_only=False)
    assert_true(report["blocked"] is False, "Ready unblocked")
    assert_true(report["preflight_passed"] is True, "Preflight passed")
    assert_true(report["manual_runtime_launch_allowed"] is True, "Manual launch allowed")
    assert_true(report["ready_for_manual_readonly_runtime_launch"] is True, "Ready for manual launch")
    assert_true(report["codex_runtime_launch_forbidden"] is True, "Codex forbidden")
    assert_true(report["send_messages_enabled"] is False, "Send false")
    assert_true(report["private_test_reply_enabled"] is False, "Reply false")
    assert_no_live_or_send(report)


def test_no_sensitive_values_or_markdown_leak() -> None:
    report = build_private_test_readonly_runtime_preflight(env=ready_env(), report_only=False)
    text = json.dumps(report, ensure_ascii=False).lower()
    markdown = render_private_test_readonly_runtime_preflight_markdown(report).lower()
    assert_true(APPROVAL_PHRASE.lower() not in text and APPROVAL_PHRASE.lower() not in markdown, "Approval phrase hidden")
    assert_true("token=" not in text and "sk-" not in text and "api_key" not in text, "Secrets hidden")
    assert_true(not LONG_NUMBER_RE.search(text + markdown), "No raw IDs")


def main() -> int:
    for test in (
        test_default_blocked_when_approval_missing,
        test_blocked_when_token_or_channel_missing,
        test_blocked_when_runtime_flags_unsafe,
        test_ready_report_still_does_not_connect_or_send,
        test_no_sensitive_values_or_markdown_leak,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40T private-test read-only runtime preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
