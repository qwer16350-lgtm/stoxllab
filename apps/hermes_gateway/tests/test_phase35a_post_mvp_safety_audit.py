"""Phase 35A post-MVP safety audit tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_phase35a_post_mvp_safety_audit.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase35a_post_mvp_safety_audit import (
    assert_phase35a_post_mvp_safety_audit_safe,
    build_phase35a_post_mvp_safety_audit,
    render_phase35a_post_mvp_safety_audit_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")
DOCS = APP_DIR.parents[1] / "docs"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def test_builder_returns_success_fixture() -> None:
    report = build_phase35a_post_mvp_safety_audit()
    assert_true(report["phase35a_audit_passed"] is True, "Audit should pass")
    assert_true(report["ready_for_phase35_entry_planning"] is True, "Entry planning should be ready")


def test_counts_and_scope_locked() -> None:
    report = build_phase35a_post_mvp_safety_audit()
    counts = report["final_e2e_counts"]
    assert_true(counts["total_llm_call_count"] == 1, "Total LLM count should be 1")
    assert_true(counts["send_retry_llm_call_count"] == 0, "Retry LLM count should be 0")
    assert_true(counts["final_discord_message_sent_count"] == 1, "Final sent count should be 1")
    assert_true(counts["sent_channel_scope"] == "private_test_only", "Scope should be private-test only")


def test_gate_blocked_and_disabled_states() -> None:
    report = build_phase35a_post_mvp_safety_audit()
    assert_true(not any(report["default_gate_state"].values()), "All default gates should be off")
    assert_true(not any(report["blocked_scopes"].values()), "All blocked scopes should be false")
    assert_true(not any(report["disabled_capabilities"].values()), "All disabled capabilities should be false")


def test_audit_fails_if_public_team_allowed() -> None:
    report = build_phase35a_post_mvp_safety_audit()
    report["blocked_scopes"]["public_channel_reply_allowed"] = True
    assert_raises(lambda: assert_phase35a_post_mvp_safety_audit_safe(report), "Public reply true should fail")


def test_audit_fails_if_unattended_auto_reply_true() -> None:
    report = build_phase35a_post_mvp_safety_audit()
    report["blocked_scopes"]["unattended_auto_reply_allowed"] = True
    assert_raises(lambda: assert_phase35a_post_mvp_safety_audit_safe(report), "Unattended true should fail")


def test_audit_fails_if_embedding_vector_external_true() -> None:
    for key in ("embedding_api_called", "vector_index_created", "external_execution"):
        report = build_phase35a_post_mvp_safety_audit()
        report["disabled_capabilities"][key] = True
        assert_raises(lambda report=report: assert_phase35a_post_mvp_safety_audit_safe(report), f"{key} true should fail")


def test_audit_fails_if_manual_future_approval_false() -> None:
    report = build_phase35a_post_mvp_safety_audit()
    report["manual_controls"]["future_live_runs_require_manual_approval"] = False
    assert_raises(lambda: assert_phase35a_post_mvp_safety_audit_safe(report), "Manual approval false should fail")


def test_operation_canonical_operations_forbidden() -> None:
    report = build_phase35a_post_mvp_safety_audit()
    assert_true("operation" in report["source_policy"]["canonical_sources"], "operation should be canonical")
    assert_true("operations" in report["source_policy"]["forbidden_sources"], "operations should be forbidden")


def test_sensitive_values_not_logged() -> None:
    report = build_phase35a_post_mvp_safety_audit()
    text = json.dumps(report, ensure_ascii=False)
    assert_true("sk-" not in text.lower() and "xoxb-" not in text.lower(), "Secret markers should be absent")
    assert_true("I_APPROVE_" not in text, "Approval phrase values should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_phase35a_post_mvp_safety_audit_markdown(build_phase35a_post_mvp_safety_audit())
    assert_true("Post-MVP Safety Audit" in markdown, "Markdown should render")
    assert_true("Audit passed: true" in markdown, "Markdown should show pass")


def test_docs_contain_runbook_and_entry_plan() -> None:
    runbook = (DOCS / "STOXL_HERMES_OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")
    plan = (DOCS / "STOXL_PHASE35_ENTRY_PLAN.md").read_text(encoding="utf-8")
    assert_true("Emergency Gate Off" in runbook, "Runbook should include emergency gate off")
    assert_true("HERMES_DISCORD_SEND_MESSAGES" in runbook, "Runbook should include send gate")
    assert_true("Allowed Next Work" in plan, "Plan should include allowed work")
    assert_true("Hold" in plan and "Forbidden" in plan, "Plan should classify hold and forbidden")


def main() -> int:
    tests = [
        test_builder_returns_success_fixture,
        test_counts_and_scope_locked,
        test_gate_blocked_and_disabled_states,
        test_audit_fails_if_public_team_allowed,
        test_audit_fails_if_unattended_auto_reply_true,
        test_audit_fails_if_embedding_vector_external_true,
        test_audit_fails_if_manual_future_approval_false,
        test_operation_canonical_operations_forbidden,
        test_sensitive_values_not_logged,
        test_markdown_render,
        test_docs_contain_runbook_and_entry_plan,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 35A post-MVP safety audit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
