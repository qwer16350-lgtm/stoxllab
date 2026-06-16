from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase41b_private_test_reply_one_shot import build_phase41b_private_test_reply_one_shot
from phase41b_reply_adapters import FakePhase41BReplyAdapter, Phase41BReplyEvent, Phase41BReplySendResult


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env() -> dict[str, str]:
    return {
        "DISCORD_BOT_TOKEN": "SENSITIVE_TOKEN_VALUE_DO_NOT_LOG",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "SENSITIVE_CHANNEL_VALUE_DO_NOT_LOG",
        "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVED": "true",
        "HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE": "I_APPROVE_PHASE41B_PRIVATE_TEST_REPLY_ONE_SHOT",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_RAG_LLM_REPLY_ENABLED": "false",
    }


def test_fake_private_test_human_message_sends_once() -> None:
    adapter = FakePhase41BReplyAdapter(events=[Phase41BReplyEvent()])
    report = build_phase41b_private_test_reply_one_shot(
        ready_env(),
        allow_actual_private_test_reply=True,
        execute_actual_runtime=True,
        reply_adapter=adapter,
    )
    assert_true(report["version"] == "phase41b_actual_private_test_reply_one_shot", "Runtime version")
    assert_true(report["safe_prep_only"] is False, "Runtime separated from prep")
    assert_true(report["actual_runtime_path_available"] is True, "Runtime path available")
    assert_true(report["runtime_adapter_type"] == "fake", "Fake adapter")
    assert_true(report["actual_reply_send_executed"] is True, "Fake reply executed")
    assert_true(report["discord_api_send_called"] is True, "Fake API called")
    assert_true(report["discord_message_sent"] is True, "Fake message sent")
    assert_true(report["message_sent_count"] == 1, "One fake message")
    assert_true(report["sent_scope"] == "private_test_only", "Private-test scope")
    assert_true(report["ready_for_phase41c_actual_reply_closeout"] is True, "Ready for closeout")
    assert_true(report["ready_for_repeat_send"] is False, "No repeat")
    assert_true(adapter.send_called is True, "Fake send called")


def test_allow_flag_missing_does_not_run_adapter() -> None:
    adapter = FakePhase41BReplyAdapter(events=[Phase41BReplyEvent()])
    report = build_phase41b_private_test_reply_one_shot(ready_env(), execute_actual_runtime=True, reply_adapter=adapter)
    assert_true(report["blocked"] is True, "Blocked")
    assert_true("allow_actual_private_test_reply_flag_missing" in report["blocked_reasons"], "Allow flag missing")
    assert_true(adapter.collect_called is False, "No collect")
    assert_true(adapter.send_called is False, "No send")


def test_ignored_events_and_timeout_do_not_send() -> None:
    cases = [
        [Phase41BReplyEvent(author_type="self")],
        [Phase41BReplyEvent(author_type="bot")],
        [Phase41BReplyEvent(duplicate=True)],
        [Phase41BReplyEvent(channel_scope="public")],
        [Phase41BReplyEvent(channel_scope="team")],
        [],
    ]
    for events in cases:
        adapter = FakePhase41BReplyAdapter(events=events)
        report = build_phase41b_private_test_reply_one_shot(
            ready_env(),
            allow_actual_private_test_reply=True,
            execute_actual_runtime=True,
            reply_adapter=adapter,
        )
        assert_true(report["actual_reply_send_executed"] is False, "No reply")
        assert_true(report["discord_message_sent"] is False, "No message")
        assert_true(report["message_sent_count"] == 0, "No count")
        assert_true(report["ready_for_phase41c_actual_reply_closeout"] is False, "No closeout")
        assert_true(report["ready_for_repeat_send"] is False, "No repeat")


def test_one_shot_lock_consumed_blocks_runtime() -> None:
    adapter = FakePhase41BReplyAdapter(events=[Phase41BReplyEvent()])
    report = build_phase41b_private_test_reply_one_shot(
        ready_env(),
        allow_actual_private_test_reply=True,
        execute_actual_runtime=True,
        reply_adapter=adapter,
        one_shot_lock_consumed=True,
    )
    assert_true("one_shot_lock_consumed" in report["blocked_reasons"], "Lock reason")
    assert_true(adapter.collect_called is False, "Runtime not collected")
    assert_true(adapter.send_called is False, "Runtime not sent")


def test_failed_send_does_not_prepare_closeout() -> None:
    adapter = FakePhase41BReplyAdapter(
        events=[Phase41BReplyEvent()],
        send_result=Phase41BReplySendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type="fake"),
    )
    report = build_phase41b_private_test_reply_one_shot(
        ready_env(),
        allow_actual_private_test_reply=True,
        execute_actual_runtime=True,
        reply_adapter=adapter,
    )
    assert_true(report["actual_reply_send_executed"] is False, "No execution")
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_true(report["ready_for_phase41c_actual_reply_closeout"] is False, "No closeout")


def test_runtime_error_failure_is_classified_without_error_value() -> None:
    adapter = FakePhase41BReplyAdapter(
        events=[Phase41BReplyEvent()],
        send_result=Phase41BReplySendResult(
            api_send_called=False,
            message_sent=False,
            message_sent_count=0,
            sent_scope="none",
            adapter_type="fake",
            error_type="RuntimeError",
        ),
    )
    report = build_phase41b_private_test_reply_one_shot(
        ready_env(),
        allow_actual_private_test_reply=True,
        execute_actual_runtime=True,
        reply_adapter=adapter,
    )
    assert_true(report["send_result_error_type"] == "RuntimeError", "RuntimeError retained")
    assert_true(report["send_result_error_category"] == "adapter_not_wired_or_contract_error", "RuntimeError classified")
    assert_true(report["send_result_error_value_logged"] is False, "No error value")
    assert_true(report["actual_reply_send_executed"] is False, "No execution")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["message_sent_count"] == 0, "No send count")


def test_no_sensitive_values_or_external_calls() -> None:
    report = build_phase41b_private_test_reply_one_shot(
        ready_env(),
        allow_actual_private_test_reply=True,
        execute_actual_runtime=True,
        reply_adapter=FakePhase41BReplyAdapter(events=[Phase41BReplyEvent()]),
    )
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sensitive_token_value_do_not_log" not in text, "No token")
    assert_true("sensitive_channel_value_do_not_log" not in text, "No channel")
    assert_true("i_approve_" not in text, "No phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    for key in ("llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")


def main() -> int:
    tests = [
        test_fake_private_test_human_message_sends_once,
        test_allow_flag_missing_does_not_run_adapter,
        test_ignored_events_and_timeout_do_not_send,
        test_one_shot_lock_consumed_blocks_runtime,
        test_failed_send_does_not_prepare_closeout,
        test_runtime_error_failure_is_classified_without_error_value,
        test_no_sensitive_values_or_external_calls,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 41B actual reply runtime tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
