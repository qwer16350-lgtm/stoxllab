from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from one_shot_llm_draft_output_safety_rehearsal import (
    build_one_shot_llm_draft_output_safety_rehearsal,
    check_mock_output_safety,
    render_one_shot_llm_draft_output_safety_rehearsal_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")
BASE_PACKET = {
    "mock_response_created": True,
    "mock_response_review_only": True,
    "evidence_citations": ["knowledge/operation/stoxl_operation_tone_sample.md"],
    "mock_response_text": "Review-only draft. No external action has been taken.",
    "full_content_included": False,
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_rehearsal_success_fixture() -> None:
    report = build_one_shot_llm_draft_output_safety_rehearsal()
    assert_true(report["output_safety_rehearsal_available"] is True, "Rehearsal available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["input_mock_packet_available"] is True, "Input mock available")
    assert_true(report["ready_for_phase36c_actual_llm_call_preflight"] is True, "Phase 36C preflight ready")


def test_rehearsal_never_calls_or_sends() -> None:
    report = build_one_shot_llm_draft_output_safety_rehearsal()
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_call_count"] == 0, "LLM count zero")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["discord_api_send_called"] is False, "No Discord send API")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external")


def test_kasumi_output_safety_allowed() -> None:
    result = build_one_shot_llm_draft_output_safety_rehearsal()["agent_safety_results"]["kasumi"]
    assert_true(result["mock_response_created"] is True, "Kasumi mock created")
    assert_true(result["output_safety_checked"] is True, "Checked")
    assert_true(result["output_safety_allowed"] is True, "Allowed")
    assert_true(result["blocked_reasons"] == [], "No blocks")
    assert_true(result["ready_for_actual_llm_call"] is False, "Actual LLM false")
    assert_true(result["ready_for_discord_send"] is False, "Discord false")


def test_negative_fixtures() -> None:
    report = build_one_shot_llm_draft_output_safety_rehearsal()
    negative = report["negative_fixtures"]
    for key in (
        "secret_value_present_blocks",
        "approval_phrase_present_blocks",
        "raw_discord_id_present_blocks",
        "public_team_send_instruction_blocks",
        "unattended_auto_reply_instruction_blocks",
        "full_content_included_blocks",
    ):
        assert_true(negative[key] is True, f"{key} true")
    assert_true(report["negative_fixtures_passed"] is True, "Negative fixtures passed")


def test_direct_negative_checks() -> None:
    cases = [
        ("secret", dict(BASE_PACKET, mock_response_text="Review-only draft with api key: sk-test-secret")),
        ("approval", dict(BASE_PACKET, mock_response_text="Review-only draft I_APPROVE_TEST_VALUE")),
        ("discord_id", dict(BASE_PACKET, mock_response_text="Review-only draft 123456789012345678")),
        ("public", dict(BASE_PACKET, mock_response_text="Review-only draft. Send to public team channel.")),
        ("unattended", dict(BASE_PACKET, mock_response_text="Review-only draft. Use unattended auto reply.")),
        ("full", dict(BASE_PACKET, full_content_included=True)),
    ]
    for _name, packet in cases:
        assert_true(check_mock_output_safety(packet)["output_safety_allowed"] is False, "Negative case blocks")


def test_no_sensitive_values() -> None:
    text = json.dumps(build_one_shot_llm_draft_output_safety_rehearsal(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    assert_true("Output Safety Rehearsal" in render_one_shot_llm_draft_output_safety_rehearsal_markdown(build_one_shot_llm_draft_output_safety_rehearsal()), "Markdown")


def main() -> int:
    tests = [
        test_rehearsal_success_fixture,
        test_rehearsal_never_calls_or_sends,
        test_kasumi_output_safety_allowed,
        test_negative_fixtures,
        test_direct_negative_checks,
        test_no_sensitive_values,
        test_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All one-shot LLM draft output safety rehearsal tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
