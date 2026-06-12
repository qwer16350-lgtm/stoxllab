"""Local replay and approval queue tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_replay_approval.py
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from replay import run_replay


ROOT = APP_DIR.parents[1]
EVENTS = ROOT / "apps" / "hermes_gateway" / "examples" / "replay_events.example.json"
ACTIONS = ROOT / "apps" / "hermes_gateway" / "examples" / "approval_actions.example.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_replay_processes_at_least_eight_events() -> None:
    output = run_replay(EVENTS)
    assert_true(output["events_processed"] >= 8, "Replay should process at least 8 events")


def test_approval_required_count() -> None:
    output = run_replay(EVENTS)
    assert_true(output["summary"]["approval_required_count"] >= 1, "Replay should create approval-required items")


def test_pending_queue_created() -> None:
    output = run_replay(EVENTS)
    assert_true(any(item["status"] == "pending" for item in output["approval_queue"]), "Approval queue should contain pending items")


def test_approval_actions_apply_approve_and_reject() -> None:
    output = run_replay(EVENTS, ACTIONS)
    statuses = {item["source_event_id"]: item["status"] for item in output["approval_queue"]}
    assert_true(statuses.get("evt_sns_publish_002") == "approved", "SNS publish item should be approved")
    assert_true(statuses.get("evt_homepage_upload_003") == "rejected", "Homepage upload item should be rejected")
    assert_true(statuses.get("evt_grant_submit_005") == "approved", "Grant submit item should be approved")


def test_external_execution_count_zero() -> None:
    output = run_replay(EVENTS, ACTIONS)
    assert_true(output["summary"]["external_execution_count"] == 0, "External execution count must remain zero")


def test_approved_items_remain_human_only() -> None:
    output = run_replay(EVENTS, ACTIONS)
    approved = [item for item in output["approval_queue"] if item["status"] == "approved"]
    assert_true(approved, "There should be approved mock items")
    assert_true(all(item["human_only_execution"] is True for item in approved), "Approved items must remain human-only")
    assert_true(all(item["external_execution_allowed"] is False for item in approved), "Approved items must not allow external execution")


def test_api_key_request_blocked() -> None:
    output = run_replay(EVENTS, ACTIONS)
    secret_event = next(event for event in output["events"] if event["event_id"] == "evt_secret_008")
    assert_true(secret_event["blocked"] is True, "API key request should be blocked")


def main() -> int:
    tests = [
        test_replay_processes_at_least_eight_events,
        test_approval_required_count,
        test_pending_queue_created,
        test_approval_actions_apply_approve_and_reject,
        test_external_execution_count_zero,
        test_approved_items_remain_human_only,
        test_api_key_request_blocked,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All replay approval tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
