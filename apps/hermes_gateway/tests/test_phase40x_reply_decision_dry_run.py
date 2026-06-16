from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40w_synthetic_private_test_replay import build_synthetic_event
from phase40x_reply_decision_dry_run import build_phase40x_reply_decision_dry_run


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_private_test_human_would_reply() -> None:
    report = build_phase40x_reply_decision_dry_run(build_synthetic_event())
    assert_true(report["would_reply"] is True, "Would reply")
    assert_true(report["reply_payload_frozen"] is True, "Payload frozen")
    assert_true(report["ready_for_phase41_preflight_gate"] is True, "Ready for gate")


def test_negative_fixtures_do_not_reply() -> None:
    cases = [
        build_synthetic_event(author_type="self", is_self=True),
        build_synthetic_event(author_type="bot", is_bot=True),
        build_synthetic_event(is_duplicate=True),
        build_synthetic_event(channel_scope="public"),
        build_synthetic_event(channel_scope="team"),
    ]
    for event in cases:
        report = build_phase40x_reply_decision_dry_run(event)
        assert_true(report["would_reply"] is False, "Blocked")
        assert_true(report["reply_payload_frozen"] is False, "No payload")


def test_no_actual_send_or_llm_rag_external() -> None:
    report = build_phase40x_reply_decision_dry_run()
    for key in ("actual_send_allowed", "discord_api_send_called", "discord_message_sent", "llm_called", "llm_api_call_attempted", "rag_called", "external_execution", "ready_for_actual_reply_send"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No messages")


def main() -> int:
    for test in (test_private_test_human_would_reply, test_negative_fixtures_do_not_reply, test_no_actual_send_or_llm_rag_external):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40X reply decision dry-run tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
