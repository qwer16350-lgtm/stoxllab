from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "apps" / "hermes_gateway" / "cli.py"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _safe_env() -> dict[str, str]:
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


def _run_allow_flag_cli() -> dict[str, object]:
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--actual-private-test-one-shot-send",
            "--json",
            "--allow-actual-private-test-send",
        ],
        cwd=ROOT,
        env=_safe_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"CLI should accept allow flag: {result.stderr}")
    assert_true("unrecognized arguments" not in result.stderr.lower(), "Allow flag recognized")
    return json.loads(result.stdout)


def test_cli_recognizes_allow_actual_private_test_send() -> None:
    report = _run_allow_flag_cli()
    assert_true(report["allow_flag_present"] is True, "Allow flag reflected")
    assert_true(report["blocked"] is True, "Allow flag alone remains blocked")


def test_cli_allow_flag_never_sends() -> None:
    report = _run_allow_flag_cli()
    for key in (
        "actual_private_test_send_executed",
        "actual_send_executed",
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
    assert_true(report["message_sent_count"] == 0, "No messages sent")
    assert_true(report["ready_for_discord_send"] is False, "Not ready for Discord send")


def main() -> int:
    tests = [
        test_cli_recognizes_allow_actual_private_test_send,
        test_cli_allow_flag_never_sends,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39A allow flag CLI tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
