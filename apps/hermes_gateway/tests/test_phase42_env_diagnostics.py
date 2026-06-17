from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase42_supervised_private_test_session import build_phase42_env_diagnostics


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env() -> dict[str, str]:
    return {
        "HERMES_PHASE42_SUPERVISED_SESSION_APPROVED": "true",
        "HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE": "I_APPROVE_PHASE42_SUPERVISED_PRIVATE_TEST_SESSION",
        "HERMES_PHASE42_MAX_SESSION_MESSAGES": "2",
        "HERMES_PHASE42_MAX_REPLY_COUNT": "2",
        "HERMES_PHASE42_MAX_SEND_COUNT": "2",
        "HERMES_PHASE42_TIMEOUT_SECONDS": "90",
        "HERMES_PHASE42_COOLDOWN_SECONDS": "1",
        "HERMES_PHASE42_DETERMINISTIC_REPLY_ONLY": "true",
        "HERMES_PHASE42_FROZEN_REPLY_ONLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_LLM_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "HERMES_EMBEDDING_ENABLED": "false",
        "HERMES_VECTOR_ENABLED": "false",
    }


def test_phase42_env_diagnostics_process_env_booleans_only() -> None:
    env = ready_env()
    original = {key: os.environ.get(key) for key in env}
    try:
        os.environ.update(env)
        report = build_phase42_env_diagnostics()
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    assert_true(report["manual_approval_present"] is True, "Approval present")
    assert_true(report["manual_approval_true"] is True, "Approval true")
    assert_true(report["approval_phrase_present"] is True, "Phrase present")
    assert_true(report["approval_phrase_exact_match"] is True, "Phrase exact")
    assert_true(report["max_session_messages"] == 2, "Session messages")
    assert_true(report["max_reply_count"] == 2, "Reply count")
    assert_true(report["max_send_count"] == 2, "Send count")
    assert_true(report["timeout_seconds"] == 90, "Timeout")
    assert_true(report["cooldown_seconds"] == 1, "Cooldown")
    assert_true(report["deterministic_reply_only"] is True, "Deterministic")
    assert_true(report["frozen_reply_only"] is True, "Frozen")
    assert_true(report["reply_mode_private_test_only"] is True, "Reply mode")
    assert_true(report["send_messages_enabled"] is True, "Send flag read")
    assert_true(report["private_test_reply_enabled"] is True, "Private reply flag read")
    assert_true(report["llm_disabled"] is True, "LLM disabled")
    assert_true(report["rag_disabled"] is True, "RAG disabled")
    assert_true(report["embedding_disabled"] is True, "Embedding disabled")
    assert_true(report["external_execution_disabled"] is True, "External disabled")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No send")
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("i_approve_" not in text, "No phrase value")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw ID")


def main() -> int:
    test_phase42_env_diagnostics_process_env_booleans_only()
    print("PASS test_phase42_env_diagnostics_process_env_booleans_only")
    print("All Phase 42 env diagnostics tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
