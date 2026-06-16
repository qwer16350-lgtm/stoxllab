from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_readonly_live_runner import FakeReadOnlyLiveAdapter, run_phase40t_readonly_live_runtime
from private_test_readonly_runtime import APPROVAL_PHRASE


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class LoginFailureLike(Exception):
    pass


LoginFailureLike.__name__ = "LoginFailure"


class RaisingAdapter:
    called = False

    def run(self, *, timeout_seconds: int, max_events: int) -> dict[str, object]:
        self.called = True
        raise LoginFailureLike("Improper token has been passed. 401 Unauthorized")


def ready_env() -> dict[str, str]:
    return {
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


def test_runner_blocks_without_execute_flag() -> None:
    adapter = FakeReadOnlyLiveAdapter()
    report = run_phase40t_readonly_live_runtime(env=ready_env(), execute_flag_present=False, adapter=adapter)
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(adapter.called is False, "Adapter not called")
    assert_true(report["started"] is False, "Not started")


def test_fake_adapter_ready_closeout_no_send() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = FakeReadOnlyLiveAdapter(
            events=[
                {
                    "event_id": "123456789012345678",
                    "message_id": "234567890123456789",
                    "channel_scope": "private_test",
                    "author_kind": "human",
                    "decision": "capture_only",
                }
            ]
        )
        report = run_phase40t_readonly_live_runtime(
            env=ready_env(),
            execute_flag_present=True,
            timeout_seconds=1,
            max_events=10,
            root=tmp,
            adapter=adapter,
        )
        text = json.dumps(report, ensure_ascii=False)
        assert_true(adapter.called is True, "Adapter called")
        assert_true(report["report_type"] == "phase40t_readonly_runtime_closeout", "Closeout")
        assert_true(report["started"] is True, "Started simulated")
        assert_true(report["discord_gateway_connected"] is True, "Gateway simulated")
        assert_true(report["capture_file_written"] is True, "Capture written")
        assert_true(report["captured_event_count"] == 1, "One event")
        assert_true(report["discord_api_send_called"] is False, "No API send")
        assert_true(report["discord_message_sent"] is False, "No message")
        assert_true(report["message_sent_count"] == 0, "No count")
        assert_true(report["llm_called"] is False and report["rag_called"] is False, "No LLM/RAG")
        assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs in report")


def test_fake_adapter_max_events() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = FakeReadOnlyLiveAdapter(
            events=[
                {"event_id": "a", "message_id": "a", "channel_scope": "private_test", "author_kind": "human"},
                {"event_id": "b", "message_id": "b", "channel_scope": "private_test", "author_kind": "human"},
            ],
            exit_reason="max_events",
        )
        report = run_phase40t_readonly_live_runtime(env=ready_env(), execute_flag_present=True, max_events=1, root=tmp, adapter=adapter)
        assert_true(report["captured_event_count"] == 1, "Max events respected")
        assert_true(report["exit_reason"] == "max_events", "Exit reason")


def test_adapter_login_failure_returns_safe_closeout() -> None:
    adapter = RaisingAdapter()
    report = run_phase40t_readonly_live_runtime(env=ready_env(), execute_flag_present=True, adapter=adapter)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true(adapter.called is True, "Adapter called")
    assert_true(report["report_type"] == "phase40t_discord_login_failure_closeout", "Login failure closeout")
    assert_true(report["discord_login_failure"] is True, "Login failure")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")
    assert_true(report["retry_attempted"] is False, "No retry")
    assert_true("traceback (most recent call last)" not in text, "No traceback")


def main() -> int:
    for test in (
        test_runner_blocks_without_execute_flag,
        test_fake_adapter_ready_closeout_no_send,
        test_fake_adapter_max_events,
        test_adapter_login_failure_returns_safe_closeout,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40T read-only live runner tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
