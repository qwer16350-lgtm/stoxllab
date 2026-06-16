from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_DIR.parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40t_discord_login_failure_closeout import (
    assert_phase40t_discord_login_failure_closeout_safe,
    build_phase40t_discord_login_failure_closeout,
    build_phase40t_discord_login_failure_closeout_from_exception,
    build_phase40t_missing_env_before_login_closeout,
    classify_discord_login_failure,
    render_phase40t_discord_login_failure_closeout_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")
APPROVAL_PHRASE = "I_APPROVE_PHASE40J_READONLY_LIVE_RUNTIME"


class FakeLoginFailure(Exception):
    pass


FakeLoginFailure.__name__ = "LoginFailure"


class FakeHTTP401(Exception):
    status = 401


FakeHTTP401.__name__ = "HTTPException"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def env() -> dict[str, str]:
    values = os.environ.copy()
    values.update(
        {
            "DISCORD_BOT_TOKEN": "xoxb-sensitive-token-value",
            "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "123456789012345678",
            "HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE": APPROVAL_PHRASE,
        }
    )
    return values


def ready_snapshot(**overrides: object) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "snapshot_type": "phase40t_readonly_preflight_snapshot",
        "version": "phase40t_readonly_preflight_snapshot",
        "preflight_passed": True,
        "discord_token_present": True,
        "private_test_channel_id_present": True,
        "approval_actualized": True,
        "approval_phrase_present": True,
        "approval_phrase_exact_match": True,
        "send_messages_enabled": False,
        "private_test_reply_enabled": False,
        "reply_mode_readonly_private_test_only": True,
        "llm_disabled": True,
        "rag_disabled": True,
        "embedding_disabled": True,
        "external_execution": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_content_logged": False,
        "secret_values_logged": False,
    }
    snapshot.update(overrides)
    return snapshot


def assert_common_safe(report: dict[str, object]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    assert_phase40t_discord_login_failure_closeout_safe(report)
    assert_true("xoxb-sensitive" not in lowered, "Raw token hidden")
    assert_true(APPROVAL_PHRASE.lower() not in lowered, "Approval phrase hidden")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord IDs hidden")
    assert_true("traceback" in lowered and "traceback (most recent call last)" not in lowered, "No raw traceback")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_true(report["retry_attempted"] is False, "No retry")
    assert_true(report["automatic_retry_allowed"] is False, "No automatic retry")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["capture_file_written"] is False, "No capture file")


def test_login_failure_converted_to_safe_json() -> None:
    report = build_phase40t_discord_login_failure_closeout_from_exception(env(), FakeLoginFailure("Improper token has been passed."))
    assert_true(report["discord_login_failure_type"] == "LoginFailure", "LoginFailure type")
    assert_true(report["discord_login_failure_reason"] == "invalid_or_unauthorized_token", "Invalid token reason")
    assert_true(report["discord_token_present"] is True, "Token presence boolean")
    assert_true(report["discord_token_valid"] is False, "Token validity boolean")
    assert_common_safe(report)


def test_http_401_converted_to_invalid_token_closeout() -> None:
    report = build_phase40t_discord_login_failure_closeout_from_exception(env(), FakeHTTP401("401 Unauthorized"))
    assert_true(report["discord_login_failure_type"] == "HTTPException", "HTTPException type")
    assert_true(report["discord_login_failure_reason"] == "invalid_or_unauthorized_token", "401 reason")
    assert_common_safe(report)


def test_login_failure_preserves_preflight_snapshot_presence() -> None:
    report = build_phase40t_discord_login_failure_closeout_from_exception(
        {},
        FakeLoginFailure("Improper token has been passed."),
        preflight_snapshot=ready_snapshot(),
    )
    assert_true(report["preflight_passed"] is True, "Preflight passed preserved")
    assert_true(report["preflight_snapshot_preserved"] is True, "Snapshot preserved")
    assert_true(report["presence_consistency_verified"] is True, "Presence consistent")
    assert_true(report["discord_token_present"] is True, "Token presence preserved")
    assert_true(report["private_test_channel_id_present"] is True, "Channel presence preserved")
    assert_true(report["approval_phrase_exact_match"] is True, "Approval exact preserved")
    assert_true(report["reply_mode_readonly_private_test_only"] is True, "Reply mode preserved")
    assert_true(report["login_attempted"] is True, "Login attempted")
    assert_true(report["discord_login_failure_reason"] == "invalid_or_unauthorized_token", "Invalid token")
    assert_common_safe(report)


def test_missing_token_or_channel_blocks_before_login() -> None:
    report = build_phase40t_missing_env_before_login_closeout(
        {},
        preflight_snapshot=ready_snapshot(
            preflight_passed=False,
            discord_token_present=False,
            private_test_channel_id_present=False,
        ),
    )
    assert_true(report["preflight_passed"] is False, "Preflight failed")
    assert_true(report["login_attempted"] is False, "Login not attempted")
    assert_true(report["discord_login_failure"] is False, "No Discord login failure")
    assert_true(report["discord_login_failure_reason"] == "missing_token_or_channel", "Missing reason")
    assert_true(report["discord_token_present"] is False, "Token missing")
    assert_true(report["private_test_channel_id_present"] is False, "Channel missing")
    assert_common_safe(report)


def test_timeout_and_manual_abort_classification() -> None:
    timeout_type, timeout_reason = classify_discord_login_failure(TimeoutError())
    abort_type, abort_reason = classify_discord_login_failure(KeyboardInterrupt())
    assert_true(timeout_type == "TimeoutError" and timeout_reason == "login_timeout", "Timeout classified")
    assert_true(abort_type == "KeyboardInterrupt" and abort_reason == "manual_abort", "Manual abort classified")


def test_report_only_cli_no_login_and_no_traceback() -> None:
    completed = subprocess.run(
        [sys.executable, "apps/hermes_gateway/cli.py", "--phase40t-discord-login-failure-closeout", "--json"],
        cwd=REPO_ROOT,
        env=env(),
        text=True,
        capture_output=True,
        check=True,
    )
    text = completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert_true("logging in using static token" not in text.lower(), "No Discord login attempted")
    assert_true("traceback (most recent call last)" not in text.lower(), "No traceback")
    assert_common_safe(report)


def test_markdown_render() -> None:
    markdown = render_phase40t_discord_login_failure_closeout_markdown(build_phase40t_discord_login_failure_closeout(env()))
    assert_true("Discord Login Failure Closeout" in markdown, "Markdown")
    assert_true("Token value logged: false" in markdown, "Token hidden")


def main() -> int:
    for test in (
        test_login_failure_converted_to_safe_json,
        test_http_401_converted_to_invalid_token_closeout,
        test_login_failure_preserves_preflight_snapshot_presence,
        test_missing_token_or_channel_blocks_before_login,
        test_timeout_and_manual_abort_classification,
        test_report_only_cli_no_login_and_no_traceback,
        test_markdown_render,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40T Discord login failure closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
