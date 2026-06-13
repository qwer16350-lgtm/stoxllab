"""Phase 32D LLM private test reply replay closeout tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_private_test_reply_replay.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from llm_private_test_reply_replay import (
    EVENT_TYPES,
    assert_llm_private_test_reply_replay_safe,
    build_llm_private_test_reply_replay_event,
    build_llm_private_test_reply_replay_report,
    render_llm_private_test_reply_replay_markdown,
    verify_live_success_fixture,
)
from operations_packet_viewer import build_operations_packet_viewer_report, render_operations_summary_markdown


ROOT = APP_DIR.parents[1]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_live_success_fixture_verified() -> None:
    result = verify_live_success_fixture()
    assert_true(result["verified"] is True, "Live success fixture should verify")
    assert_true(result["ready_log_exists"] is True, "Ready log should exist")
    assert_true(result["accepted_private_test_event_exists"] is True, "Accepted private event should exist")


def test_exactly_one_sent_event_in_fixture() -> None:
    result = verify_live_success_fixture()
    assert_true(result["sent_count"] == 1, "Fixture should have exactly one sent event")
    assert_true(result["llm_call_allowed_count"] == 1, "Fixture should have exactly one LLM allowed line")
    assert_true(result["output_safety_allowed_count"] == 1, "Fixture should have exactly one output safety allowed line")


def test_self_message_skipped_after_sent() -> None:
    result = verify_live_success_fixture()
    assert_true(result["self_message_skipped_exists"] is True, "Self-message skipped should exist")


def test_no_second_llm_call_after_self_message() -> None:
    result = verify_live_success_fixture()
    assert_true(result["no_second_llm_call_after_self_message"] is True, "Self-message should not trigger second LLM call")


def test_raw_discord_ids_not_present() -> None:
    result = verify_live_success_fixture()
    text = json.dumps(result, ensure_ascii=False)
    assert_true(result["raw_discord_ids_present"] is False, "Fixture validation should not find raw Discord IDs")
    assert_true(not LONG_ID_RE.search(text), "Verification result should not contain raw Discord IDs")


def test_replay_event_types_create() -> None:
    for event_type in EVENT_TYPES:
        event = build_llm_private_test_reply_replay_event(event_type)
        assert_true(event["event_type"] == event_type, f"Event type should be preserved: {event_type}")
        assert_true(event["message_sent"] is False, "Replay event should not perform live send")


def test_human_private_test_allowed_sent_replay() -> None:
    event = build_llm_private_test_reply_replay_event("human_private_test_llm_allowed_sent")
    assert_true(event["allowed"] is True, "Human private test event should be allowed historically")
    assert_true(event["historical_message_sent"] is True, "Historical sent should be represented")
    assert_true(event["message_sent"] is False, "Replay top-level send should remain false")


def test_blocked_and_skipped_replay_cases() -> None:
    report = build_llm_private_test_reply_replay_report()
    summary = report["summary"]
    assert_true(summary["public_channel_blocked"] == 1, "Public channel block should be counted")
    assert_true(summary["private_channel_id_mismatch_blocked"] == 1, "Private channel ID mismatch should be counted")
    assert_true(summary["self_messages_skipped"] == 1, "Self skipped should be counted")
    assert_true(summary["duplicates_blocked"] == 1, "Duplicate block should be counted")
    assert_true(summary["cooldown_blocked"] == 1, "Cooldown block should be counted")
    assert_true(summary["budget_exhausted_blocked"] == 1, "Budget block should be counted")
    assert_true(summary["provider_error_blocked"] == 1, "Provider error block should be counted")
    assert_true(summary["output_safety_blocked"] == 1, "Output safety block should be counted")
    assert_true(summary["packet_safety_blocked"] == 1, "Packet safety block should be counted")
    assert_true(summary["circuit_breakers"] == 2, "Circuit breaker count should be two")


def test_replay_top_level_safety_flags_false() -> None:
    report = build_llm_private_test_reply_replay_report()
    assert_true(report["message_sent"] is False, "Replay closeout should not mark live send")
    assert_true(report["llm_api_called"] is False, "Replay closeout should not call LLM API")
    assert_true(report["live_discord_send_executed"] is False, "Replay closeout should not execute Discord send")
    assert_true(report["rag_called"] is False, "RAG should be false")
    assert_true(report["external_execution"] is False, "External execution should be false")


def test_operations_viewer_summary_includes_closeout() -> None:
    report = build_operations_packet_viewer_report(ROOT)
    summary = report["llm_private_test_reply_closeout"]
    assert_true(summary["available"] is True, "Operations viewer should include closeout")
    assert_true(summary["live_success_fixture_verified"] is True, "Viewer should show fixture verified")
    assert_true(summary["sent_in_fixture"] == 1, "Viewer should show one sent in fixture")
    assert_true(summary["llm_api_called_by_replay"] is False, "Viewer should show no replay LLM API call")
    assert_true(summary["discord_send_by_replay"] is False, "Viewer should show no replay Discord send")


def test_markdown_render_works() -> None:
    markdown = render_llm_private_test_reply_replay_markdown(build_llm_private_test_reply_replay_report())
    assert_true("LLM Private Test Reply Closeout" in markdown, "Markdown title should render")
    assert_true("Replay Discord send: false" in markdown, "Markdown should include replay safety")
    viewer_markdown = render_operations_summary_markdown(build_operations_packet_viewer_report(ROOT))
    assert_true("## LLM Private Test Reply Closeout" in viewer_markdown, "Operations viewer markdown should include closeout")


def test_json_example_has_no_token_api_key_or_raw_id() -> None:
    path = APP_DIR / "examples" / "llm_private_test_reply_replay_report.example.json"
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    assert_llm_private_test_reply_replay_safe(data)
    lowered = text.lower()
    assert_true("sk-" not in lowered and "xoxb-" not in lowered and "token=" not in lowered, "Example should not contain secret values")
    assert_true(not LONG_ID_RE.search(text), "Example should not contain raw Discord IDs")


def main() -> int:
    tests = [
        test_live_success_fixture_verified,
        test_exactly_one_sent_event_in_fixture,
        test_self_message_skipped_after_sent,
        test_no_second_llm_call_after_self_message,
        test_raw_discord_ids_not_present,
        test_replay_event_types_create,
        test_human_private_test_allowed_sent_replay,
        test_blocked_and_skipped_replay_cases,
        test_replay_top_level_safety_flags_false,
        test_operations_viewer_summary_includes_closeout,
        test_markdown_render_works,
        test_json_example_has_no_token_api_key_or_raw_id,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM private test reply replay tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
