"""Phase 30 live event review packet tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_live_event_review_packet.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from live_event_audit_persistence import build_live_event_audit_record, build_sample_visibility_event
from live_event_review_packet import build_live_event_review_packet, render_live_event_review_packet_markdown, write_live_event_review_packet
from live_event_routing_report import build_live_event_routing_report
from would_send_preview import build_would_send_preview


ROOT = APP_DIR.parents[1]
TEST_ROOT = ROOT / "exports" / "hermes_gateway_test" / "phase30_packets"
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def packet() -> dict:
    audit = build_live_event_audit_record(build_sample_visibility_event(), content="hello")
    routing = build_live_event_routing_report(audit)
    preview = build_would_send_preview(audit, routing)
    return build_live_event_review_packet(audit, routing, preview)


def test_packet_created() -> None:
    item = packet()
    assert_true(item["packet_type"] == "live_event_review_packet", "Packet should be created")


def test_human_review_required() -> None:
    assert_true(packet()["human_review"]["required"] is True, "Human review should be required")


def test_disallowed_auto_reply_present() -> None:
    assert_true("auto_reply" in packet()["human_review"]["disallowed_actions"], "auto_reply should be disallowed")


def test_json_write() -> None:
    paths = write_live_event_review_packet(packet(), root=TEST_ROOT)
    assert_true(Path(paths["json_path"]).exists(), "JSON packet should be written")


def test_markdown_render() -> None:
    text = render_live_event_review_packet_markdown(packet())
    assert_true("# Live Event Review Packet" in text, "Markdown should render")


def test_execution_flags_false() -> None:
    safety = packet()["safety_assertions"]
    assert_true(safety["message_sent"] is False, "message_sent should be false")
    assert_true(safety["external_execution"] is False, "external_execution should be false")
    assert_true(safety["llm_called"] is False, "llm_called should be false")
    assert_true(safety["rag_called"] is False, "rag_called should be false")


def test_no_raw_token_or_id_leak() -> None:
    text = json.dumps(packet(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Token markers should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_summary_fields_consistent() -> None:
    item = packet()
    assert_true(item["summary"]["channel_name"] == item["audit_record"]["channel_name"], "Summary channel should match audit")
    assert_true(item["summary"]["agent_route_candidate"] == item["routing_report"]["agent_route_candidate"], "Summary route should match routing")


def main() -> int:
    tests = [
        test_packet_created,
        test_human_review_required,
        test_disallowed_auto_reply_present,
        test_json_write,
        test_markdown_render,
        test_execution_flags_false,
        test_no_raw_token_or_id_leak,
        test_summary_fields_consistent,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All live event review packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
