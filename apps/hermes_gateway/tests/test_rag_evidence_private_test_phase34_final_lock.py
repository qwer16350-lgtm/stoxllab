"""Phase 34M final lock tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_private_test_phase34_final_lock.py
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

from rag_evidence_private_test_e2e_live_closeout import build_success_fixture
from rag_evidence_private_test_phase34_final_lock import (
    build_rag_evidence_private_test_phase34_final_lock,
    render_rag_evidence_private_test_phase34_final_lock_markdown,
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


def bad_closeout(mutator):
    report = build_success_fixture()
    mutator(report)
    return report


def test_final_lock_builder_returns_success_fixture() -> None:
    report = build_rag_evidence_private_test_phase34_final_lock()
    assert_true(report["phase34_private_test_mvp_complete"] is True, "MVP should be complete")
    assert_true(report["phase34m_final_lock_passed"] is True, "Final lock should pass")


def test_final_lock_passes_when_closeout_and_retry_succeeded() -> None:
    report = build_rag_evidence_private_test_phase34_final_lock()
    assert_true(report["e2e_live_reply_closeout"]["closeout_passed"] is True, "Closeout should pass")
    assert_true(report["no_llm_send_retry_closeout"]["discord_message_sent"] is True, "Retry sent should be true")


def test_final_lock_fails_if_llm_count_not_one() -> None:
    assert_raises(lambda: build_rag_evidence_private_test_phase34_final_lock(closeout=bad_closeout(lambda r: r.update({"llm_api_call_count": 2}))), "LLM count mismatch should fail")


def test_final_lock_fails_if_send_retry_llm_count_not_zero() -> None:
    def mutate(report: dict) -> None:
        report["no_llm_send_retry"]["llm_recall_allowed"] = True
        report["no_llm_send_retry"]["llm_api_call_count"] = 1

    assert_raises(lambda: build_rag_evidence_private_test_phase34_final_lock(closeout=bad_closeout(mutate)), "Retry LLM count should fail")


def test_final_lock_fails_if_final_discord_message_count_not_one() -> None:
    def mutate(report: dict) -> None:
        report["no_llm_send_retry"]["message_sent_count"] = 0
        report["final_result"]["message_sent_count"] = 0

    assert_raises(lambda: build_rag_evidence_private_test_phase34_final_lock(closeout=bad_closeout(mutate)), "Final count 0 should fail")


def test_final_lock_fails_if_scope_not_private_test() -> None:
    assert_raises(lambda: build_rag_evidence_private_test_phase34_final_lock(closeout=bad_closeout(lambda r: r["no_llm_send_retry"].update({"sent_channel_scope": "team"}))), "Team scope should fail")


def test_final_lock_fails_if_public_team_allowed() -> None:
    report = build_rag_evidence_private_test_phase34_final_lock()
    report["final_safety_state"]["public_channel_send_allowed"] = True
    assert_raises(lambda: _raise_if_unsafe(report), "Mutated unsafe public send should fail")


def _raise_if_unsafe(report: dict) -> None:
    from rag_evidence_private_test_phase34_final_lock import assert_rag_evidence_private_test_phase34_final_lock_safe

    assert_rag_evidence_private_test_phase34_final_lock_safe(report)


def test_final_lock_fails_if_unattended_auto_reply_true() -> None:
    assert_raises(lambda: build_rag_evidence_private_test_phase34_final_lock(closeout=bad_closeout(lambda r: r["final_result"].update({"ready_for_unattended_auto_reply": True}))), "Unattended true should fail")


def test_final_lock_confirms_embedding_external_false() -> None:
    report = build_rag_evidence_private_test_phase34_final_lock()
    assert_true(report["final_safety_state"]["embedding_api_called"] is False, "Embedding false")
    assert_true(report["final_safety_state"]["external_execution"] is False, "External false")


def test_final_lock_confirms_operation_not_operations() -> None:
    report = build_rag_evidence_private_test_phase34_final_lock()
    boundary = report["local_knowledge_boundary"]
    assert_true("operation" in boundary["canonical_sources"], "operation should be canonical")
    assert_true("operations" in boundary["forbidden_sources"], "operations should be forbidden")


def test_final_lock_requires_future_manual_approvals() -> None:
    report = build_rag_evidence_private_test_phase34_final_lock()
    assert_true(report["manual_gates_required_for_future_live_runs"] is True, "Future manual gates should be required")
    assert_true(report["default_runtime_sends_disabled"] is True, "Default sends should be disabled")


def test_sensitive_values_not_logged() -> None:
    report = build_rag_evidence_private_test_phase34_final_lock()
    text = json.dumps(report, ensure_ascii=False)
    assert_true("sk-" not in text.lower() and "xoxb-" not in text.lower(), "Secret markers should be absent")
    assert_true("I_APPROVE_" not in text, "Approval phrase values should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_phase34_final_lock_markdown(build_rag_evidence_private_test_phase34_final_lock())
    assert_true("Phase 34 Final Lock" in markdown, "Markdown should render")
    assert_true("Final lock passed: true" in markdown, "Markdown should show pass")


def main() -> int:
    tests = [
        test_final_lock_builder_returns_success_fixture,
        test_final_lock_passes_when_closeout_and_retry_succeeded,
        test_final_lock_fails_if_llm_count_not_one,
        test_final_lock_fails_if_send_retry_llm_count_not_zero,
        test_final_lock_fails_if_final_discord_message_count_not_one,
        test_final_lock_fails_if_scope_not_private_test,
        test_final_lock_fails_if_public_team_allowed,
        test_final_lock_fails_if_unattended_auto_reply_true,
        test_final_lock_confirms_embedding_external_false,
        test_final_lock_confirms_operation_not_operations,
        test_final_lock_requires_future_manual_approvals,
        test_sensitive_values_not_logged,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 34 final lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
