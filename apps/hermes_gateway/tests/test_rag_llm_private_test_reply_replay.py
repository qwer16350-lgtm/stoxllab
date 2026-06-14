"""Phase 33D-safe RAG+LLM private test reply replay tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_llm_private_test_reply_replay import EVENT_TYPES, build_rag_llm_private_test_reply_replay_report, render_rag_llm_private_test_reply_replay_markdown


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_all_required_event_types_present() -> None:
    report = build_rag_llm_private_test_reply_replay_report()
    event_types = {item["event_type"] for item in report["events"]}
    for event_type in EVENT_TYPES:
        assert_true(event_type in event_types, f"Missing {event_type}")


def test_public_self_bot_blocked_before_retrieval() -> None:
    report = build_rag_llm_private_test_reply_replay_report()
    by_type = {item["event_type"]: item for item in report["events"]}
    for key in ("public_channel_blocked_before_retrieval", "self_message_skipped_before_retrieval", "bot_message_skipped_before_retrieval"):
        assert_true(by_type[key]["retrieval_executed"] is False, f"{key} should block before retrieval")


def test_operations_and_invalid_source_represented() -> None:
    report = build_rag_llm_private_test_reply_replay_report()
    reasons = {item["reason"] for item in report["events"]}
    assert_true("operations_source_not_allowed" in reasons, "operations represented")
    assert_true("invalid_source" in reasons, "invalid source represented")


def test_context_packet_output_budget_circuit_cases() -> None:
    report = build_rag_llm_private_test_reply_replay_report()
    reasons = {item["reason"] for item in report["events"]}
    for reason in ("context_too_large", "too_many_documents", "rag_response_packet_missing", "output_safety_blocked", "cooldown", "budget_exhausted", "rate_limit_circuit_breaker", "send_exception_circuit_breaker"):
        assert_true(reason in reasons, f"{reason} represented")


def test_top_level_safety_false() -> None:
    report = build_rag_llm_private_test_reply_replay_report()
    assert_true(report["actual_message_sent"] is False, "No actual send")
    assert_true(report["llm_api_called"] is False, "No LLM")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external")


def test_report_safe_and_markdown() -> None:
    report = build_rag_llm_private_test_reply_replay_report()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text, "No secret")
    assert_true(not LONG_ID_RE.search(text), "No raw IDs")
    assert_true("RAG+LLM Private Test Reply Replay" in render_rag_llm_private_test_reply_replay_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_all_required_event_types_present,
        test_public_self_bot_blocked_before_retrieval,
        test_operations_and_invalid_source_represented,
        test_context_packet_output_budget_circuit_cases,
        test_top_level_safety_false,
        test_report_safe_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM private test reply replay tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
