"""Phase 33D-4 RAG+LLM single live success closeout tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_llm_live_success_closeout.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_llm_live_success_closeout import (
    DEFAULT_LIVE_SUCCESS_LOG,
    build_rag_llm_live_success_closeout,
    render_rag_llm_live_success_closeout_markdown,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(func, message: str) -> None:
    try:
        func()
    except ValueError:
        return
    raise AssertionError(message)


def test_success_fixture_passes() -> None:
    report = build_rag_llm_live_success_closeout()
    assert_true(report["closeout_passed"] is True, "Closeout should pass")
    assert_true(report["ready_for_phase34_knowledge_ingestion"] is True, "Phase 34 readiness should be true")


def test_required_counts_are_exactly_one() -> None:
    report = build_rag_llm_live_success_closeout()
    assert_true(report["accepted_private_test_event_count"] == 1, "Accepted event should be exactly one")
    assert_true(report["retrieval_allowed_count"] == 1, "Retrieval allowed should be exactly one")
    assert_true(report["context_safety_allowed_count"] == 1, "Context safety should be exactly one")
    assert_true(report["rag_packet_created_count"] == 1, "RAG packet should be exactly one")
    assert_true(report["llm_call_allowed_count"] == 1, "LLM call allowed should be exactly one")
    assert_true(report["output_safety_allowed_count"] == 1, "Output safety should be exactly one")
    assert_true(report["discord_message_sent_count"] == 1, "Discord sent should be exactly one")


def test_self_message_skipped() -> None:
    report = build_rag_llm_live_success_closeout()
    assert_true(report["self_message_observed"] is True, "Self message should be observed")
    assert_true(report["self_message_skipped"] is True, "Self message should be skipped")
    assert_true(report["llm_call_after_self_message"] is False, "No LLM after self message")
    assert_true(report["sent_after_self_message"] is False, "No additional send after self message")


def test_private_test_channel_only() -> None:
    report = build_rag_llm_live_success_closeout()
    assert_true(report["private_test_channel_only"] is True, "Only private test channel should appear")


def test_no_secret_or_raw_ids() -> None:
    report = build_rag_llm_live_success_closeout()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Token markers should be absent")
    assert_true(report["token_value_logged"] is False, "Token value should not be logged")
    assert_true(report["api_key_value_logged"] is False, "API key value should not be logged")
    assert_true(report["raw_discord_ids_logged"] is False, "Raw Discord IDs should not be logged")


def test_safety_assertions() -> None:
    safety = build_rag_llm_live_success_closeout()["safety_assertions"]
    assert_true(safety["discord_live_runtime_executed_once"] is True, "Live runtime should be observed once")
    assert_true(safety["discord_message_sent_once"] is True, "Discord message should be sent once")
    assert_true(safety["llm_api_called_once"] is True, "LLM API should be allowed once")
    assert_true(safety["embedding_called"] is False, "Embedding should be false")
    assert_true(safety["external_execution"] is False, "External execution should be false")
    assert_true(safety["self_loop_prevented"] is True, "Self loop should be prevented")


def test_fails_if_sent_twice() -> None:
    log = DEFAULT_LIVE_SUCCESS_LOG + "[PRIVATE_TEST_RAG_LLM_REPLY_SENT] message_sent=true channel=hermes-private-test\n"
    report = build_rag_llm_live_success_closeout(log)
    assert_true(report["closeout_passed"] is False, "Sent twice should fail closeout")
    assert_true(report["sent_exactly_once"] is False, "Sent exactly once should be false")
    assert_true(report["discord_message_sent_count"] == 2, "Sent count should be two")


def test_fails_if_self_message_triggers_llm_again() -> None:
    log = DEFAULT_LIVE_SUCCESS_LOG.replace(
        "[PRIVATE_TEST_RAG_LLM_REPLY] skipped reason=self_message",
        "[PRIVATE_TEST_RAG_LLM_REPLY] skipped reason=self_message\n[PRIVATE_TEST_RAG_LLM_REPLY] llm_call_allowed",
    )
    report = build_rag_llm_live_success_closeout(log)
    assert_true(report["closeout_passed"] is False, "LLM after self should fail closeout")
    assert_true(report["llm_call_after_self_message"] is True, "LLM after self should be detected")


def test_raw_discord_id_rejected() -> None:
    log = DEFAULT_LIVE_SUCCESS_LOG.replace("discord_id_redacted:2216", "123456789012345678")
    assert_raises(lambda: build_rag_llm_live_success_closeout(log), "Raw Discord ID should be rejected")


def test_token_value_rejected() -> None:
    log = DEFAULT_LIVE_SUCCESS_LOG + "\ntoken=secret_value\n"
    assert_raises(lambda: build_rag_llm_live_success_closeout(log), "Token value should be rejected")


def test_api_key_value_rejected() -> None:
    log = DEFAULT_LIVE_SUCCESS_LOG + "\napi_key=secret_value\n"
    assert_raises(lambda: build_rag_llm_live_success_closeout(log), "API key value should be rejected")


def test_markdown_render() -> None:
    markdown = render_rag_llm_live_success_closeout_markdown(build_rag_llm_live_success_closeout())
    assert_true("# STOXL RAG+LLM Single Live Test Closeout" in markdown, "Markdown should render title")


def main() -> int:
    tests = [
        test_success_fixture_passes,
        test_required_counts_are_exactly_one,
        test_self_message_skipped,
        test_private_test_channel_only,
        test_no_secret_or_raw_ids,
        test_safety_assertions,
        test_fails_if_sent_twice,
        test_fails_if_self_message_triggers_llm_again,
        test_raw_discord_id_rejected,
        test_token_value_rejected,
        test_api_key_value_rejected,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM live success closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
