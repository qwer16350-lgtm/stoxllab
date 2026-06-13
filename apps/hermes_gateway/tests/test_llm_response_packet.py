"""Phase 32C LLM response packet integration tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_response_packet.py
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from live_event_audit_persistence import build_live_event_audit_record, build_sample_visibility_event
from live_event_review_packet import build_live_event_review_packet
from live_event_routing_report import build_live_event_routing_report
from llm_response_packet import (
    assert_llm_response_packet_safe,
    build_llm_response_packet,
    build_llm_response_summary,
    render_llm_response_packet_markdown,
    write_llm_response_packet,
)
from operations_packet_viewer import build_operations_packet_viewer_report
from would_send_preview import build_would_send_preview


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def allowed_dry_report(response_text: str = "Review-only draft. No final publishing or external delivery has been made.") -> dict:
    return {
        "report_type": "llm_dry_call_report",
        "version": "phase32b_private_test_only_no_discord_send",
        "request": {
            "agent_route_candidate": "marin",
            "channel_scope": "private_test_only",
            "allow_api_call": True,
            "discord_send_enabled": False,
            "rag_enabled": False,
            "external_execution": False,
        },
        "client_result": {
            "provider": "openrouter",
            "model": "openai/gpt-5.4-mini",
            "response_text": response_text,
            "usage": {
                "input_chars": 120,
                "output_chars": len(response_text),
                "estimated_cost_krw": 0.00043425,
                "provider_usage": {"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
            },
        },
        "output_safety": {
            "allowed": True,
            "blocked": False,
            "blocked_reasons": [],
            "safe_disclaimer_detected": True,
            "safe_disclaimer_reasons": ["review_only", "negated_action_made"],
        },
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
    }


def blocked_dry_report() -> dict:
    report = allowed_dry_report("")
    report["output_safety"] = {"allowed": False, "blocked": True, "blocked_reasons": ["empty_output"]}
    return report


def test_allowed_report_builds_packet() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    assert_true(packet["packet_type"] == "llm_response_packet", "Packet should be created")
    assert_true(packet["output_safety"]["allowed"] is True, "Allowed safety result should be preserved")


def test_blocked_output_packet_send_disallowed() -> None:
    packet = build_llm_response_packet(blocked_dry_report())
    assert_true(packet["output_safety"]["blocked"] is True, "Blocked safety result should be preserved")
    assert_true(packet["message_sent"] is False and packet["discord_send_attempted"] is False, "Blocked packet must not send")


def test_response_summary_created() -> None:
    summary = build_llm_response_summary(allowed_dry_report())
    assert_true(summary["char_count"] > 0, "Summary should include char count")
    assert_true(summary["review_only"] is True, "Summary should mark review-only")


def test_provider_model_preserved() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    assert_true(packet["provider"] == "openrouter", "Provider should be preserved")
    assert_true(packet["model"] == "openai/gpt-5.4-mini", "Model should be preserved")


def test_usage_cost_preserved() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    assert_true(packet["usage"]["prompt_tokens"] == 10, "Prompt tokens should be preserved")
    assert_true(packet["usage"]["cost"] == 0.00043425, "Cost should be preserved")


def test_human_review_required() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    assert_true(packet["human_review"]["required"] is True, "Human review should be required")


def test_disallowed_auto_reply_present() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    assert_true("auto_reply" in packet["human_review"]["disallowed_actions"], "Auto reply should be disallowed")


def test_execution_flags_false() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    assert_true(packet["message_sent"] is False, "Message sent should be false")
    assert_true(packet["discord_send_attempted"] is False, "Discord send attempted should be false")
    assert_true(packet["rag_called"] is False, "RAG should be false")
    assert_true(packet["external_execution"] is False, "External execution should be false")


def test_no_api_key_or_raw_discord_id_logged() -> None:
    packet = build_llm_response_packet(allowed_dry_report("token=abc 123456789012345678 Review-only draft."))
    text = json.dumps(packet, ensure_ascii=False).lower()
    assert_true("token=abc" not in text and "sk-" not in text, "Token-like values should be redacted")
    assert_true(not LONG_ID_RE.search(text), "Raw Discord-like IDs should be absent")
    assert_llm_response_packet_safe(packet)


def test_markdown_render_possible() -> None:
    markdown = render_llm_response_packet_markdown(build_llm_response_packet(allowed_dry_report()))
    assert_true("# LLM Response Packet" in markdown, "Markdown should render")


def test_json_write_possible() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    with tempfile.TemporaryDirectory() as temp:
        paths = write_llm_response_packet(packet, root=temp)
        assert_true(Path(paths["json_path"]).exists(), "JSON packet should be written")
        assert_true(Path(paths["markdown_path"]).exists(), "Markdown packet should be written")


def live_context() -> tuple[dict, dict]:
    visibility = build_sample_visibility_event()
    visibility["event_id"] = "event_redacted_0000"
    audit = build_live_event_audit_record(visibility, content="hello")
    routing = build_live_event_routing_report(audit)
    return audit, routing


def test_would_send_preview_llm_summary_connected() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    audit, routing = live_context()
    preview = build_would_send_preview(audit, routing, llm_response_packet=packet)
    assert_true(preview["llm_response"]["available"] is True, "Would-send preview should include LLM response summary")
    assert_true(preview["llm_response"]["will_send"] is False, "LLM response would-send should stay false")


def test_live_event_review_packet_llm_summary_connected() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    audit, routing = live_context()
    preview = build_would_send_preview(audit, routing, llm_response_packet=packet)
    review = build_live_event_review_packet(audit, routing, preview, llm_response_packet=packet)
    assert_true(review["llm_response_packet"]["available"] is True, "Review packet should include LLM response packet summary")
    assert_true(review["safety_assertions"]["message_sent"] is False, "Review packet should not send")


def test_operations_viewer_reads_llm_summary() -> None:
    packet = build_llm_response_packet(allowed_dry_report())
    with tempfile.TemporaryDirectory() as temp:
        write_llm_response_packet(packet, root=temp)
        report = build_operations_packet_viewer_report(temp, date=packet["created_at"][:10].replace("-", ""))
        assert_true(report["llm_response_summary"]["llm_response_available"] is True, "Operations viewer should read LLM summary")
        assert_true(report["llm_response_summary"]["llm_message_sent"] is False, "Operations viewer should keep sent false")


def main() -> int:
    tests = [
        test_allowed_report_builds_packet,
        test_blocked_output_packet_send_disallowed,
        test_response_summary_created,
        test_provider_model_preserved,
        test_usage_cost_preserved,
        test_human_review_required,
        test_disallowed_auto_reply_present,
        test_execution_flags_false,
        test_no_api_key_or_raw_discord_id_logged,
        test_markdown_render_possible,
        test_json_write_possible,
        test_would_send_preview_llm_summary_connected,
        test_live_event_review_packet_llm_summary_connected,
        test_operations_viewer_reads_llm_summary,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM response packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
