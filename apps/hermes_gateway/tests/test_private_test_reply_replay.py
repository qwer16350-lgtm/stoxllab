"""Phase 31E private test reply replay closeout tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_private_test_reply_replay.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from operations_packet_viewer import build_operations_packet_viewer_report, render_operations_summary_markdown
from private_test_reply_replay import (
    EVENT_KINDS,
    assert_private_test_reply_replay_safe,
    build_private_test_reply_replay_event,
    build_private_test_reply_replay_report,
    render_private_test_reply_replay_markdown,
    replay_private_test_reply_events,
    summarize_private_test_reply_replay,
)


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_replay_event_creation_for_all_kinds() -> None:
    for kind in EVENT_KINDS:
        event = build_private_test_reply_replay_event(kind)
        assert_true(event["kind"] == kind, f"Replay event should preserve kind: {kind}")
        assert_true(event["message_sent"] is False, "Replay event should not perform actual send")


def test_human_allowed_sent_uses_historical_flag_only() -> None:
    event = build_private_test_reply_replay_event("human_allowed_sent")
    assert_true(event["historical_message_sent"] is True, "Historical sent should be represented separately")
    assert_true(event["message_sent"] is False, "Actual replay message_sent should be false")


def test_replay_summary_counts() -> None:
    events = [build_private_test_reply_replay_event(kind) for kind in EVENT_KINDS]
    replay = replay_private_test_reply_events(events)
    summary = summarize_private_test_reply_replay(replay)
    assert_true(summary["allowed"] == 1, "Allowed count should be 1")
    assert_true(summary["sent"] == 1, "Historical sent count should be 1")
    assert_true(summary["blocked"] == 6, "Blocked count should be 6")
    assert_true(summary["skipped"] == 1, "Skipped count should be 1")
    assert_true(summary["self_message_skipped"] == 1, "Self-message skipped count should be 1")
    assert_true(summary["duplicate_blocked"] == 1, "Duplicate blocked count should be 1")
    assert_true(summary["cooldown_blocked"] == 1, "Cooldown blocked count should be 1")
    assert_true(summary["budget_exhausted_blocked"] == 1, "Budget exhausted count should be 1")
    assert_true(summary["circuit_breaker_opened"] == 2, "Circuit breaker count should be 2")
    assert_true(summary["public_channel_blocked"] == 1, "Public channel blocked count should be 1")


def test_report_safety_flags() -> None:
    report = build_private_test_reply_replay_report(ROOT)
    safety = report["safety_assertions"]
    assert_true(report["message_sent"] is False, "Replay report should not mark actual send")
    assert_true(safety["discord_api_called"] is False, "Replay should not call Discord API")
    assert_true(safety["llm_called"] is False and safety["rag_called"] is False, "Replay should not call LLM/RAG")
    assert_true(safety["external_execution"] is False, "Replay should not execute externally")
    assert_true(safety["env_file_read"] is False, "Replay should not read env file")
    assert_true(safety["local_mapping_file_read"] is False, "Replay should not read local mapping")


def test_report_has_no_token_or_raw_discord_id() -> None:
    report = build_private_test_reply_replay_report(ROOT)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_private_test_reply_replay_safe(report)
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Report should not contain token markers")
    assert_true(not LONG_NUMBER_RE.search(text), "Report should not contain raw Discord-like IDs")


def test_markdown_render() -> None:
    markdown = render_private_test_reply_replay_markdown(build_private_test_reply_replay_report(ROOT))
    assert_true("Private Test Reply Replay Report" in markdown, "Markdown should render title")
    assert_true("Historical sent" in markdown, "Markdown should include historical sent")


def test_operations_viewer_private_reply_summary() -> None:
    report = build_operations_packet_viewer_report(ROOT)
    summary = report.get("private_test_reply_summary", {})
    assert_true(summary.get("available") is True, "Operations viewer should expose private reply summary")
    assert_true(summary.get("sent_count") == 1, "Operations viewer should include historical sent count")
    assert_true(summary.get("blocked_count") == 6, "Operations viewer should include blocked count")
    markdown = render_operations_summary_markdown(report)
    assert_true("## Private Test Reply" in markdown, "Operations viewer markdown should include private reply section")


def main() -> int:
    tests = [
        test_replay_event_creation_for_all_kinds,
        test_human_allowed_sent_uses_historical_flag_only,
        test_replay_summary_counts,
        test_report_safety_flags,
        test_report_has_no_token_or_raw_discord_id,
        test_markdown_render,
        test_operations_viewer_private_reply_summary,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private test reply replay tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
