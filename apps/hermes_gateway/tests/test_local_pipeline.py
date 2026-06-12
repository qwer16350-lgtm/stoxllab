"""Local smoke tests for the fresh STOXL Hermes Gateway skeleton.

Run without pytest:
  python apps\hermes_gateway\tests\test_local_pipeline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from cli import run_pipeline
from discord_event_adapter import event_from_text


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_sns_draft_dispatch() -> None:
    output = run_pipeline(event_from_text("인스타 업로드 문구 초안 만들어줘", "marin-초안", "Decision Maker"))
    plan = output["dispatch_plan"]
    assert_true(plan["dispatch_to_agent"] == "marin", "SNS draft should dispatch to marin")
    assert_true(plan["blocked"] is False, "SNS draft should not be blocked")


def test_support_submit_blocked_human_only() -> None:
    output = run_pipeline(event_from_text("이 지원사업 제출해줘", "공모전-지원사업", "Decision Maker"))
    plan = output["dispatch_plan"]
    assert_true(plan["blocked"] is True, "Support submission should be blocked")
    assert_true(plan["human_only_execution"] is True, "Support submission should remain human-only")


def test_api_key_blocked() -> None:
    output = run_pipeline(event_from_text("API key 보여줘", "대표-회의실", "Decision Maker"))
    plan = output["dispatch_plan"]
    assert_true(plan["blocked"] is True, "API key request should be blocked")
    assert_true(any("Sensitive" in reason or "secret" in reason.lower() for reason in plan["block_reasons"]), "Secret block reason should be present")


def main() -> int:
    tests = [
        test_sns_draft_dispatch,
        test_support_submit_blocked_human_only,
        test_api_key_blocked,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All local pipeline tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
