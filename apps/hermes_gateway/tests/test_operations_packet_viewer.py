"""Phase 31A operations packet viewer tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_operations_packet_viewer.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from live_event_audit_persistence import build_daily_live_event_manifest, build_live_event_audit_record, build_sample_visibility_event
from live_event_review_packet import build_live_event_review_packet, write_live_event_review_packet
from live_event_routing_report import build_live_event_routing_report
from operations_packet_viewer import (
    assert_viewer_output_safe,
    build_operations_packet_viewer_report,
    filter_events,
    list_recent_live_events,
    list_recent_review_packets,
    load_daily_manifest,
    load_review_packet,
    render_operations_summary_markdown,
)
from would_send_preview import build_would_send_preview


ROOT = APP_DIR.parents[1]
TEST_ROOT = ROOT / "logs" / "hermes_gateway_test" / "phase31_viewer"
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def setup_artifacts() -> dict:
    date = "20260613"
    log_dir = TEST_ROOT / "logs" / "hermes_gateway" / "live_events"
    log_dir.mkdir(parents=True, exist_ok=True)
    visibility = build_sample_visibility_event()
    visibility["created_at"] = "2026-06-13T01:00:00+00:00"
    visibility["event_id"] = "event_redacted_0000"
    audit = build_live_event_audit_record(visibility, content="hello from marketing")
    ignored_visibility = dict(visibility)
    ignored_visibility.update(
        {
            "created_at": "2026-06-13T01:05:00+00:00",
            "decision": "ignored_unmapped_channel",
            "reason": "ignored_unmapped_channel",
            "channel_mapped": False,
            "workflow_role": "",
            "agent_route_candidate": "unrouted",
        }
    )
    ignored = build_live_event_audit_record(ignored_visibility, content="")
    log_path = log_dir / f"readonly_events_{date}.jsonl"
    log_path.write_text(json.dumps(audit, ensure_ascii=False) + "\n" + json.dumps(ignored, ensure_ascii=False) + "\n", encoding="utf-8")
    build_daily_live_event_manifest(root=TEST_ROOT, date="2026-06-13T00:00:00+00:00")
    routing = build_live_event_routing_report(audit)
    preview = build_would_send_preview(audit, routing)
    packet = build_live_event_review_packet(audit, routing, preview)
    paths = write_live_event_review_packet(packet, root=TEST_ROOT)
    return {"audit": audit, "packet": packet, "paths": paths}


def test_recent_events_returned() -> None:
    setup_artifacts()
    events = list_recent_live_events(TEST_ROOT, date="20260613")
    assert_true(len(events) >= 2, "Recent events should be returned")


def test_limit_applied() -> None:
    setup_artifacts()
    assert_true(len(list_recent_live_events(TEST_ROOT, limit=1, date="20260613")) == 1, "Limit should be applied")


def test_date_filter_applied() -> None:
    setup_artifacts()
    assert_true(list_recent_live_events(TEST_ROOT, date="19990101") == [], "Missing date should return no events")


def test_channel_filter() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613", channel_name="marketing-brief")
    assert_true(all(item["channel_name"] == "marketing-brief" for item in report["recent_live_events"]), "Channel filter should apply")


def test_workflow_role_filter() -> None:
    setup_artifacts()
    events = filter_events(list_recent_live_events(TEST_ROOT, date="20260613"), workflow_role="marketing_intake")
    assert_true(all(item["workflow_role"] == "marketing_intake" for item in events), "Workflow filter should apply")


def test_agent_route_filter() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613", agent_route_candidate="marin")
    assert_true(all(item["agent_route_candidate"] == "marin" for item in report["recent_live_events"]), "Agent route filter should apply")


def test_decision_filter() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613", decision="accepted_mapped_channel")
    assert_true(all(item["decision"] == "accepted_mapped_channel" for item in report["recent_live_events"]), "Decision filter should apply")


def test_review_packet_list_returned() -> None:
    setup_artifacts()
    packets = list_recent_review_packets(TEST_ROOT)
    assert_true(len(packets) >= 1, "Review packet list should be returned")


def test_load_packet_by_event_id() -> None:
    data = setup_artifacts()
    packet = load_review_packet(TEST_ROOT, event_id=data["packet"]["event_id"])
    assert_true(packet["packet_type"] == "live_event_review_packet", "Packet detail should load by event_id")


def test_daily_manifest_load() -> None:
    setup_artifacts()
    manifest = load_daily_manifest(TEST_ROOT, date="20260613")
    assert_true(manifest["total_events"] >= 2, "Daily manifest summary should load")


def test_markdown_summary_render() -> None:
    setup_artifacts()
    markdown = render_operations_summary_markdown(build_operations_packet_viewer_report(TEST_ROOT, date="20260613"))
    assert_true("# STOXL Hermes Operations Viewer" in markdown, "Markdown summary should render")


def test_no_raw_token_or_id() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Token markers should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_no_env_or_local_mapping_read_flags() -> None:
    setup_artifacts()
    safety = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["safety_assertions"]
    assert_true(safety["env_file_read"] is False, ".env should not be read")
    assert_true(safety["local_mapping_file_read"] is False, "local mapping should not be read")


def test_safety_flags_false() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    assert_viewer_output_safe(report)
    safety = report["safety_assertions"]
    assert_true(safety["discord_api_called"] is False, "Discord API should not be called")
    assert_true(safety["message_sent"] is False, "Message should not be sent")
    assert_true(safety["external_execution"] is False, "External execution should be false")
    assert_true(safety["llm_called"] is False, "LLM should not be called")
    assert_true(safety["rag_called"] is False, "RAG should not be called")


def test_rag_llm_scaffold_summary() -> None:
    setup_artifacts()
    scaffold = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_llm_private_test_scaffold"]
    assert_true(scaffold["preflight_available"] is True, "RAG+LLM preflight should be available")
    assert_true(scaffold["context_safety_available"] is True, "Context safety should be available")
    assert_true(scaffold["prompt_envelope_available"] is True, "Prompt envelope should be available")
    assert_true(scaffold["would_send_preview_available"] is True, "Would-send should be available")
    assert_true(scaffold["replay_available"] is True, "Replay should be available")
    assert_true(scaffold["actual_discord_send"] is False, "No actual Discord send")
    assert_true(scaffold["actual_llm_api_call"] is False, "No actual LLM API call")
    assert_true(scaffold["embedding_api_call"] is False, "No embedding API call")
    assert_true(scaffold["external_execution"] is False, "No external execution")


def main() -> int:
    tests = [
        test_recent_events_returned,
        test_limit_applied,
        test_date_filter_applied,
        test_channel_filter,
        test_workflow_role_filter,
        test_agent_route_filter,
        test_decision_filter,
        test_review_packet_list_returned,
        test_load_packet_by_event_id,
        test_daily_manifest_load,
        test_markdown_summary_render,
        test_no_raw_token_or_id,
        test_no_env_or_local_mapping_read_flags,
        test_safety_flags_false,
        test_rag_llm_scaffold_summary,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All operations packet viewer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
