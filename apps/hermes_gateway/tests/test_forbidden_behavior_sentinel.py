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
    assert_true(report["phase39c_actual_discord_send_count_locked"] == 1, "39C locked count")
    assert_true(report["phase39c_no_repeat_lock_active"] is True, "39C no-repeat active")
    assert_true(report["phase40_actual_discord_send_count_locked"] == 1, "40 locked count")
    assert_true(report["phase40_additional_discord_send_count"] == 0, "40 no additional send")
    assert_true(report["phase40_message_sent_count"] == 0, "40 no message count")
    assert_true(report["phase40_synthetic_replay_only"] is True, "40 synthetic replay")
    assert_true(report["phase40_duplicate_message_id_guard"] is True, "40 duplicate guard")


def test_forbidden_behavior_sentinel_flags_false() -> None:
    report = build_forbidden_behavior_sentinel()
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated"):
        assert_true(report[key] is False, f"{key} false")


def test_forbidden_behavior_sentinel_negative_fixtures() -> None:
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated", "discord_api_send_called", "actual_private_test_send_executed", "actual_send_implementation_executed", "new_llm_api_call_attempted", "new_llm_api_called", "llm_api_call_attempted", "llm_api_called", "discord_live_runtime_executed", "ready_for_discord_send", "ready_for_actual_private_test_send", "ready_for_phase37d_actual_private_test_send", "ready_for_phase38_actual_private_test_send_path", "ready_for_phase39_live_execution", "ready_for_phase39b_manual_one_shot_send", "ready_for_phase39b_actual_send_manual_attempt", "ready_for_phase39c_send_closeout", "actual_discord_api_send_called", "actual_discord_message_sent", "api_key_value_logged", "token_value_logged", "discord_token_value_logged", "private_test_channel_id_value_logged", "raw_discord_ids_logged", "approval_phrase_value_logged", "additional_discord_send_called_in_phase39c", "additional_discord_message_sent_in_phase39c", "phase39c_repeat_send_allowed", "phase39c_automatic_retry_allowed", "phase39c_manual_retry_allowed", "phase39c_ready_for_repeat_send", "phase40_live_runtime_started", "phase40_discord_gateway_connected", "phase40_discord_api_send_called", "phase40_discord_message_sent", "phase40_repeat_send_allowed", "phase40_automatic_retry_allowed", "phase40_unattended_auto_reply_allowed", "phase40_public_channel_send_allowed", "phase40_team_channel_send_allowed", "phase40_public_channel_reply_allowed", "phase40_team_channel_reply_allowed", "phase40_llm_api_call_attempted", "phase40_llm_api_called", "phase40_rag_called", "phase40_embedding_api_called", "phase40_vector_index_created", "phase40_external_execution", "phase40_secret_values_logged", "phase40_ready_for_live_runtime_execution"):
        assert_raises(lambda selected=key: build_forbidden_behavior_sentinel({selected: True}), f"{key} should fail")


def test_forbidden_behavior_sentinel_actual_message_count_fixture() -> None:
    assert_raises(lambda: build_forbidden_behavior_sentinel({"actual_message_sent_count": 1}), "Actual message count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"actual_discord_send_count": 1}), "Actual Discord send count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"additional_message_sent_count_in_phase39c": 1}), "Phase 39C additional count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_actual_discord_send_count_locked": 2}), "Phase 40 count should stay 1")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_additional_discord_send_count": 1}), "Phase 40 additional count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_message_sent_count": 1}), "Phase 40 message count should fail")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_synthetic_replay_only": False}), "Phase 40 synthetic replay required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40_duplicate_message_id_guard": False}), "Phase 40 duplicate guard required")


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
