"""Phase 32C-LIVE LLM response packet closeout tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_response_packet_live_closeout.py
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

from llm_dry_call import write_llm_dry_call_artifact
from llm_response_packet import (
    build_latest_llm_response_packet_report,
    build_llm_response_packet,
    build_llm_response_packet_live_closeout,
    find_latest_llm_dry_call_artifact,
)
from operations_packet_viewer import build_operations_packet_viewer_report


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def live_success_report(created_at: str = "2026-06-13T01:02:03+00:00") -> dict:
    return {
        "report_type": "llm_dry_call_report",
        "version": "phase32b_private_test_only_no_discord_send",
        "created_at": created_at,
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
            "api_call_attempted": True,
            "api_call_succeeded": True,
            "api_call_failed": False,
            "response_text": "Review-only draft. No final publishing or external delivery has been made.",
            "usage": {
                "input_chars": 100,
                "output_chars": 72,
                "estimated_cost_krw": 0.001,
                "provider_usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 15,
                    "total_tokens": 35,
                },
            },
            "safety_assertions": {
                "api_key_value_logged": False,
                "discord_message_sent": False,
                "rag_called": False,
                "external_execution": False,
                "raw_discord_ids_logged": False,
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
        "safety_assertions": {
            "llm_api_called_only_when_explicitly_enabled": True,
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def blocked_report() -> dict:
    report = live_success_report("2026-06-13T01:03:03+00:00")
    report["client_result"]["response_text"] = "I posted it on SNS."
    report["output_safety"] = {
        "allowed": False,
        "blocked": True,
        "blocked_reasons": ["public_publish_claim"],
        "safe_disclaimer_detected": False,
        "safe_disclaimer_reasons": [],
    }
    return report


def test_unique_live_dry_call_artifact_written() -> None:
    with tempfile.TemporaryDirectory() as temp:
        result = write_llm_dry_call_artifact(live_success_report(), root=temp)
        paths = result["artifact_paths"]
        assert_true(paths[0].endswith("_openrouter_openai-gpt-5.4-mini.json"), "Artifact filename should include provider and model")
        assert_true(Path(paths[0]).exists(), "JSON artifact should exist")
        assert_true(Path(paths[1]).exists(), "Markdown artifact should exist")


def test_find_latest_live_dry_call_artifact() -> None:
    with tempfile.TemporaryDirectory() as temp:
        write_llm_dry_call_artifact(live_success_report("2026-06-13T01:00:00+00:00"), root=temp)
        write_llm_dry_call_artifact(live_success_report("2026-06-13T02:00:00+00:00"), root=temp)
        latest = find_latest_llm_dry_call_artifact(temp)
        assert_true(latest["found"] is True, "Latest dry call artifact should be found")
        assert_true(latest["created_at"] == "2026-06-13T02:00:00+00:00", "Latest created_at should win")


def test_latest_artifact_builds_response_packet() -> None:
    with tempfile.TemporaryDirectory() as temp:
        write_llm_dry_call_artifact(live_success_report(), root=temp)
        report = build_latest_llm_response_packet_report(temp)
        assert_true(report["latest_dry_call_found"] is True, "Latest artifact should be used")
        assert_true(report["packet_created"] is True, "Response packet should be created")
        assert_true(report["packet"]["output_safety"]["allowed"] is True, "Output safety should remain allowed")


def test_operations_viewer_reads_latest_llm_packet() -> None:
    with tempfile.TemporaryDirectory() as temp:
        write_llm_dry_call_artifact(live_success_report(), root=temp)
        build_latest_llm_response_packet_report(temp)
        viewer = build_operations_packet_viewer_report(temp, date="20260613")
        latest = viewer["latest_llm_response_packet"]
        assert_true(latest["available"] is True, "Operations viewer should expose latest LLM packet")
        assert_true(latest["provider"] == "openrouter", "Provider should be visible")
        assert_true(latest["message_sent"] is False, "Viewer must keep message_sent false")


def test_live_closeout_summary_safe_and_ready() -> None:
    with tempfile.TemporaryDirectory() as temp:
        write_llm_dry_call_artifact(live_success_report(), root=temp)
        closeout = build_llm_response_packet_live_closeout(temp)
        assert_true(closeout["latest_dry_call_found"] is True, "Closeout should find latest artifact")
        assert_true(closeout["llm_response_packet_created"] is True, "Closeout should create response packet")
        assert_true(closeout["ready_for_phase32d_guarded_private_test_llm_reply"] is True, "Closeout should be ready for guarded next phase")
        assert_true(closeout["message_sent"] is False, "Closeout must not send messages")
        assert_true(closeout["rag_called"] is False, "Closeout must not call RAG")
        assert_true(closeout["external_execution"] is False, "Closeout must not execute externally")


def test_blocked_output_packet_not_available() -> None:
    packet = build_llm_response_packet(blocked_report())
    assert_true(packet["output_safety"]["blocked"] is True, "Blocked output should be preserved")
    assert_true(packet["response_available"] is False, "Blocked output should not be available for reply")
    assert_true(packet["message_sent"] is False, "Blocked packet must not send")


def test_no_secret_or_raw_discord_id_logged() -> None:
    with tempfile.TemporaryDirectory() as temp:
        report = live_success_report()
        report["client_result"]["response_text"] = "Review-only draft. token=abc 123456789012345678"
        write_llm_dry_call_artifact(report, root=temp)
        closeout = build_llm_response_packet_live_closeout(temp)
        text = json.dumps(closeout, ensure_ascii=False).lower()
        assert_true("token=abc" not in text and "sk-" not in text, "Secret-like values should be absent")
        assert_true(not LONG_ID_RE.search(text), "Raw Discord-like IDs should be absent")


def test_no_discord_api_or_rag_flags() -> None:
    with tempfile.TemporaryDirectory() as temp:
        write_llm_dry_call_artifact(live_success_report(), root=temp)
        closeout = build_llm_response_packet_live_closeout(temp)
        assert_true(closeout["discord_send_attempted"] is False, "Discord send should not be attempted")
        assert_true(closeout["safety_assertions"]["discord_message_sent"] is False, "Discord message sent assertion should be false")
        assert_true(closeout["safety_assertions"]["rag_called"] is False, "RAG assertion should be false")


def main() -> int:
    tests = [
        test_unique_live_dry_call_artifact_written,
        test_find_latest_live_dry_call_artifact,
        test_latest_artifact_builds_response_packet,
        test_operations_viewer_reads_latest_llm_packet,
        test_live_closeout_summary_safe_and_ready,
        test_blocked_output_packet_not_available,
        test_no_secret_or_raw_discord_id_logged,
        test_no_discord_api_or_rag_flags,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM response packet live closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
