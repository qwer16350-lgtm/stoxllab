from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from forbidden_behavior_sentinel import build_forbidden_behavior_sentinel, render_forbidden_behavior_sentinel_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def test_forbidden_behavior_sentinel_success_fixture() -> None:
    report = build_forbidden_behavior_sentinel()
    assert_true(report["sentinel_available"] is True, "Sentinel available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["forbidden_behavior_sentinel_passed"] is True, "Sentinel passed")
    assert_true(report["public_team_blocked"] is True, "Public/team blocked")
    assert_true(report["embedding_vector_disabled"] is True, "Embedding/vector disabled")


def test_forbidden_behavior_sentinel_flags_false() -> None:
    report = build_forbidden_behavior_sentinel()
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated"):
        assert_true(report[key] is False, f"{key} false")


def test_forbidden_behavior_sentinel_negative_fixtures() -> None:
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated", "api_key_value_logged"):
        assert_raises(lambda selected=key: build_forbidden_behavior_sentinel({selected: True}), f"{key} should fail")


def test_forbidden_behavior_sentinel_no_sensitive_values() -> None:
    text = json.dumps(build_forbidden_behavior_sentinel(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_forbidden_behavior_sentinel_markdown() -> None:
    assert_true("Forbidden Behavior Sentinel" in render_forbidden_behavior_sentinel_markdown(build_forbidden_behavior_sentinel()), "Markdown")


def main() -> int:
    tests = [
        test_forbidden_behavior_sentinel_success_fixture,
        test_forbidden_behavior_sentinel_flags_false,
        test_forbidden_behavior_sentinel_negative_fixtures,
        test_forbidden_behavior_sentinel_no_sensitive_values,
        test_forbidden_behavior_sentinel_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All forbidden behavior sentinel tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
