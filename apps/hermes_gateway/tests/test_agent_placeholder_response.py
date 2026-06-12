"""Phase 31C deterministic agent placeholder response tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_agent_placeholder_response.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agent_placeholder_response import (
    assert_agent_placeholder_response_safe,
    build_agent_placeholder_response,
    render_agent_placeholder_response_markdown,
    write_agent_placeholder_response,
)
from live_event_audit_persistence import build_live_event_audit_record, build_sample_visibility_event
from live_event_review_packet import build_live_event_review_packet, write_live_event_review_packet
from live_event_routing_report import build_live_event_routing_report
from operations_packet_viewer import list_recent_review_packets
from would_send_preview import build_would_send_preview


ROOT = APP_DIR.parents[1]
TEST_ROOT = ROOT / "logs" / "hermes_gateway_test" / "phase31c_placeholder"
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def audit_and_routing(agent: str = "marin", workflow_role: str = "marketing_intake") -> tuple[dict, dict]:
    visibility = build_sample_visibility_event()
    visibility["event_id"] = "event_redacted_0000"
    visibility["workflow_role"] = workflow_role
    audit = build_live_event_audit_record(visibility, content="api_key=abc 123456789012345678 " + "x" * 200)
    routing = build_live_event_routing_report(audit)
    routing["agent_route_candidate"] = agent
    return audit, routing


def response_for(agent: str, workflow_role: str) -> dict:
    audit, routing = audit_and_routing(agent, workflow_role)
    return build_agent_placeholder_response(audit, routing)


def test_marin_placeholder() -> None:
    assert_true(response_for("marin", "marketing_intake")["placeholder"]["title"] == "Marin placeholder draft intake", "Marin template should be selected")


def test_lucy_placeholder() -> None:
    assert_true(response_for("lucy", "senior_review")["placeholder"]["title"] == "Lucy placeholder review", "Lucy template should be selected")


def test_kasumi_placeholder() -> None:
    assert_true(response_for("kasumi", "operation_intake")["placeholder"]["title"] == "Kasumi placeholder research intake", "Kasumi template should be selected")


def test_meiko_placeholder() -> None:
    assert_true(response_for("meiko", "senior_operation_review")["placeholder"]["title"] == "Meiko placeholder operation review", "Meiko template should be selected")


def test_reze_placeholder() -> None:
    assert_true(response_for("reze", "strategy_planning")["placeholder"]["title"] == "Reze placeholder strategy note", "Reze template should be selected")


def test_decision_maker_placeholder() -> None:
    assert_true(response_for("decision_maker_review", "final_approval")["placeholder"]["title"] == "Decision maker placeholder review", "Decision maker template should be selected")


def test_unrouted_placeholder() -> None:
    assert_true(response_for("unknown", "unknown")["agent_route_candidate"] == "unrouted", "Unknown agent should become unrouted")


def test_safety_flags() -> None:
    response = response_for("marin", "marketing_intake")
    assert_true(response["deterministic"] is True, "Response should be deterministic")
    assert_true(response["llm_enabled"] is False, "LLM should be disabled")
    assert_true(response["rag_enabled"] is False, "RAG should be disabled")
    assert_true(response["will_send"] is False, "will_send should be false")
    assert_true(response["message_sent"] is False, "message_sent should be false")


def test_content_preview_redaction_and_limit() -> None:
    response = response_for("marin", "marketing_intake")
    preview = response["content_basis"]["content_preview"]
    assert_true(len(preview) <= 120, "Content preview should be capped")
    assert_true("abc" not in preview, "Secret-like value should be redacted")
    assert_true(not LONG_NUMBER_RE.search(json.dumps(response, ensure_ascii=False)), "Raw Discord-like IDs should be redacted")


def test_markdown_render() -> None:
    text = render_agent_placeholder_response_markdown(response_for("marin", "marketing_intake"))
    assert_true("# Agent Placeholder Response" in text, "Markdown should render")


def test_json_write() -> None:
    path = write_agent_placeholder_response(response_for("marin", "marketing_intake"), root=TEST_ROOT)
    assert_true(path.exists(), "Placeholder response JSON should be written")


def test_would_send_preview_links_placeholder() -> None:
    audit, routing = audit_and_routing("marin", "marketing_intake")
    response = build_agent_placeholder_response(audit, routing)
    preview = build_would_send_preview(audit, routing, response)
    assert_true(preview["agent_placeholder_response"]["available"] is True, "Preview should include placeholder summary")
    assert_true(preview["message_sent"] is False, "Preview should not send")


def test_review_packet_links_placeholder() -> None:
    audit, routing = audit_and_routing("marin", "marketing_intake")
    response = build_agent_placeholder_response(audit, routing)
    preview = build_would_send_preview(audit, routing, response)
    packet = build_live_event_review_packet(audit, routing, preview, response)
    assert_true(packet["agent_placeholder_response"]["available"] is True, "Packet should include placeholder summary")
    assert_true(packet["safety_assertions"]["message_sent"] is False, "Packet should not send")


def test_operations_viewer_reads_placeholder_summary() -> None:
    audit, routing = audit_and_routing("marin", "marketing_intake")
    response = build_agent_placeholder_response(audit, routing)
    preview = build_would_send_preview(audit, routing, response)
    packet = build_live_event_review_packet(audit, routing, preview, response)
    write_live_event_review_packet(packet, root=TEST_ROOT)
    packets = list_recent_review_packets(TEST_ROOT)
    assert_true(any(item.get("agent_placeholder_response_available") for item in packets), "Viewer should expose placeholder availability")


def test_no_raw_token_or_id_leak() -> None:
    response = response_for("marin", "marketing_intake")
    assert_agent_placeholder_response_safe(response)
    text = json.dumps(response, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Token markers should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def main() -> int:
    tests = [
        test_marin_placeholder,
        test_lucy_placeholder,
        test_kasumi_placeholder,
        test_meiko_placeholder,
        test_reze_placeholder,
        test_decision_maker_placeholder,
        test_unrouted_placeholder,
        test_safety_flags,
        test_content_preview_redaction_and_limit,
        test_markdown_render,
        test_json_write,
        test_would_send_preview_links_placeholder,
        test_review_packet_links_placeholder,
        test_operations_viewer_reads_placeholder_summary,
        test_no_raw_token_or_id_leak,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All agent placeholder response tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
