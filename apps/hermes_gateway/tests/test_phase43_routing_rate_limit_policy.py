from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase43_routing_rate_limit_policy import build_phase43_routing_rate_limit_policy, evaluate_phase43_rate_limit, evaluate_phase43_routing_policy


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_routing_policy() -> None:
    assert_true(evaluate_phase43_routing_policy({"channel_scope": "private_test", "author_type": "human"})["private_test_human_eligible"] is True, "Private human eligible")
    assert_true(evaluate_phase43_routing_policy({"author_type": "self"})["self_ignored"] is True, "Self ignored")
    assert_true(evaluate_phase43_routing_policy({"author_type": "bot"})["bot_ignored"] is True, "Bot ignored")
    assert_true(evaluate_phase43_routing_policy({"duplicate": True})["duplicate_ignored"] is True, "Duplicate ignored")
    assert_true(evaluate_phase43_routing_policy({"channel_scope": "team"})["public_team_not_eligible_for_send"] is True, "Team blocked")


def test_rate_limit_policy() -> None:
    assert_true(evaluate_phase43_rate_limit(replies_sent=0, max_replies=1, phase41b_repeat_locked=False, manual_gate_open=True)["rate_limit_allows_reply"] is True, "Allowed by policy")
    assert_true(evaluate_phase43_rate_limit(replies_sent=1, max_replies=1)["rate_limit_allows_reply"] is False, "Max blocks")
    assert_true(evaluate_phase43_rate_limit(cooldown_active=True)["rate_limit_allows_reply"] is False, "Cooldown blocks")
    assert_true(evaluate_phase43_rate_limit(one_shot_lock_consumed=True)["rate_limit_allows_reply"] is False, "Lock blocks")
    assert_true(evaluate_phase43_rate_limit(phase41b_repeat_locked=True, manual_gate_open=True)["rate_limit_allows_reply"] is False, "Phase 41B repeat lock blocks")
    assert_true(evaluate_phase43_rate_limit(phase41b_repeat_locked=False, manual_gate_open=False)["rate_limit_allows_reply"] is False, "Manual gate blocks")


def test_phase43_report_syncs_phase42_locks() -> None:
    report = build_phase43_routing_rate_limit_policy()
    assert_true(report["phase41b_repeat_send_locked"] is True, "Phase 41B repeat locked")
    assert_true(report["phase42_actual_supervised_session_succeeded"] is True, "Phase 42 success")
    assert_true(report["phase42_message_sent_count"] == 1, "Phase 42 one message")
    assert_true(report["phase42_sent_scope"] == "private_test_only", "Phase 42 private-test")
    assert_true(report["phase42_repeat_supervised_session_locked"] is True, "Phase 42 repeat locked")
    assert_true(report["phase42_repeat_supervised_session_allowed"] is False, "Phase 42 repeat disallowed")
    assert_true(report["phase42_manual_gate_required"] is True, "Phase 42 manual gate")
    assert_true(report["phase42_manual_gate_open"] is False, "Phase 42 gate closed")
    assert_true(report["phase42_session_lock_active"] is True, "Session lock")
    assert_true(report["phase42_max_session_messages_enforced"] is True, "Session max")
    assert_true(report["phase42_max_send_count_enforced"] is True, "Send max")
    assert_true(report["ready_for_phase41b_repeat_send"] is False, "No Phase 41B repeat")
    assert_true(report["ready_for_phase42_actual_supervised_session"] is False, "No Phase 42 actual")
    assert_true(report["ready_for_phase42_repeat_supervised_session"] is False, "No Phase 42 repeat")
    assert_true(report["public_team_blocked"] is True, "Public/team blocked")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")


def main() -> int:
    for test in (test_routing_policy, test_rate_limit_policy, test_phase43_report_syncs_phase42_locks):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 43 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
