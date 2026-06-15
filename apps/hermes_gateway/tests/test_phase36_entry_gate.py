from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase36_entry_gate import build_phase36_entry_gate, render_phase36_entry_gate_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase36_entry_gate_success_fixture() -> None:
    report = build_phase36_entry_gate()
    assert_true(report["phase36_entry_gate_available"] is True, "Entry gate available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase36_not_started"] is True, "Phase 36 not started")
    assert_true(report["requires_explicit_user_approval"] is True, "Explicit approval required")
    assert_true(report["dashboard_lock_available"] is True, "Dashboard lock available")
    assert_true(report["forbidden_behavior_sentinel_passed"] is True, "Sentinel passed")


def test_phase36_entry_gate_readiness_false() -> None:
    report = build_phase36_entry_gate()
    for key in ("ready_for_phase36_live_execution", "ready_for_llm_call", "ready_for_discord_send", "ready_for_embedding", "ready_for_external_sources", "ready_for_unattended_auto_reply"):
        assert_true(report[key] is False, f"{key} false")


def test_phase36_entry_gate_candidate_groups() -> None:
    report = build_phase36_entry_gate()
    assert_true("private_test_one_shot_llm_draft_preflight_no_send" in report["allowed_next_candidates"], "Allowed preflight no send")
    assert_true("private_test_multi_turn_runtime" in report["hold_candidates"], "Hold multi-turn")
    assert_true("public_team_auto_reply" in report["forbidden_candidates"], "Forbid public/team")


def test_phase36_entry_gate_no_sensitive_values() -> None:
    text = json.dumps(build_phase36_entry_gate(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_phase36_entry_gate_markdown() -> None:
    assert_true("Phase 36 Entry Gate" in render_phase36_entry_gate_markdown(build_phase36_entry_gate()), "Markdown")


def main() -> int:
    tests = [
        test_phase36_entry_gate_success_fixture,
        test_phase36_entry_gate_readiness_false,
        test_phase36_entry_gate_candidate_groups,
        test_phase36_entry_gate_no_sensitive_values,
        test_phase36_entry_gate_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 36 entry gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
