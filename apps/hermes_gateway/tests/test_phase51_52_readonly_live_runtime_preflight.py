from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase51_52_readonly_live_runtime_preflight import (
    APPROVAL_PHRASE,
    build_phase51_52_readonly_live_runtime_preflight,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env() -> dict[str, str]:
    return {
        "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED": "true",
        "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_DISCORD_SEND_MESSAGES": "false",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "false",
        "HERMES_DISCORD_REPLY_MODE": "readonly_private_test_only",
        "HERMES_DISCORD_LLM_ENABLED": "false",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_RAG_LLM_REPLY_ENABLED": "false",
        "HERMES_EMBEDDING_ENABLED": "false",
        "HERMES_VECTOR_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
    }


def test_phase51_52_readonly_preflight_closed_state() -> None:
    report = build_phase51_52_readonly_live_runtime_preflight(env={})
    assert_true(report["report_type"] == "phase51_52_readonly_live_runtime_preflight", "Report type")
    assert_true(report["manual_gate_required"] is True, "Manual gate")
    assert_true(report["manual_approval_present"] is False, "No approval")
    assert_true(report["approval_phrase_present"] is False, "No phrase")
    assert_true(report["approval_phrase_exact_match"] is False, "No exact phrase")
    assert_true(report["approval_phrase_value_logged"] is False, "Phrase hidden")
    assert_true(report["ready_for_manual_readonly_runtime_launch"] is False, "Closed")
    assert_true(report["live_runtime_started"] is False, "No runtime")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")


def test_phase51_52_readonly_preflight_open_state() -> None:
    report = build_phase51_52_readonly_live_runtime_preflight(env=ready_env())
    assert_true(report["manual_approval_present"] is True, "Approval present")
    assert_true(report["manual_approval_true"] is True, "Approval true")
    assert_true(report["approval_phrase_present"] is True, "Phrase present")
    assert_true(report["approval_phrase_exact_match"] is True, "Phrase exact")
    assert_true(report["send_messages_disabled"] is True, "Send disabled")
    assert_true(report["private_test_reply_disabled"] is True, "Reply disabled")
    assert_true(report["reply_mode_readonly_private_test_only"] is True, "Reply mode")
    assert_true(report["llm_disabled"] is True, "LLM disabled")
    assert_true(report["rag_disabled"] is True, "RAG disabled")
    assert_true(report["embedding_vector_disabled"] is True, "Embedding/vector disabled")
    assert_true(report["external_execution_disabled"] is True, "External disabled")
    assert_true(report["ready_for_manual_readonly_runtime_launch"] is True, "Open")
    assert_true(report["actual_discord_runtime_executed"] is False, "No actual runtime")


def test_phase51_52_readonly_preflight_no_sensitive_values() -> None:
    text = json.dumps(build_phase51_52_readonly_live_runtime_preflight(env=ready_env()), ensure_ascii=False)
    assert_true(APPROVAL_PHRASE not in text, "Approval phrase value hidden")
    lowered = text.lower()
    assert_true("sk-" not in lowered and "bearer " not in lowered and "token=" not in lowered, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase51_52_readonly_preflight_closed_state,
        test_phase51_52_readonly_preflight_open_state,
        test_phase51_52_readonly_preflight_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase51/52 read-only live runtime preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
