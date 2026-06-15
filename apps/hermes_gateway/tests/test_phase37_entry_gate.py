from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase37_entry_gate import build_phase37_entry_gate, render_phase37_entry_gate_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase37_entry_gate_success_fixture() -> None:
    report = build_phase37_entry_gate()
    assert_true(report["phase37_entry_gate_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase37_not_started"] is True, "Not started")
    assert_true(report["requires_explicit_user_approval"] is True, "Requires approval")
    assert_true(report["source_phase36f_no_send_final_lock_passed"] is True, "36F source")


def test_phase37_candidates_and_readiness() -> None:
    report = build_phase37_entry_gate()
    assert_true("private_test_llm_draft_review_packet_no_send" in report["allowed_next_candidates"], "Review packet allowed")
    assert_true("private_test_discord_send_preflight_no_send" in report["allowed_next_candidates"], "Send preflight allowed")
    assert_true("actual_private_test_discord_send" in report["hold_candidates"], "Actual send hold")
    assert_true("multi_turn_private_test_runtime" in report["hold_candidates"], "Runtime hold")
    for candidate in ("public_team_send", "public_team_auto_reply", "unattended_auto_reply", "external_execution"):
        assert_true(candidate in report["forbidden_candidates"], f"{candidate} forbidden")
    assert_true(report["ready_for_phase37_live_execution"] is False, "No live")
    assert_true(report["ready_for_discord_send"] is False, "No send")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase37_no_execution_or_sensitive_values() -> None:
    report = build_phase37_entry_gate()
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_called"] is False, "No LLM call")
    assert_true(report["discord_live_runtime_executed"] is False, "No Discord runtime")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external")
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_phase37_markdown() -> None:
    assert_true("Phase 37 Entry Gate" in render_phase37_entry_gate_markdown(build_phase37_entry_gate()), "Markdown")


def main() -> int:
    tests = [
        test_phase37_entry_gate_success_fixture,
        test_phase37_candidates_and_readiness,
        test_phase37_no_execution_or_sensitive_values,
        test_phase37_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 37 entry gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
