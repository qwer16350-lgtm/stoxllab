"""Phase 33D-3 single live private test runbook checks.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_llm_single_live_test_runbook.py
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNBOOK = ROOT / "docs" / "STOXL_RAG_LLM_SINGLE_LIVE_TEST_RUNBOOK.md"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_VALUE_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*[^\s<][^\s]*|password\s*[:=]\s*[^\s<][^\s]*)")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_runbook() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def test_runbook_exists() -> None:
    assert_true(RUNBOOK.exists(), "Runbook should exist")


def test_manual_only_live_command() -> None:
    text = read_runbook()
    assert_true("--run-discord-private-test-rag-llm-reply" in text, "Live command should be documented")
    assert_true("Manual-only command" in text, "Live command should be manual-only")
    assert_true("Codex/agent must not execute this command automatically" in text, "Codex should not auto-run live command")
    assert_true("user runs it directly in powershell" in text.lower(), "User-run PowerShell should be explicit")


def test_before_run_checks_present() -> None:
    text = read_runbook()
    for command in (
        "--rag-llm-live-preflight-closeout --json",
        "--rag-llm-private-test-runtime-report --json",
        "--rag-llm-private-test-replay-report --json",
        "scripts\\validate_stoxl_configs.py",
    ):
        assert_true(command in text, f"Missing before-run command: {command}")
    for expected in (
        "ready_for_single_live_private_test=true",
        "runtime_executed=false",
        "actual_discord_send=false",
        "actual_llm_api_call=false",
        "embedding_api_called=false",
        "external_execution=false",
    ):
        assert_true(expected in text, f"Missing before-run expected value: {expected}")


def test_required_env_gates_present() -> None:
    text = read_runbook()
    for gate in (
        'HERMES_DISCORD_SEND_MESSAGES="true"',
        'HERMES_DISCORD_PRIVATE_TEST_REPLY="true"',
        'HERMES_DISCORD_REPLY_MODE="private_test_only"',
        'HERMES_RAG_MODE="local_readonly"',
        'HERMES_RAG_LLM_REPLY_ENABLED="true"',
        'HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="true"',
        'HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE="I_APPROVE_ONE_PRIVATE_TEST_RAG_LLM_REPLY"',
        'HERMES_LLM_API_CALL_ENABLED="true"',
        'HERMES_LLM_PROVIDER="openrouter"',
        'HERMES_LLM_MODEL="openai/gpt-5.4-mini"',
        'HERMES_LLM_BASE_URL="https://openrouter.ai/api/v1"',
        'HERMES_DISCORD_EXTERNAL_EXECUTION="false"',
        'HERMES_LLM_EXTERNAL_EXECUTION="false"',
    ):
        assert_true(gate in text, f"Missing env gate: {gate}")
    assert_true("<PRIVATE_TEST_CHANNEL_ID>" in text, "Private test channel ID should be placeholder only")
    assert_true("<OPENROUTER_KEY_PLACEHOLDER>" in text, "OpenRouter key should be placeholder only")
    assert_true("Do not persist it in `.env`" in text, "Approval phrase should not be persisted")


def test_expected_logs_exactly_one_sent() -> None:
    text = read_runbook()
    assert_true("[PRIVATE_TEST_RAG_LLM_READY]" in text, "Ready log should be documented")
    assert_true("[READONLY_EVENT] accepted_private_test_channel" in text, "Accepted private channel log should be documented")
    assert_true("[PRIVATE_TEST_RAG_LLM_REPLY_SENT] message_sent=true channel=hermes-private-test" in text, "Sent log should be documented")
    assert_true("appears exactly once" in text, "Exactly one sent log should be required")
    assert_true("`llm_call_allowed` must not appear again after `ignored_self_message`" in text, "Self-message LLM loop should be forbidden")


def test_abort_and_rollback_present() -> None:
    text = read_runbook()
    for rollback in (
        'HERMES_DISCORD_SEND_MESSAGES="false"',
        'HERMES_DISCORD_PRIVATE_TEST_REPLY="false"',
        'HERMES_LLM_DISCORD_SEND_ENABLED="false"',
        'HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"',
        'HERMES_RAG_LLM_REPLY_ENABLED="false"',
        'HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="false"',
        'HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE=""',
    ):
        assert_true(rollback in text, f"Missing rollback gate: {rollback}")
    for abort in (
        "public or team channel event is accepted",
        "`source=operations` is accepted",
        "self message triggers retrieval",
        "self message triggers LLM call",
        "more than one reply is sent",
        "output safety blocks but send is attempted",
        "rate limit or circuit breaker opens",
        "unknown exception loop appears",
    ):
        assert_true(abort in text, f"Missing abort condition: {abort}")


def test_no_secret_values_or_raw_ids() -> None:
    text = read_runbook()
    assert_true(not SECRET_VALUE_RE.search(text), "Runbook should not contain secret-like values")
    assert_true(not LONG_ID_RE.search(text), "Runbook should not contain raw Discord-like IDs")


def test_no_live_execution_claims() -> None:
    text = read_runbook()
    for expected in (
        "Codex/agent live runtime execution in Phase 33D-3: false",
        "Discord message sent by Codex/agent in Phase 33D-3: false",
        "OpenRouter/LLM API call by Codex/agent in Phase 33D-3: false",
        "embedding API call in Phase 33D-3: false",
        "external execution in Phase 33D-3: false",
        "single live test execution: user-run PowerShell only",
        "single live approval phrase value logged by runtime reports: false",
    ):
        assert_true(expected in text, f"Missing no-live safety statement: {expected}")


def main() -> int:
    tests = [
        test_runbook_exists,
        test_manual_only_live_command,
        test_before_run_checks_present,
        test_required_env_gates_present,
        test_expected_logs_exactly_one_sent,
        test_abort_and_rollback_present,
        test_no_secret_values_or_raw_ids,
        test_no_live_execution_claims,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM single live private test runbook checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
