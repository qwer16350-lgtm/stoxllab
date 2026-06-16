from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_DIR.parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40t_private_test_readonly_runtime_command import build_phase40t_private_test_readonly_runtime_command
from private_test_readonly_runtime import APPROVAL_PHRASE
from private_test_readonly_live_runner import FakeReadOnlyLiveAdapter


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
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
    )
    return env


def run_cli(*args: str, env: dict[str, str] | None = None) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "apps/hermes_gateway/cli.py", *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true("logging in using static token" not in completed.stderr.lower(), "No Discord login")
    assert_true(APPROVAL_PHRASE not in completed.stdout, "Approval phrase hidden")
    return json.loads(completed.stdout)


def test_command_builder_default_blocked() -> None:
    report = build_phase40t_private_test_readonly_runtime_command(env={}, report_only=False)
    assert_true(report["blocked"] is True, "Default blocked")
    assert_true(report["started"] is False, "Not started")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_true(report["execute_flag_present"] is False, "Execute absent")


def test_cli_accepts_run_command_default_blocked() -> None:
    env = os.environ.copy()
    for key in (
        "DISCORD_BOT_TOKEN",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID",
        "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED",
        "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE",
    ):
        env.pop(key, None)
    report = run_cli("--run-discord-private-test-readonly", "--json", env=env)
    assert_true(report["blocked"] is True, "Run command blocked")
    assert_true(report["started"] is False, "Run command not started")
    assert_true(report["discord_gateway_connected"] is False, "Run command no gateway")
    assert_true(report["discord_message_sent"] is False, "Run command no send")


def test_cli_accepts_preflight_command() -> None:
    env = os.environ.copy()
    for key in (
        "DISCORD_BOT_TOKEN",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID",
        "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED",
        "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE",
    ):
        env.pop(key, None)
    report = run_cli("--run-discord-private-test-readonly-preflight", "--json", env=env)
    assert_true(report["report_only"] is True, "Preflight report only")
    assert_true(report["blocked"] is True, "Preflight blocked")
    assert_true(report["started"] is False, "Preflight not started")


def test_cli_ready_report_still_no_gateway_or_send() -> None:
    report = run_cli("--run-discord-private-test-readonly", "--json", env=ready_env())
    assert_true(report["blocked"] is False, "Ready report unblocked")
    assert_true(report["manual_runtime_launch_allowed"] is True, "Manual launch allowed")
    assert_true(report["codex_runtime_launch_forbidden"] is True, "Codex forbidden")
    assert_true(report["started"] is False, "Ready still not started")
    assert_true(report["discord_gateway_connected"] is False, "Ready no gateway")
    assert_true(report["discord_api_send_called"] is False, "Ready no API")
    assert_true(report["discord_message_sent"] is False, "Ready no message")
    assert_true(report["message_sent_count"] == 0, "Ready count 0")
    assert_true(report["llm_called"] is False and report["rag_called"] is False, "No LLM/RAG")


def test_command_builder_execute_uses_fake_adapter_only_in_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = FakeReadOnlyLiveAdapter(events=[{"event_id": "e", "message_id": "m", "channel_scope": "private_test", "author_kind": "human"}])
        report = build_phase40t_private_test_readonly_runtime_command(
            env=ready_env(),
            execute_flag_present=True,
            adapter=adapter,
            root=tmp,
        )
        assert_true(adapter.called is True, "Fake adapter called")
        assert_true(report["report_type"] == "phase40t_readonly_runtime_closeout", "Closeout")
        assert_true(report["discord_api_send_called"] is False, "No API")
        assert_true(report["discord_message_sent"] is False, "No message")
        assert_true(report["message_sent_count"] == 0, "Count 0")


def test_cli_login_failure_closeout_report_only() -> None:
    report = run_cli("--phase40t-discord-login-failure-closeout", "--json", env=ready_env())
    assert_true(report["report_type"] == "phase40t_discord_login_failure_closeout", "Login failure closeout")
    assert_true(report["discord_login_failure"] is True, "Login failure")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No send")
    assert_true(report["message_sent_count"] == 0, "Count 0")
    assert_true(report["retry_attempted"] is False, "No retry")


def main() -> int:
    for test in (
        test_command_builder_default_blocked,
        test_cli_accepts_run_command_default_blocked,
        test_cli_accepts_preflight_command,
        test_cli_ready_report_still_no_gateway_or_send,
        test_command_builder_execute_uses_fake_adapter_only_in_test,
        test_cli_login_failure_closeout_report_only,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40T private-test read-only runtime command tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
