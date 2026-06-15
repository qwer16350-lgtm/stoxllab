from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_one_shot_llm_draft_mock_packet import build_private_test_one_shot_llm_draft_mock_packet, render_private_test_one_shot_llm_draft_mock_packet_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_mock_packet_success_fixture() -> None:
    report = build_private_test_one_shot_llm_draft_mock_packet()
    assert_true(report["mock_packet_available"] is True, "Mock packet available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase36_live_execution_started"] is False, "No live execution")
    assert_true(report["source_preflight"] == "phase36a_private_test_one_shot_llm_draft_preflight_no_call_no_send", "Source preflight")


def test_mock_packet_never_calls_or_sends() -> None:
    report = build_private_test_one_shot_llm_draft_mock_packet()
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_call_count"] == 0, "LLM count zero")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["discord_api_send_called"] is False, "No Discord send API")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")


def test_mock_packet_readiness_false() -> None:
    report = build_private_test_one_shot_llm_draft_mock_packet()
    for key in ("approval_phrase_generated", "approval_phrase_value_logged", "manual_approval_actualized", "ready_for_actual_llm_call", "ready_for_discord_send", "ready_for_unattended_auto_reply"):
        assert_true(report[key] is False, f"{key} false")


def test_kasumi_mock_response_created() -> None:
    packets = build_private_test_one_shot_llm_draft_mock_packet()["mock_draft_packets"]
    kasumi = packets["kasumi"]
    assert_true(kasumi["candidate_from_preflight"] is True, "Kasumi candidate")
    assert_true(kasumi["mock_response_created"] is True, "Kasumi mock created")
    assert_true(kasumi["mock_response_review_only"] is True, "Review only")
    assert_true(kasumi["allowed_sources"] == ["operation"], "Operation only")
    assert_true(kasumi["evidence_citations"] == ["knowledge/operation/stoxl_operation_tone_sample.md"], "Relative citation")
    assert_true(kasumi["full_content_included"] is False, "No full content")
    assert_true(kasumi["ready_for_output_safety_rehearsal"] is True, "Ready for rehearsal")
    assert_true(kasumi["ready_for_actual_llm_call"] is False, "Actual LLM false")


def test_marin_mock_response_not_created() -> None:
    marin = build_private_test_one_shot_llm_draft_mock_packet()["mock_draft_packets"]["marin"]
    assert_true(marin["candidate_from_preflight"] is False, "Marin not candidate")
    assert_true(marin["mock_response_created"] is False, "Marin no mock")
    assert_true(marin["blocked_reason"] == "not_preflight_candidate", "Blocked reason")


def test_no_sensitive_values() -> None:
    text = json.dumps(build_private_test_one_shot_llm_draft_mock_packet(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    assert_true("Draft Mock Packet" in render_private_test_one_shot_llm_draft_mock_packet_markdown(build_private_test_one_shot_llm_draft_mock_packet()), "Markdown")


def main() -> int:
    tests = [
        test_mock_packet_success_fixture,
        test_mock_packet_never_calls_or_sends,
        test_mock_packet_readiness_false,
        test_kasumi_mock_response_created,
        test_marin_mock_response_not_created,
        test_no_sensitive_values,
        test_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test one-shot LLM draft mock packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
