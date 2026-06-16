from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40t_readonly_live_execution_gate import build_phase40t_readonly_live_execution_gate
from private_test_readonly_runtime import APPROVAL_PHRASE


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


def test_execute_flag_required() -> None:
    report = build_phase40t_readonly_live_execution_gate(env=ready_env(), execute_flag_present=False)
    assert_true(report["blocked"] is True, "No execute flag blocks")
    assert_true(report["reason"] == "readonly_live_execution_preflight_failed:execute_flag_missing", "Reason")
    assert_true(report["started"] is False, "Not started")


def test_execute_blocked_when_approval_missing() -> None:
    report = build_phase40t_readonly_live_execution_gate(env={}, execute_flag_present=True)
    assert_true(report["blocked"] is True, "Approval missing blocks")
    assert_true("approval_missing_or_mismatch" in report["reason"], "Approval reason")


def test_execute_blocks_unsafe_flags() -> None:
    cases = [
        ("HERMES_DISCORD_SEND_MESSAGES", "true", "send_messages_enabled"),
        ("HERMES_DISCORD_PRIVATE_TEST_REPLY", "true", "private_test_reply_enabled"),
        ("HERMES_DISCORD_REPLY_MODE", "private_test_only", "reply_mode_not_readonly_private_test_only"),
        ("HERMES_LLM_DISCORD_SEND_ENABLED", "true", "llm_discord_send_enabled"),
        ("HERMES_DISCORD_RAG_ENABLED", "true", "discord_rag_enabled"),
        ("HERMES_EMBEDDING_API_ENABLED", "true", "embedding_or_vector_enabled"),
    ]
    for key, value, reason in cases:
        report = build_phase40t_readonly_live_execution_gate(env=ready_env(**{key: value}), execute_flag_present=True)
        assert_true(report["blocked"] is True, f"{key} blocks")
        assert_true(reason in report["reason"], f"{key} reason")


def test_execute_blocks_invalid_runtime_options() -> None:
    timeout = build_phase40t_readonly_live_execution_gate(env=ready_env(), execute_flag_present=True, timeout_seconds=0)
    events = build_phase40t_readonly_live_execution_gate(env=ready_env(), execute_flag_present=True, max_events=101)
    root = build_phase40t_readonly_live_execution_gate(env=ready_env(), execute_flag_present=True, capture_root="exports")
    assert_true("invalid_timeout_seconds" in timeout["reason"], "Timeout invalid")
    assert_true("invalid_max_events" in events["reason"], "Max events invalid")
    assert_true("capture_root_not_local_ignored_path" in root["reason"], "Capture root invalid")


def test_execute_ready_gate_still_no_runtime_or_send() -> None:
    report = build_phase40t_readonly_live_execution_gate(env=ready_env(), execute_flag_present=True)
    assert_true(report["blocked"] is False, "Gate ready")
    assert_true(report["preflight_passed"] is True, "Preflight passed")
    for key in ("started", "live_runtime_started", "discord_gateway_connected", "discord_api_send_called", "discord_message_sent", "llm_called", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "Count 0")
    text = json.dumps(report, ensure_ascii=False)
    assert_true(APPROVAL_PHRASE not in text and not LONG_NUMBER_RE.search(text), "No secrets or IDs")


def main() -> int:
    for test in (
        test_execute_flag_required,
        test_execute_blocked_when_approval_missing,
        test_execute_blocks_unsafe_flags,
        test_execute_blocks_invalid_runtime_options,
        test_execute_ready_gate_still_no_runtime_or_send,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40T execution gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
