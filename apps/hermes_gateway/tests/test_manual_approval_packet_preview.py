from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from manual_approval_packet_preview import build_manual_approval_packet_preview, render_manual_approval_packet_preview_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_approval_preview_success_fixture() -> None:
    report = build_manual_approval_packet_preview()
    assert_true(report["approval_packet_preview_available"] is True, "Preview available")
    assert_true(report["rule_only"] is True, "Rule only")
    assert_true(report["approval_phrase_generated"] is False, "No phrase generated")
    assert_true(report["approval_phrase_value_logged"] is False, "No phrase logged")
    assert_true(report["human_review_required"] is True, "Human review required")
    assert_true(report["ready_for_actual_approval"] is False, "No actual approval readiness")


def test_approval_preview_readiness_false() -> None:
    report = build_manual_approval_packet_preview()
    for key in ("ready_for_llm_call", "ready_for_discord_send", "ready_for_embedding", "ready_for_external_sources", "ready_for_unattended_auto_reply"):
        assert_true(report[key] is False, f"{key} false")


def test_agent_preview_gates() -> None:
    previews = build_manual_approval_packet_preview()["approval_packet_previews"]
    assert_true(previews["kasumi"]["review_packet_ready"] is True, "Kasumi review packet ready")
    assert_true(previews["kasumi"]["approval_scope"] == "private_test_only", "Kasumi private-test scope")
    assert_true(previews["kasumi"]["allowed_future_action"] == "one_private_test_review_only_llm_draft", "Kasumi future action preview")
    assert_true(previews["marin"]["review_packet_ready"] is False, "Marin not ready")
    assert_true(previews["marin"]["approval_scope"] == "none", "Marin no scope")
    for preview in previews.values():
        assert_true(preview["discord_send_allowed"] is False, "No Discord send allowed")
        assert_true(preview["llm_call_allowed"] is False, "No LLM call allowed")
        assert_true(preview["approval_phrase_generated"] is False, "No phrase generated")


def test_sensitive_values_not_logged() -> None:
    text = json.dumps(build_manual_approval_packet_preview(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    markdown = render_manual_approval_packet_preview_markdown(build_manual_approval_packet_preview())
    assert_true("Manual Approval Packet Preview" in markdown, "Markdown renders")


def main() -> int:
    tests = [
        test_approval_preview_success_fixture,
        test_approval_preview_readiness_false,
        test_agent_preview_gates,
        test_sensitive_values_not_logged,
        test_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All manual approval packet preview tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
