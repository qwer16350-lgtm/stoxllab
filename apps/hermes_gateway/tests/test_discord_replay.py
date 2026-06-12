"""Local Discord raw event replay tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_discord_replay.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from discord_replay import load_discord_raw_events, run_discord_raw_event_replay


ROOT = APP_DIR.parents[1]
EVENTS = ROOT / "apps" / "hermes_gateway" / "examples" / "discord_raw_event_replay.example.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def replay() -> dict:
    events = load_discord_raw_events(EVENTS)
    return run_discord_raw_event_replay(events, root=ROOT)


def by_id(result: dict, event_id: str) -> dict:
    for event in result["events"]:
        if event["event_id"] == event_id:
            return event
    raise AssertionError(f"Missing event_id={event_id}")


def test_replay_processes_at_least_ten_events() -> None:
    result = replay()
    assert_true(result["events_processed"] >= 10, "Discord replay should process at least 10 events")


def test_would_send_payloads_present() -> None:
    result = replay()
    assert_true(len(result["would_send_payloads"]) >= 1, "Replay should build would-send payloads")
    assert_true(result["summary"]["would_send_count"] == len(result["would_send_payloads"]), "Would-send count should match payload count")


def test_sns_draft_agent_dispatch() -> None:
    event = by_id(replay(), "discord_replay_evt_001_sns_draft")
    assert_true(event["would_send_payload"]["message_kind"] == "agent_dispatch", "SNS draft should dispatch to an agent")


def test_sns_publish_approval_required() -> None:
    event = by_id(replay(), "discord_replay_evt_002_sns_publish")
    assert_true(event["would_send_payload"]["message_kind"] == "approval_required", "SNS publish should require approval")


def test_grant_submit_human_only() -> None:
    event = by_id(replay(), "discord_replay_evt_005_grant_submit")
    assert_true(event["dispatch_plan"]["human_only_execution"] is True, "Grant submit should remain human-only")
    assert_true(event["would_send_payload"]["message_kind"] in {"approval_required", "blocked_request"}, "Grant submit should be approval-gated or blocked")


def test_junior_shortcut_blocked() -> None:
    event = by_id(replay(), "discord_replay_evt_008_junior_shortcut")
    assert_true(event["blocked"] is True, "Junior direct approval shortcut should be blocked")
    assert_true(event["would_send_payload"]["message_kind"] == "blocked_request", "Junior shortcut should render blocked_request")


def test_unknown_channel_blocked() -> None:
    event = by_id(replay(), "discord_replay_evt_009_unknown_channel")
    assert_true(event["blocked"] is True, "Unknown channel should be blocked")
    assert_true(event["would_send_payload"]["message_kind"] == "blocked_request", "Unknown channel should render blocked_request")


def test_credential_request_blocked() -> None:
    event = by_id(replay(), "discord_replay_evt_010_credential_request")
    assert_true(event["blocked"] is True, "Credential request should be blocked")
    assert_true(event["would_send_payload"]["message_kind"] == "blocked_request", "Credential request should render blocked_request")


def test_payload_safety_flags_false() -> None:
    result = replay()
    for payload in result["would_send_payloads"]:
        safety = payload["safety"]
        assert_true(safety["message_sent"] is False, "Message must not be sent")
        assert_true(safety["discord_api_called"] is False, "Discord API must not be called")
        assert_true(safety["external_execution"] is False, "External execution must remain false")


def test_summary_external_and_message_counts_zero() -> None:
    summary = replay()["summary"]
    assert_true(summary["external_execution_count"] == 0, "external_execution_count must be 0")
    assert_true(summary["message_sent_count"] == 0, "message_sent_count must be 0")


def test_secret_like_values_redacted() -> None:
    result_text = json.dumps(replay(), ensure_ascii=False).lower()
    assert_true("api key" not in result_text, "Secret-like request text should be redacted")
    assert_true("token" not in result_text, "Token-like values should not appear")


def test_safety_assertions_pass() -> None:
    result = replay()
    assert_true(all(item["passed"] is True for item in result["safety_assertions"]), "All safety assertions should pass")


def main() -> int:
    tests = [
        test_replay_processes_at_least_ten_events,
        test_would_send_payloads_present,
        test_sns_draft_agent_dispatch,
        test_sns_publish_approval_required,
        test_grant_submit_human_only,
        test_junior_shortcut_blocked,
        test_unknown_channel_blocked,
        test_credential_request_blocked,
        test_payload_safety_flags_false,
        test_summary_external_and_message_counts_zero,
        test_secret_like_values_redacted,
        test_safety_assertions_pass,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Discord raw event replay tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
