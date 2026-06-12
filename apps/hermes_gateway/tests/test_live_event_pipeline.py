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

from live_event_pipeline import build_live_event_pipeline_report, normalize_live_discord_message_event, process_live_event_audit_only, write_visibility_log


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


def visibility_context() -> dict:
    return {
        "guild_configured": True,
        "allowed_guild_id": "234567890123456789",
        "mapped_channel_names": {"marin-珥덉븞": "junior_draft"},
        "mapped_channel_ids": {"345678901234567890": {"channel_name": "marin-珥덉븞", "workflow_role": "junior_draft"}},
    }


def private_test_visibility_context() -> dict:
    context = visibility_context()
    context["private_test_channel_id"] = "777777777777777777"
    return context


def test_normalize_redacts_discord_ids() -> None:
    event = normalize_live_discord_message_event(sample_event())
    text = json.dumps(event, ensure_ascii=False)
    assert_true(not LONG_NUMBER_RE.search(text), "Normalized live event should redact long Discord-like IDs")
    assert_true(event["channel_name"] == "marin-초안", "Channel name should be preserved")


def test_process_live_event_is_audit_only() -> None:
    result = process_live_event_audit_only(sample_event(), root=ROOT, visibility_context=visibility_context())
    event = result["visibility_event"]
    assert_true(result["pipeline_mode"] == "audit_only", "Pipeline should be audit-only")
    assert_true(result["status"] == "processed_audit_only", "Pipeline should process non-bot event")
    assert_true(result["decision"] == "accepted_mapped_channel", "Mapped channel should be accepted for audit-only processing")
    assert_true(event["guild_configured"] is True, "Accepted mapped channel should have guild_configured=true")
    assert_true(event["channel_mapped"] is True, "Accepted mapped channel should have channel_mapped=true")
    assert_true(bool(event["workflow_role"]), "Accepted mapped channel should include workflow role")
    assert_true(result["safety"]["message_sent"] is False, "Pipeline must not send messages")
    assert_true(result["safety"]["write_action_blocked"] is True, "Outbound action should be blocked")


def test_bot_message_is_ignored() -> None:
    event = sample_event()
    event["author"]["bot"] = True
    result = process_live_event_audit_only(event, root=ROOT, visibility_context=visibility_context())
    assert_true(result["decision"] == "ignored_self_message", "Bot-authored messages should be ignored")
    assert_true(result["reason"] == "ignored_self_message", "Self/bot reason should be explicit")
    assert_true(result["would_send_payload"]["message_sent"] is False, "Ignored bot message should not send")


def test_unmapped_channel_is_ignored() -> None:
    event = sample_event()
    event["channel_name"] = "random-channel"
    event["channel_id"] = "999999999999999999"
    result = process_live_event_audit_only(event, root=ROOT, visibility_context=visibility_context())
    assert_true(result["decision"] == "ignored_unmapped_channel", "Unmapped channel should be ignored")
    assert_true(result["visibility_event"]["guild_configured"] is True, "Unmapped channel in target guild should keep guild_configured=true")
    assert_true(result["visibility_event"]["channel_mapped"] is False, "Unmapped channel should have channel_mapped=false")
    assert_true(result["visibility_event"]["workflow_role"] == "", "Unmapped channel should not include workflow role")
    assert_true(result["message_sent"] is False, "Unmapped channel should not send")


def test_unmapped_private_test_channel_id_match_is_accepted() -> None:
    event = sample_event()
    event["channel_name"] = "hermes-private-test"
    event["channel_id"] = "777777777777777777"
    event["content"] = "lucy private test reply please"
    result = process_live_event_audit_only(event, root=ROOT, visibility_context=private_test_visibility_context())
    assert_true(result["decision"] == "accepted_private_test_channel", "Private test channel ID match should be accepted")
    assert_true(result["visibility_event"]["channel_is_private_test"] is True, "Private test channel marker should be true")
    assert_true(result["visibility_event"]["channel_mapped"] is False, "Private test channel should not require work channel mapping")
    assert_true(result["routing_report"]["agent_route_candidate"] == "lucy", "Private test route should use deterministic keyword routing")
    assert_true(result["agent_placeholder_response"]["response_type"] == "agent_placeholder_response", "Private test event should build placeholder response")


def test_private_test_channel_name_only_stays_unmapped() -> None:
    event = sample_event()
    event["channel_name"] = "hermes-private-test"
    event["channel_id"] = "888888888888888888"
    result = process_live_event_audit_only(event, root=ROOT, visibility_context=private_test_visibility_context())
    assert_true(result["decision"] == "ignored_unmapped_channel", "Private test channel name alone should not be accepted")
    assert_true(result["visibility_event"]["channel_is_private_test"] is False, "ID mismatch should not be marked private test")


def test_guild_mismatch_is_ignored() -> None:
    event = sample_event()
    event["guild_id"] = "999999999999999999"
    result = process_live_event_audit_only(event, root=ROOT, visibility_context=visibility_context())
    assert_true(result["decision"] == "ignored_guild_not_allowed", "Guild mismatch should be ignored")
    assert_true(result["visibility_event"]["guild_configured"] is False, "Guild mismatch should have guild_configured=false")
    assert_true(result["visibility_event"]["channel_mapped"] is False, "Guild mismatch should not report channel as mapped")
    assert_true(result["message_sent"] is False, "Guild mismatch should not send")


def test_empty_content_is_visible() -> None:
    event = sample_event()
    event["content"] = ""
    result = process_live_event_audit_only(event, root=ROOT, visibility_context=visibility_context())
    assert_true(result["decision"] == "content_unavailable_or_empty", "Empty content should be visible")
    assert_true(result["visibility_event"]["guild_configured"] is True, "Empty content in target guild should keep guild_configured=true")
    assert_true(result["visibility_event"]["channel_mapped"] is True, "Empty content in mapped channel should keep channel_mapped=true")
    assert_true(result["visibility_event"]["content_present"] is False, "Content presence should be false")


def test_would_send_payload_is_disabled() -> None:
    result = process_live_event_audit_only(sample_event(), root=ROOT, visibility_context=visibility_context())
    payload = result["would_send_payload"]
    assert_true(payload["will_send"] is False, "Would-send payload should not be live-send enabled")
    assert_true(payload["message_sent"] is False, "Would-send payload should not send")


def test_audit_payload_redacts_attachments() -> None:
    result = process_live_event_audit_only(sample_event(), root=ROOT, visibility_context=visibility_context())
    audit = result["audit_log_payload"]
    attachments = audit["normalized_request"]["attachments"]
    assert_true(attachments[0]["redacted"] is True, "Attachment originals should be redacted")


def test_visibility_log_writer_creates_jsonl_line() -> None:
    path = ROOT / "logs" / "hermes_gateway_test" / "live_events" / "readonly_events_test.jsonl"
    if path.exists():
        path.unlink()
    result = process_live_event_audit_only(sample_event(), root=ROOT, visibility_context=visibility_context(), write_log=True, log_path=path)
    assert_true(path.exists(), "Visibility log writer should create a jsonl file")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert_true(len(lines) == 1, "Visibility log writer should append one line")
    data = json.loads(lines[0])
    assert_true(data["decision"] == result["decision"], "Visibility log should contain decision")
    assert_true(data["guild_configured"] is True, "Visibility log should preserve guild_configured=true for accepted mapped channel")
    assert_true(data["channel_mapped"] is True, "Visibility log should preserve channel_mapped=true")
    assert_true(data["workflow_role"] == "junior_draft", "Visibility log should preserve workflow role")
    assert_true(data["message_sent"] is False, "Visibility log must show no message sent")


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
        test_unmapped_channel_is_ignored,
        test_unmapped_private_test_channel_id_match_is_accepted,
        test_private_test_channel_name_only_stays_unmapped,
        test_guild_mismatch_is_ignored,
        test_empty_content_is_visible,
        test_would_send_payload_is_disabled,
        test_audit_payload_redacts_attachments,
        test_visibility_log_writer_creates_jsonl_line,
        test_pipeline_report_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All live event pipeline tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
