from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase43_routing_rate_limit_policy import evaluate_phase43_rate_limit, evaluate_phase43_routing_policy


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
    assert_true(evaluate_phase43_rate_limit(replies_sent=0, max_replies=1)["rate_limit_allows_reply"] is True, "Allowed by policy")
    assert_true(evaluate_phase43_rate_limit(replies_sent=1, max_replies=1)["rate_limit_allows_reply"] is False, "Max blocks")
    assert_true(evaluate_phase43_rate_limit(cooldown_active=True)["rate_limit_allows_reply"] is False, "Cooldown blocks")
    assert_true(evaluate_phase43_rate_limit(one_shot_lock_consumed=True)["rate_limit_allows_reply"] is False, "Lock blocks")


def main() -> int:
    for test in (test_routing_policy, test_rate_limit_policy):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 43 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
