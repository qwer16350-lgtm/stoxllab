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
            "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
            "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
            "HERMES_DISCORD_RAG_ENABLED": "false",
            "HERMES_LLM_RAG_ENABLED": "false",
            "HERMES_RAG_LLM_REPLY_ENABLED": "false",
        }
    )
    return env


def _run_cli(env: dict[str, str]) -> dict[str, object]:
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--actual-private-test-one-shot-send",
            "--json",
            "--allow-actual-private-test-send",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"CLI should succeed: {result.stderr}")
    return json.loads(result.stdout)


def test_phase39b_ready_gate_exact_phrase_required() -> None:
    missing = _run_cli(_ready_env(""))
    wrong = _run_cli(_ready_env("I_APPROVE_STOXL_PRIVATE_TEST_DRAFT_SEND"))
    exact = _run_cli(_ready_env())
    assert_true(missing["approval_phrase_exact_match"] is False, "Missing phrase false")
    assert_true(wrong["approval_phrase_exact_match"] is False, "Wrong phrase false")
    assert_true(exact["approval_phrase_exact_match"] is True, "Exact phrase true")
    assert_true(missing["ready_for_phase39b_manual_one_shot_send"] is False, "Missing phrase blocks")
    assert_true(wrong["ready_for_phase39b_manual_one_shot_send"] is False, "Wrong phrase blocks")
    assert_true(exact["ready_for_phase39b_manual_one_shot_send"] is True, "Exact phrase allows readiness")


def test_phase39b_ready_gate_no_send_or_external_effects() -> None:
    report = _run_cli(_ready_env())
    assert_true(report["version"] == "phase39b_manual_actual_private_test_one_shot_send_ready_gate", "Ready version")
    assert_true(report["phase39b_manual_execution"] is True, "Manual execution readiness")
    assert_true(report["phase39a_implementation_only"] is False, "Not 39A only")
    assert_true(report["manual_approval_actualized"] is True, "Manual approval actualized")
    assert_true(report["blocked"] is False, "Readiness report not blocked")
    assert_true(report["ready_for_phase39b_manual_one_shot_send"] is True, "Ready for manual one-shot")
    assert_true(report["ready_for_discord_send"] is False, "No automatic Discord send readiness")
    for key in (
        "actual_private_test_send_executed",
        "discord_live_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
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
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase39b_ready_gate_no_sensitive_values_logged() -> None:
    report = _run_cli(_ready_env())
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("token-value" not in text, "Token value hidden")
    assert_true("private-channel-present" not in text, "Channel value hidden")
    assert_true(EXPECTED_APPROVAL_PHRASE.lower() not in text, "Approval phrase hidden")
    assert_true("sk-" not in text, "No API key")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw Discord IDs")


def main() -> int:
    tests = [
        test_phase39b_ready_gate_exact_phrase_required,
        test_phase39b_ready_gate_no_send_or_external_effects,
        test_phase39b_ready_gate_no_sensitive_values_logged,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39B manual send ready gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
