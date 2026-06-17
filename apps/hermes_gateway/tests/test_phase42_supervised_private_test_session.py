from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase42_supervised_private_test_session import (
    FakePhase42SessionAdapter,
    Phase42SessionEvent,
    Phase42SessionSendResult,
    build_phase42_supervised_private_test_session,
    build_phase42_supervised_private_test_session_preflight,
)


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


def test_phase42_default_blocked_no_runtime() -> None:
    report = build_phase42_supervised_private_test_session_preflight()
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["manual_gate_required"] is True, "Manual gate required")
    assert_true(report["manual_gate_open"] is False, "Manual gate closed")
    assert_true(report["actual_supervised_session_executed"] is False, "No supervised session")
    assert_true("manual_approval_missing" in report["blocked_reasons"], "Approval required")
    assert_true("approval_phrase_mismatch" in report["blocked_reasons"], "Phrase required")
    assert_true("max_reply_count_missing" in report["blocked_reasons"], "Max count required")
    assert_true("max_session_messages_missing" in report["blocked_reasons"], "Max session messages required")
    assert_true("max_send_count_missing" in report["blocked_reasons"], "Max send count required")
    assert_true("timeout_missing" in report["blocked_reasons"], "Timeout required")
    assert_true("cooldown_missing" in report["blocked_reasons"], "Cooldown required")
    assert_true("send_messages_disabled" in report["blocked_reasons"], "Send flag required")
    assert_true("private_test_reply_disabled" in report["blocked_reasons"], "Private reply flag required")
    assert_true(report["private_test_channel_only"] is True, "Private-test only")
    assert_true(report["public_team_blocked"] is True, "Public/team blocked")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["ready_for_phase42_manual_supervised_session"] is False, "No manual readiness")
    assert_true(report["ready_for_phase41b_repeat_send"] is False, "No 41B repeat")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["actual_runtime_executed"] is False, "No runtime")


def test_phase42_gate_values_do_not_open_runtime() -> None:
    report = build_phase42_supervised_private_test_session_preflight(ready_env())
    assert_true(report["gate_checks_ready"] is True, "Gate checks ready")
    assert_true(report["blocked"] is False, "Gate not blocked")
    assert_true(report["manual_gate_open"] is True, "Manual gate open")
    assert_true(report["ready_for_phase42_manual_supervised_session"] is True, "Ready for manual supervised session")
    assert_true(report["actual_supervised_session_executed"] is False, "No runtime")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")


def test_phase42_runtime_default_blocked_does_not_call_adapter() -> None:
    adapter = FakePhase42SessionAdapter(events=[Phase42SessionEvent()])
    report = build_phase42_supervised_private_test_session(ready_env(), session_adapter=adapter)
    assert_true(report["report_type"] == "phase42_supervised_private_test_session", "Runtime report")
    assert_true(report["blocked"] is True, "Blocked without allow")
    assert_true("allow_actual_phase42_supervised_session_flag_missing" in report["blocked_reasons"], "Allow flag missing")
    assert_true(report["actual_runtime_executed"] is False, "No runtime")
    assert_true(report["actual_supervised_session_executed"] is False, "No supervised execution")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_true(adapter.collect_called is False, "No collect")
    assert_true(adapter.send_called is False, "No send")


def test_phase42_fake_adapter_supervised_session_sends_once() -> None:
    adapter = FakePhase42SessionAdapter(events=[Phase42SessionEvent(), Phase42SessionEvent()])
    report = build_phase42_supervised_private_test_session(
        ready_env(),
        allow_actual_phase42_supervised_session=True,
        session_adapter=adapter,
    )
    assert_true(report["actual_runtime_executed"] is True, "Fake runtime")
    assert_true(report["runtime_adapter_type"] == "fake", "Fake adapter")
    assert_true(report["actual_supervised_session_executed"] is True, "Supervised session executed")
    assert_true(report["sent_scope"] == "private_test_only", "Private-test scope")
    assert_true(report["discord_api_send_called"] is True, "Fake API")
    assert_true(report["discord_message_sent"] is True, "Fake message")
    assert_true(report["message_sent_count"] == 1, "Exactly one fake message")
    assert_true(report["public_channel_reply_allowed"] is False, "No public")
    assert_true(report["team_channel_reply_allowed"] is False, "No team")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["llm_api_called"] is False, "No LLM")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(adapter.collect_called is True, "Collect called")
    assert_true(adapter.send_called is True, "Send called")


def test_phase42_ignored_events_do_not_send() -> None:
    cases = [
        [Phase42SessionEvent(author_type="self")],
        [Phase42SessionEvent(author_type="bot")],
        [Phase42SessionEvent(duplicate=True)],
        [Phase42SessionEvent(channel_scope="public")],
        [Phase42SessionEvent(channel_scope="team")],
        [Phase42SessionEvent(operator_command=True)],
        [],
    ]
    for events in cases:
        adapter = FakePhase42SessionAdapter(events=events)
        report = build_phase42_supervised_private_test_session(
            ready_env(),
            allow_actual_phase42_supervised_session=True,
            session_adapter=adapter,
        )
        assert_true(report["discord_api_send_called"] is False, "No API")
        assert_true(report["discord_message_sent"] is False, "No message")
        assert_true(report["message_sent_count"] == 0, "No count")
        assert_true(report["actual_supervised_session_executed"] is False, "No supervised send")
        assert_true(adapter.send_called is False, "No send call")


def test_phase42_failed_fake_send_stays_blocked() -> None:
    adapter = FakePhase42SessionAdapter(
        events=[Phase42SessionEvent()],
        send_result=Phase42SessionSendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type="fake"),
    )
    report = build_phase42_supervised_private_test_session(
        ready_env(),
        allow_actual_phase42_supervised_session=True,
        session_adapter=adapter,
    )
    assert_true(report["blocked"] is True, "Failed send blocked")
    assert_true(report["actual_supervised_session_executed"] is False, "No execution")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")


def test_env_none_reads_process_env() -> None:
    env = ready_env()
    original = {key: os.environ.get(key) for key in env}
    try:
        os.environ.update(env)
        report = build_phase42_supervised_private_test_session_preflight()
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    assert_true(report["manual_approval_present"] is True, "Approval present")
    assert_true(report["manual_approval_true"] is True, "Approval true")
    assert_true(report["approval_phrase_present"] is True, "Phrase present")
    assert_true(report["approval_phrase_exact_match"] is True, "Phrase match")
    assert_true(report["max_session_messages"] == 2, "Session messages")
    assert_true(report["max_reply_count"] == 2, "Reply count")
    assert_true(report["max_send_count"] == 2, "Send count")
    assert_true(report["timeout_seconds"] == 90, "Timeout")
    assert_true(report["cooldown_seconds"] == 1, "Cooldown")
    assert_true(report["reply_mode_private_test_only"] is True, "Reply mode")
    assert_true(report["deterministic_reply_only"] is True, "Deterministic")
    assert_true(report["frozen_reply_only"] is True, "Frozen")
    assert_true(report["ready_for_phase42_manual_supervised_session"] is True, "Ready")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No send")


def test_blocked_reason_fixtures() -> None:
    cases = [
        ({"HERMES_PHASE42_SUPERVISED_SESSION_APPROVED": "false"}, "manual_approval_missing"),
        ({"HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE": "wrong"}, "approval_phrase_mismatch"),
        ({"HERMES_PHASE42_MAX_REPLY_COUNT": "0"}, "max_reply_count_missing"),
        ({"HERMES_PHASE42_TIMEOUT_SECONDS": "0"}, "timeout_missing"),
        ({"HERMES_PHASE42_COOLDOWN_SECONDS": "-1"}, "cooldown_missing"),
        ({"HERMES_DISCORD_SEND_MESSAGES": "false"}, "send_messages_disabled"),
        ({"HERMES_DISCORD_PRIVATE_TEST_REPLY": "false"}, "private_test_reply_disabled"),
        ({"HERMES_DISCORD_REPLY_MODE": "team"}, "reply_mode_not_private_test_only"),
    ]
    for override, reason in cases:
        env = {**ready_env(), **override}
        report = build_phase42_supervised_private_test_session_preflight(env)
        assert_true(reason in report["blocked_reasons"], reason)
        assert_true(report["ready_for_phase42_manual_supervised_session"] is False, "Not ready")


def test_phase42_no_sensitive_values() -> None:
    text = json.dumps(
        build_phase42_supervised_private_test_session(
            ready_env(),
            allow_actual_phase42_supervised_session=True,
            session_adapter=FakePhase42SessionAdapter(events=[Phase42SessionEvent()]),
        ),
        ensure_ascii=False,
    ).lower()
    assert_true("i_approve_" not in text, "No phrase value")
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    for test in (
        test_phase42_default_blocked_no_runtime,
        test_phase42_gate_values_do_not_open_runtime,
        test_phase42_runtime_default_blocked_does_not_call_adapter,
        test_phase42_fake_adapter_supervised_session_sends_once,
        test_phase42_ignored_events_do_not_send,
        test_phase42_failed_fake_send_stays_blocked,
        test_env_none_reads_process_env,
        test_blocked_reason_fixtures,
        test_phase42_no_sensitive_values,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 42 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
