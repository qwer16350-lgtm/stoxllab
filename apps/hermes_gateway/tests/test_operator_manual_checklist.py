from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from operator_manual_checklist import build_operator_manual_checklist, render_operator_manual_checklist_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_operator_manual_checklist_success_fixture() -> None:
    report = build_operator_manual_checklist()
    assert_true(report["checklist_available"] is True, "Checklist available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["human_review_required"] is True, "Human review")
    assert_true(report["approval_phrase_generated"] is False, "No phrase")
    assert_true(report["approval_phrase_value_logged"] is False, "No phrase value")


def test_operator_manual_checklist_readiness_false() -> None:
    report = build_operator_manual_checklist()
    for key in ("ready_for_actual_approval", "ready_for_live_runtime", "ready_for_llm_call", "ready_for_discord_send", "ready_for_unattended_auto_reply"):
        assert_true(report[key] is False, f"{key} false")


def test_operator_manual_checklist_no_sensitive_values() -> None:
    text = json.dumps(build_operator_manual_checklist(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_operator_manual_checklist_markdown() -> None:
    assert_true("Operator Manual Checklist" in render_operator_manual_checklist_markdown(build_operator_manual_checklist()), "Markdown")


def main() -> int:
    tests = [
        test_operator_manual_checklist_success_fixture,
        test_operator_manual_checklist_readiness_false,
        test_operator_manual_checklist_no_sensitive_values,
        test_operator_manual_checklist_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All operator manual checklist tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
