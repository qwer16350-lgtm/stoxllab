"""Phase 34L-2 E2E live closeout tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_private_test_e2e_live_closeout.py
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_private_test_e2e_live_closeout import (
    build_rag_evidence_private_test_e2e_live_closeout,
    build_success_fixture,
    render_rag_evidence_private_test_e2e_live_closeout_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def bad_report(mutator):
    report = build_success_fixture()
    mutator(report)
    return report


def test_closeout_builder_returns_success_fixture() -> None:
    report = build_rag_evidence_private_test_e2e_live_closeout()
    assert_true(report["report_type"] == "rag_evidence_private_test_e2e_live_closeout", "Report type should match")
    assert_true(report["closeout_passed"] is True, "Closeout should pass")
    assert_true(report["final_result"]["ready_for_phase34m_final_lock"] is True, "Phase 34M should be ready")


def test_closeout_passes_for_llm_one_and_no_llm_retry_success() -> None:
    report = build_rag_evidence_private_test_e2e_live_closeout()
    assert_true(report["llm_api_call_count"] == 1, "Total LLM count should be 1")
    assert_true(report["no_llm_send_retry"]["llm_api_call_count"] == 0, "Retry LLM count should be 0")
    assert_true(report["no_llm_send_retry"]["discord_message_sent"] is True, "Retry sent should be true")
    assert_true(report["final_result"]["message_sent_count"] == 1, "Final sent count should be 1")


def test_closeout_fails_if_total_llm_count_not_one() -> None:
    assert_raises(lambda: build_rag_evidence_private_test_e2e_live_closeout(bad_report(lambda r: r.update({"llm_api_call_count": 2}))), "LLM count 2 should fail")


def test_closeout_fails_if_send_retry_calls_llm() -> None:
    def mutate(report: dict) -> None:
        report["no_llm_send_retry"]["llm_api_called"] = True
        report["no_llm_send_retry"]["llm_api_call_count"] = 1

    assert_raises(lambda: build_rag_evidence_private_test_e2e_live_closeout(bad_report(mutate)), "Retry LLM call should fail")


def test_closeout_fails_if_final_message_count_not_one() -> None:
    assert_raises(lambda: build_rag_evidence_private_test_e2e_live_closeout(bad_report(lambda r: r["final_result"].update({"message_sent_count": 2}))), "Final sent count 2 should fail")


def test_closeout_fails_if_sent_scope_not_private_test() -> None:
    assert_raises(lambda: build_rag_evidence_private_test_e2e_live_closeout(bad_report(lambda r: r["final_result"].update({"sent_channel_scope": "public"}))), "Public sent scope should fail")


def test_closeout_fails_if_output_safety_not_allowed() -> None:
    assert_raises(lambda: build_rag_evidence_private_test_e2e_live_closeout(bad_report(lambda r: r.update({"output_safety_allowed": False}))), "Output safety false should fail")


def test_closeout_fails_if_public_team_channel_called() -> None:
    for key in ("public_channel_reply_called", "team_channel_reply_called", "public_channel_send_called", "team_channel_send_called"):
        assert_raises(lambda key=key: build_rag_evidence_private_test_e2e_live_closeout(bad_report(lambda r, key=key: r["safety_assertions"].update({key: True}))), f"{key} should fail")


def test_closeout_fails_if_unattended_auto_reply_true() -> None:
    assert_raises(lambda: build_rag_evidence_private_test_e2e_live_closeout(bad_report(lambda r: r["final_result"].update({"ready_for_unattended_auto_reply": True}))), "Unattended true should fail")


def test_closeout_confirms_no_embedding_external() -> None:
    report = build_rag_evidence_private_test_e2e_live_closeout()
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external execution")
    assert_true(report["safety_assertions"]["embedding_called"] is False, "No embedding assertion")
    assert_true(report["safety_assertions"]["external_execution"] is False, "No external assertion")


def test_sensitive_values_not_logged() -> None:
    report = build_rag_evidence_private_test_e2e_live_closeout()
    text = json.dumps(report, ensure_ascii=False)
    assert_true("sk-" not in text.lower() and "xoxb-" not in text.lower(), "Secret markers should be absent")
    assert_true("I_APPROVE_" not in text, "Approval phrase values should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_e2e_live_closeout_markdown(build_rag_evidence_private_test_e2e_live_closeout())
    assert_true("E2E Live Closeout" in markdown, "Markdown should render")
    assert_true("Closeout passed: true" in markdown, "Markdown should show pass")


def main() -> int:
    tests = [
        test_closeout_builder_returns_success_fixture,
        test_closeout_passes_for_llm_one_and_no_llm_retry_success,
        test_closeout_fails_if_total_llm_count_not_one,
        test_closeout_fails_if_send_retry_calls_llm,
        test_closeout_fails_if_final_message_count_not_one,
        test_closeout_fails_if_sent_scope_not_private_test,
        test_closeout_fails_if_output_safety_not_allowed,
        test_closeout_fails_if_public_team_channel_called,
        test_closeout_fails_if_unattended_auto_reply_true,
        test_closeout_confirms_no_embedding_external,
        test_sensitive_values_not_logged,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence private-test E2E live closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
