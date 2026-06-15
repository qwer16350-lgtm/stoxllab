from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from operations_dashboard_lock import build_operations_dashboard_lock, render_operations_dashboard_lock_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_operations_dashboard_lock_success_fixture() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["dashboard_lock_available"] is True, "Dashboard lock available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase34_private_test_mvp_complete"] is True, "MVP complete")
    assert_true(report["phase35a_safety_audit_passed"] is True, "35A passed")
    assert_true(report["phase35b_dry_previews_available"] is True, "35B available")
    assert_true(report["phase35c_agent_prompt_previews_available"] is True, "35C available")
    assert_true(report["phase35d_review_approval_previews_available"] is True, "35D available")
    assert_true(report["phase35e_operator_rehearsal_available"] is True, "35E available")


def test_operations_dashboard_lock_final_counts() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["total_llm_call_count"] == 1, "One total LLM call in final lock fixture")
    assert_true(report["send_retry_llm_call_count"] == 0, "No send retry LLM")
    assert_true(report["final_discord_message_sent_count"] == 1, "One final Discord message in final lock fixture")
    assert_true(report["sent_channel_scope"] == "private_test_only", "Private test only")


def test_operations_dashboard_lock_safety_false() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["current_live_gates_off"] is True, "Live gates off")
    assert_true(report["public_team_blocked"] is True, "Public/team blocked")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["embedding_vector_disabled"] is True, "No embedding/vector")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["ready_for_live_runtime"] is False, "No live readiness")


def test_operations_dashboard_lock_no_sensitive_values() -> None:
    text = json.dumps(build_operations_dashboard_lock(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_operations_dashboard_lock_markdown() -> None:
    assert_true("Operations Dashboard Lock" in render_operations_dashboard_lock_markdown(build_operations_dashboard_lock()), "Markdown")


def main() -> int:
    tests = [
        test_operations_dashboard_lock_success_fixture,
        test_operations_dashboard_lock_final_counts,
        test_operations_dashboard_lock_safety_false,
        test_operations_dashboard_lock_no_sensitive_values,
        test_operations_dashboard_lock_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All operations dashboard lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
