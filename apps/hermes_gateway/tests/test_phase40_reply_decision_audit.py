from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_reply_decision_audit import build_phase40_reply_decision_audit, render_phase40_reply_decision_audit_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40d_reply_decisions() -> None:
    report = build_phase40_reply_decision_audit()
    assert_true(report["private_test_human_message_decision"] == "eligible_for_future_manual_reply", "Human future eligible")
    assert_true(report["self_message_decision"] == "skip_self_message", "Self skipped")
    assert_true(report["bot_message_decision"] == "skip_bot_message", "Bot skipped")
    assert_true(report["duplicate_message_decision"] == "skip_duplicate_message", "Duplicate skipped")
    assert_true(report["public_channel_decision"] == "block_public_channel", "Public blocked")
    assert_true(report["team_channel_decision"] == "block_team_channel", "Team blocked")


def test_phase40d_no_generation_or_send() -> None:
    report = build_phase40_reply_decision_audit()
    for key in ("reply_text_generated", "llm_called", "rag_called", "external_execution", "discord_api_send_called", "discord_message_sent"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase40d_markdown() -> None:
    assert_true("Phase 40D" in render_phase40_reply_decision_audit_markdown(build_phase40_reply_decision_audit()), "Markdown")


def main() -> int:
    for test in (test_phase40d_reply_decisions, test_phase40d_no_generation_or_send, test_phase40d_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40D reply decision audit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
