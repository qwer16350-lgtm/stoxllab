from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
APP_DIR = ROOT / "apps" / "hermes_gateway"
CLI = APP_DIR / "cli.py"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_private_test_send_safety_gate import EXPECTED_APPROVAL_PHRASE


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "DISCORD_BOT_TOKEN",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID",
        "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED",
        "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE",
        "HERMES_DISCORD_SEND_MESSAGES",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY",
        "HERMES_DISCORD_REPLY_MODE",
        "HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION",
        "HERMES_LLM_DISCORD_SEND_ENABLED",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED",
        "HERMES_DISCORD_RAG_ENABLED",
        "HERMES_LLM_RAG_ENABLED",
        "HERMES_RAG_LLM_REPLY_ENABLED",
    ):
        env.pop(key, None)
    return env


def _ready_env(phrase: str = EXPECTED_APPROVAL_PHRASE) -> dict[str, str]:
    env = _base_env()
    env.update(
        {
            "DISCORD_BOT_TOKEN": "token-value",
            "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private-channel-present",
            "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED": "true",
            "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE": phrase,
            "HERMES_DISCORD_SEND_MESSAGES": "true",
            "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
            "HERMES_DISCORD_REPLY_MODE": "private_test_only",
            "HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION": "false",
            "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
            "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
            "HERMES_DISCORD_RAG_ENABLED": "false",
            "HERMES_LLM_RAG_ENABLED": "false",
            "HERMES_RAG_LLM_REPLY_ENABLED": "false",
        }
    )
    return env


def _run_cli(env: dict[str, str], *, allow: bool = True, execute: bool = True) -> dict[str, object]:
    command = [sys.executable, str(CLI), "--actual-private-test-one-shot-send", "--json"]
    if allow:
        command.append("--allow-actual-private-test-send")
    if execute:
        command.append("--execute-actual-private-test-send")
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"CLI should succeed: {result.stderr}")
    return json.loads(result.stdout)


def test_execute_flag_without_allow_blocks() -> None:
    report = _run_cli(_ready_env(), allow=False, execute=True)
    assert_true(report["execute_flag_present"] is True, "Execute flag reflected")
    assert_true(report["allow_flag_present"] is False, "Allow missing")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["execution_gate_conditions_met"] is False, "Execution gate false")
    assert_true(report["ready_for_actual_private_test_send"] is False, "No actual send readiness")


def test_execute_flag_with_missing_or_wrong_approval_blocks() -> None:
    missing = _run_cli(_ready_env(""), allow=True, execute=True)
    wrong = _run_cli(_ready_env("I_APPROVE_STOXL_PRIVATE_TEST_DRAFT_SEND"), allow=True, execute=True)
    assert_true(missing["approval_phrase_exact_match"] is False, "Missing phrase false")
    assert_true(wrong["approval_phrase_exact_match"] is False, "Wrong phrase false")
    assert_true(missing["execution_gate_conditions_met"] is False, "Missing blocks execution gate")
    assert_true(wrong["execution_gate_conditions_met"] is False, "Wrong blocks execution gate")
    assert_true(missing["discord_api_send_called"] is False, "Missing no API send")
    assert_true(wrong["discord_message_sent"] is False, "Wrong no message sent")


def test_execute_flag_with_exact_phrase_reaches_mock_gate_no_send() -> None:
    report = _run_cli(_ready_env(), allow=True, execute=True)
    assert_true(report["version"] == "phase39b_actual_private_test_send_execution_gate_mock_no_send", "Execution gate version")
    assert_true(report["mode"] == "phase39b_actual_send_execution", "Execution mode")
    assert_true(report["execute_flag_present"] is True, "Execute flag")
    assert_true(report["real_discord_send_execution_env_enabled"] is False, "Real env false")
    assert_true(report["execution_gate_conditions_met"] is True, "Execution gate met")
    assert_true(report["actual_execution_adapter"] == "mock", "Mock adapter")
    assert_true(report["ready_for_actual_private_test_send"] is True, "Ready for actual manual send")
    assert_true(report["ready_for_discord_send"] is False, "No direct Discord send ready")
    assert_true(report["actual_private_test_send_executed"] is False, "No actual send")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No message sent")
    assert_true(report["message_sent_count"] == 0, "Message count 0")


def test_execute_gate_no_llm_rag_external_or_sensitive_values() -> None:
    report = _run_cli(_ready_env(), allow=True, execute=True)
    for key in (
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
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
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("token-value" not in text, "Token value hidden")
    assert_true("private-channel-present" not in text, "Channel value hidden")
    assert_true(EXPECTED_APPROVAL_PHRASE.lower() not in text, "Approval phrase hidden")
    assert_true("sk-" not in text, "No API key")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_execute_flag_without_allow_blocks,
        test_execute_flag_with_missing_or_wrong_approval_blocks,
        test_execute_flag_with_exact_phrase_reaches_mock_gate_no_send,
        test_execute_gate_no_llm_rag_external_or_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39B actual send execution gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
