"""Phase 29 audit-only live event pipeline tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_live_event_pipeline.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from live_event_pipeline import build_live_event_pipeline_report, normalize_live_discord_message_event, process_live_event_audit_only


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sample_event() -> dict:
    return {
        "id": "123456789012345678",
        "guild_id": "234567890123456789",
        "channel_id": "345678901234567890",
        "channel_name": "marin-초안",
        "content": "SNS 초안 후보를 검토해 주세요.",
        "author": {"id": "456789012345678901", "display_name": "tester", "bot": False, "roles": ["Decision Maker"]},
        "attachments": [{"filename": "local.png"}],
        "mentions": [],
    }


def test_normalize_redacts_discord_ids() -> None:
    event = normalize_live_discord_message_event(sample_event())
    text = json.dumps(event, ensure_ascii=False)
    assert_true(not LONG_NUMBER_RE.search(text), "Normalized live event should redact long Discord-like IDs")
    assert_true(event["channel_name"] == "marin-초안", "Channel name should be preserved")


def test_process_live_event_is_audit_only() -> None:
    result = process_live_event_audit_only(sample_event(), root=ROOT)
    assert_true(result["pipeline_mode"] == "audit_only", "Pipeline should be audit-only")
    assert_true(result["status"] == "processed_audit_only", "Pipeline should process non-bot event")
    assert_true(result["safety"]["message_sent"] is False, "Pipeline must not send messages")
    assert_true(result["safety"]["write_action_blocked"] is True, "Outbound action should be blocked")


def test_bot_message_is_ignored() -> None:
    event = sample_event()
    event["author"]["bot"] = True
    result = process_live_event_audit_only(event, root=ROOT)
    assert_true(result["status"] == "ignored_self_or_bot_message", "Bot-authored messages should be ignored")
    assert_true(result["would_send_payload"]["message_sent"] is False, "Ignored bot message should not send")


def test_would_send_payload_is_disabled() -> None:
    result = process_live_event_audit_only(sample_event(), root=ROOT)
    payload = result["would_send_payload"]
    assert_true(payload["will_send"] is False, "Would-send payload should not be live-send enabled")
    assert_true(payload["message_sent"] is False, "Would-send payload should not send")


def test_audit_payload_redacts_attachments() -> None:
    result = process_live_event_audit_only(sample_event(), root=ROOT)
    audit = result["audit_log_payload"]
    attachments = audit["normalized_request"]["attachments"]
    assert_true(attachments[0]["redacted"] is True, "Attachment originals should be redacted")


def test_pipeline_report_safe() -> None:
    report = build_live_event_pipeline_report(ROOT)
    text = json.dumps(report, ensure_ascii=False)
    assert_true(report["safety_assertions"]["message_sent"] is False, "Report must not send messages")
    assert_true(report["safety_assertions"]["discord_api_called_by_report"] is False, "Report must not call Discord API")
    assert_true(not LONG_NUMBER_RE.search(text), "Report should not contain long Discord-like IDs")


def main() -> int:
    tests = [
        test_normalize_redacts_discord_ids,
        test_process_live_event_is_audit_only,
        test_bot_message_is_ignored,
        test_would_send_payload_is_disabled,
        test_audit_payload_redacts_attachments,
        test_pipeline_report_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All live event pipeline tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
