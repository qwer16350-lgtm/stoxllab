"""Local Discord adapter stub tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_discord_adapter_stub.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from discord_adapter_stub import load_raw_events, normalize_discord_raw_event, run_discord_adapter_stub


ROOT = APP_DIR.parents[1]
EVENTS = ROOT / "apps" / "hermes_gateway" / "examples" / "discord_raw_event_stub.example.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def events() -> list[dict]:
    return load_raw_events(EVENTS)


def run(index: int) -> dict:
    return run_discord_adapter_stub(events()[index], root=ROOT)


def test_raw_event_normalize() -> None:
    normalized = normalize_discord_raw_event(events()[0])
    assert_true(normalized["text"], "Raw event should normalize text")
    assert_true(normalized["source_channel"] == "marin-초안", "Raw event should normalize channel")


def test_sns_draft_agent_dispatch() -> None:
    result = run(0)
    payload = result["would_send_payload"]
    assert_true(payload["message_kind"] == "agent_dispatch", "SNS draft should create agent_dispatch payload")
    assert_true(payload["safety"]["message_sent"] is False, "Message must not be sent")


def test_sns_publish_approval_flow() -> None:
    result = run(1)
    payload = result["would_send_payload"]
    assert_true(payload["message_kind"] in {"approval_required", "blocked_request"}, "SNS publish should require approval or be blocked")


def test_grant_submit_human_only_blocked() -> None:
    result = run(2)
    plan = result["dispatch_plan"]
    assert_true(plan["blocked"] is True, "Grant submit should be blocked")
    assert_true(plan["human_only_execution"] is True, "Grant submit should remain human-only")


def test_api_key_blocked_request() -> None:
    result = run(4)
    payload = result["would_send_payload"]
    assert_true(payload["message_kind"] == "blocked_request", "API key request should be blocked")


def test_safety_flags_false() -> None:
    result = run(0)
    safety = result["safety"]
    payload_safety = result["would_send_payload"]["safety"]
    assert_true(safety["discord_api_called"] is False, "Discord API must not be called")
    assert_true(safety["gateway_connected"] is False, "Gateway must not connect")
    assert_true(payload_safety["message_sent"] is False, "Message must not be sent")
    assert_true(payload_safety["external_execution"] is False, "External execution must remain false")


def test_secret_not_in_payload_content() -> None:
    result = run(4)
    content = json.dumps(result["would_send_payload"], ensure_ascii=False).lower()
    assert_true("api key 보여줘" not in content, "Secret request content should be redacted from would-send payload")


def main() -> int:
    tests = [
        test_raw_event_normalize,
        test_sns_draft_agent_dispatch,
        test_sns_publish_approval_flow,
        test_grant_submit_human_only_blocked,
        test_api_key_blocked_request,
        test_safety_flags_false,
        test_secret_not_in_payload_content,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Discord adapter stub tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
