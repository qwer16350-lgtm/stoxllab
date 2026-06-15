"""Phase 34J-0 RAG evidence private-test send preflight tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_private_test_send_preflight.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_private_test_send_preflight import (
    APPROVAL_PHRASE,
    build_rag_evidence_private_test_send_preflight,
    render_rag_evidence_private_test_send_preflight_markdown,
)
from rag_evidence_would_send_preview import build_rag_evidence_would_send_preview


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def approved_env(**overrides: str) -> dict[str, str]:
    env = {
        "HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVED": "true",
        "HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
    }
    env.update(overrides)
    return env


def test_preflight_requires_would_send_preview() -> None:
    report = build_rag_evidence_private_test_send_preflight({"would_send_preview_created": False})
    assert_true(report["would_send_preview_available"] is False, "Would-send preview should be required")
    assert_true("would_send_preview_required" in report["blocked_reasons"], "Missing preview should be a blocker")


def test_preflight_default_blocks_actual_send() -> None:
    report = build_rag_evidence_private_test_send_preflight()
    assert_true(report["ready_for_actual_private_test_send"] is False, "Actual send should be false by default")
    assert_true(report["discord_api_send_allowed"] is False, "Discord API send should be disallowed")
    assert_true(report["discord_message_sent"] is False, "Discord message sent should be false")


def test_approval_phrase_value_not_logged() -> None:
    report = build_rag_evidence_private_test_send_preflight(env=approved_env())
    text = json.dumps(report, ensure_ascii=False)
    assert_true(APPROVAL_PHRASE not in text, "Approval phrase value must not be logged")
    assert_true(report["manual_approval"]["approval_phrase_value_logged"] is False, "Phrase value logged flag should be false")


def test_send_messages_false_blocks_send() -> None:
    report = build_rag_evidence_private_test_send_preflight(env=approved_env(HERMES_DISCORD_SEND_MESSAGES="false"))
    assert_true("discord_send_messages_disabled" in report["blocked_reasons"], "send_messages=false should block")
    assert_true(report["ready_for_actual_private_test_send"] is False, "Actual send should remain false")


def test_missing_private_test_channel_blocks_send() -> None:
    report = build_rag_evidence_private_test_send_preflight(env=approved_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=""))
    assert_true(report["private_test_channel_configured"] is False, "Missing channel should be reflected")
    assert_true("private_test_channel_id_missing" in report["blocked_reasons"], "Missing channel should block")


def test_public_team_channel_blocked() -> None:
    report = build_rag_evidence_private_test_send_preflight(env=approved_env())
    assert_true(report["private_test_channel_only"] is True, "Private-test only should be true")
    assert_true(report["public_channel_send_allowed"] is False, "Public send should be false")
    assert_true(report["team_channel_send_allowed"] is False, "Team send should be false")


def test_phase34j1_ready_but_actual_send_false() -> None:
    report = build_rag_evidence_private_test_send_preflight(preview=build_rag_evidence_would_send_preview(), env=approved_env())
    assert_true(report["ready_for_phase34j1_manual_live_send"] is True, "Next manual phase should be ready")
    assert_true(report["ready_for_actual_private_test_send"] is False, "This phase must not enable actual send")


def test_no_llm_embedding_external_or_discord_api() -> None:
    report = build_rag_evidence_private_test_send_preflight(env=approved_env())
    assert_true(report["discord_api_send_called"] is False, "Discord API send called should be false")
    assert_true(report["llm_api_called"] is False, "LLM API called should be false")
    assert_true(report["embedding_api_called"] is False, "Embedding called should be false")
    assert_true(report["external_execution"] is False, "External execution should be false")


def test_sensitive_values_not_logged() -> None:
    report = build_rag_evidence_private_test_send_preflight(env=approved_env())
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "bearer " not in text, "Token markers should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_send_preflight_markdown(build_rag_evidence_private_test_send_preflight())
    assert_true("Private-test Send Preflight" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_preflight_requires_would_send_preview,
        test_preflight_default_blocks_actual_send,
        test_approval_phrase_value_not_logged,
        test_send_messages_false_blocks_send,
        test_missing_private_test_channel_blocks_send,
        test_public_team_channel_blocked,
        test_phase34j1_ready_but_actual_send_false,
        test_no_llm_embedding_external_or_discord_api,
        test_sensitive_values_not_logged,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence private-test send preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
