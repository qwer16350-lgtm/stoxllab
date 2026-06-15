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
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated", "discord_api_send_called", "actual_private_test_send_executed", "actual_send_implementation_executed", "new_llm_api_call_attempted", "new_llm_api_called", "llm_api_call_attempted", "llm_api_called", "discord_live_runtime_executed", "ready_for_discord_send", "ready_for_actual_private_test_send", "ready_for_phase37d_actual_private_test_send", "ready_for_phase38_actual_private_test_send_path", "ready_for_phase39_live_execution", "ready_for_phase39b_manual_one_shot_send", "ready_for_phase39b_actual_send_manual_attempt", "ready_for_phase39c_send_closeout", "actual_discord_api_send_called", "actual_discord_message_sent", "api_key_value_logged", "token_value_logged", "discord_token_value_logged", "private_test_channel_id_value_logged", "raw_discord_ids_logged", "approval_phrase_value_logged"):
        assert_raises(lambda selected=key: build_forbidden_behavior_sentinel({selected: True}), f"{key} should fail")


def test_forbidden_behavior_sentinel_actual_message_count_fixture() -> None:
    assert_raises(lambda: build_forbidden_behavior_sentinel({"actual_message_sent_count": 1}), "Actual message count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"actual_discord_send_count": 1}), "Actual Discord send count should fail")


def test_forbidden_behavior_sentinel_post_llm_call_fixtures() -> None:
    ok = build_forbidden_behavior_sentinel({"post_llm_call_sentinel": True})
    assert_true(ok["total_phase36_llm_call_count"] == 1, "Post LLM count")
    assert_true(ok["total_phase36_discord_message_sent_count"] == 0, "Post Discord count")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"post_llm_call_sentinel": True, "total_phase36_llm_call_count": 2}), "LLM count >1 should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"post_llm_call_sentinel": True, "total_phase36_discord_message_sent_count": 1}), "Discord count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"post_llm_call_sentinel": True, "phase36_discord_message_sent": True}), "Discord sent should fail")


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
        test_forbidden_behavior_sentinel_actual_message_count_fixture,
        test_forbidden_behavior_sentinel_post_llm_call_fixtures,
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
