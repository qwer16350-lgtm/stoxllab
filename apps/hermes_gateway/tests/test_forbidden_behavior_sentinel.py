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
    assert_true(report["phase40j_readonly_preflight_available"] is True, "40J preflight")
    assert_true(report["phase40k_manual_launch_only"] is True, "40K manual")
    assert_true(report["phase40k_codex_must_not_launch"] is True, "40K codex no launch")
    assert_true(report["phase40l_capture_closeout_available"] is True, "40L closeout")
    assert_true(report["phase40m_manual_abort_available"] is True, "40M abort")
    assert_true(report["phase40n_phase41_reply_runtime_entry_gate_available"] is True, "40N gate")
    assert_true(report["phase40o_manual_launch_only"] is True, "40O manual")
    assert_true(report["phase40o_codex_must_not_launch"] is True, "40O codex no launch")
    assert_true(report["phase40p_capture_schema_available"] is True, "40P schema")
    assert_true(report["phase40r_phase41_reply_runtime_entry_available"] is True, "40R matrix")
    assert_true(report["phase40s_safe_to_review_next_morning"] is True, "40S safe")
    assert_true(report["phase40s_requires_user_confirmation"] is True, "40S confirmation")


def test_forbidden_behavior_sentinel_flags_false() -> None:
    report = build_forbidden_behavior_sentinel()
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated"):
        assert_true(report[key] is False, f"{key} false")


def test_forbidden_behavior_sentinel_negative_fixtures() -> None:
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "unattended_auto_reply_allowed", "scheduler_auto_reply_allowed", "embedding_api_called", "vector_index_created", "external_execution", "full_content_included", "approval_phrase_generated", "discord_api_send_called", "actual_private_test_send_executed", "actual_send_implementation_executed", "new_llm_api_call_attempted", "new_llm_api_called", "llm_api_call_attempted", "llm_api_called", "discord_live_runtime_executed", "ready_for_discord_send", "ready_for_actual_private_test_send", "ready_for_phase37d_actual_private_test_send", "ready_for_phase38_actual_private_test_send_path", "ready_for_phase39_live_execution", "ready_for_phase39b_manual_one_shot_send", "ready_for_phase39b_actual_send_manual_attempt", "ready_for_phase39c_send_closeout", "actual_discord_api_send_called", "actual_discord_message_sent", "api_key_value_logged", "token_value_logged", "discord_token_value_logged", "private_test_channel_id_value_logged", "raw_discord_ids_logged", "approval_phrase_value_logged", "additional_discord_send_called_in_phase39c", "additional_discord_message_sent_in_phase39c", "phase39c_repeat_send_allowed", "phase39c_automatic_retry_allowed", "phase39c_manual_retry_allowed", "phase39c_ready_for_repeat_send", "phase40_live_runtime_started", "phase40_discord_gateway_connected", "phase40_discord_api_send_called", "phase40_discord_message_sent", "phase40_repeat_send_allowed", "phase40_automatic_retry_allowed", "phase40_unattended_auto_reply_allowed", "phase40_public_channel_send_allowed", "phase40_team_channel_send_allowed", "phase40_public_channel_reply_allowed", "phase40_team_channel_reply_allowed", "phase40_llm_api_call_attempted", "phase40_llm_api_called", "phase40_rag_called", "phase40_embedding_api_called", "phase40_vector_index_created", "phase40_external_execution", "phase40_secret_values_logged", "phase40_ready_for_live_runtime_execution", "phase40j_live_runtime_started", "phase40j_discord_gateway_connected", "phase40j_ready_for_manual_readonly_runtime_launch", "phase40k_planned_command_executed_by_codex", "phase40k_live_runtime_started", "phase40k_discord_gateway_connected", "phase40l_live_capture_observed", "phase40m_discord_api_send_called", "phase40m_discord_message_sent", "phase40n_phase41_reply_runtime_allowed", "phase40n_reply_send_allowed", "phase40n_llm_reply_allowed", "phase40n_rag_reply_allowed", "phase40n_ready_for_phase41_reply_runtime", "phase40o_live_runtime_started", "phase40o_discord_gateway_connected", "phase40o_discord_api_send_called", "phase40o_discord_message_sent", "phase40o_ready_for_manual_readonly_runtime_launch", "phase40p_raw_content_logged", "phase40p_raw_discord_ids_logged", "phase40p_secret_values_logged", "phase40q_capture_review_completed", "phase40q_discord_api_send_called", "phase40q_discord_message_sent", "phase40q_ready_for_phase41_reply_runtime", "phase40r_phase41_reply_runtime_allowed", "phase40r_discord_reply_send_allowed", "phase40r_llm_reply_allowed", "phase40r_rag_reply_allowed", "phase40s_live_runtime_started_by_codex", "phase40s_overnight_external_actions_executed_by_codex", "phase40s_phase41_reply_runtime_allowed"):
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
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40j_readonly_preflight_available": False}), "Phase 40J preflight required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40k_manual_launch_only": False}), "Phase 40K manual only required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40k_codex_must_not_launch": False}), "Phase 40K Codex no-launch required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40l_capture_closeout_available": False}), "Phase 40L closeout required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40l_captured_event_count": 1}), "Phase 40L captured count must stay 0")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40m_manual_abort_available": False}), "Phase 40M abort required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40m_abort_on_any_send_attempt": False}), "Phase 40M send abort required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40n_phase41_reply_runtime_entry_gate_available": False}), "Phase 40N gate required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40o_manual_launch_only": False}), "Phase 40O manual launch required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40o_codex_must_not_launch": False}), "Phase 40O no launch required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40p_capture_schema_available": False}), "Phase 40P schema required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40q_message_sent_count": 1}), "Phase 40Q count 0 required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40r_phase41_reply_runtime_entry_available": False}), "Phase 40R matrix required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40s_safe_to_review_next_morning": False}), "Phase 40S safe review required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40s_requires_user_confirmation": False}), "Phase 40S confirmation required")
    assert_raises(lambda: build_forbidden_behavior_sentinel({"phase40s_additional_discord_send_count": 1}), "Phase 40S no additional send")


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
