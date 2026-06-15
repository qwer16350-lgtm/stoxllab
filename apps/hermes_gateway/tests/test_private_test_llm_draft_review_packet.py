from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_llm_draft_review_packet import build_private_test_llm_draft_review_packet, render_private_test_llm_draft_review_packet_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_review_packet_success_fixture() -> None:
    report = build_private_test_llm_draft_review_packet()
    assert_true(report["review_packet_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase36f_no_send_final_lock_passed"] is True, "36F source")
    assert_true(report["draft_review_packet_created"] is True, "Packet created")
    assert_true(report["human_review_required"] is True, "Human review")
    assert_true(report["ready_for_private_test_send_preflight_preview"] is True, "Ready for preview")


def test_review_packet_scope_and_no_execution() -> None:
    report = build_private_test_llm_draft_review_packet()
    assert_true(report["agent"] == "kasumi", "Kasumi only")
    assert_true(report["allowed_sources"] == ["operation"], "Operation only")
    assert_true(report["evidence_citations"] == ["knowledge/operation/stoxl_operation_tone_sample.md"], "Citation")
    assert_true(report["response_preview_only"] is True, "Preview only")
    assert_true(report["full_content_included"] is False, "No full content")
    assert_true(report["new_llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["new_llm_api_called"] is False, "No LLM call")
    assert_true(report["discord_api_send_called"] is False, "No Discord API")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["message_sent_count"] == 0, "No message")
    assert_true(report["ready_for_discord_send"] is False, "No send ready")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_review_packet_no_sensitive_values_and_markdown() -> None:
    report = build_private_test_llm_draft_review_packet()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("LLM Draft Review Packet" in render_private_test_llm_draft_review_packet_markdown(report), "Markdown")


def main() -> int:
    tests = [test_review_packet_success_fixture, test_review_packet_scope_and_no_execution, test_review_packet_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test LLM draft review packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
