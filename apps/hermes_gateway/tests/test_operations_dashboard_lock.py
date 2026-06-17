from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from operations_dashboard_lock import assert_operations_dashboard_lock_safe, build_operations_dashboard_lock, render_operations_dashboard_lock_markdown


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


def test_operations_dashboard_lock_success_fixture() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["dashboard_lock_available"] is True, "Dashboard lock available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase34_private_test_mvp_complete"] is True, "MVP complete")
    assert_true(report["phase35a_safety_audit_passed"] is True, "35A passed")
    assert_true(report["phase35b_dry_previews_available"] is True, "35B available")
    assert_true(report["phase35c_agent_prompt_previews_available"] is True, "35C available")
    assert_true(report["phase35d_review_approval_previews_available"] is True, "35D available")
    assert_true(report["phase35e_operator_rehearsal_available"] is True, "35E available")


def test_operations_dashboard_lock_final_counts() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["total_llm_call_count"] == 1, "One total LLM call in final lock fixture")
    assert_true(report["send_retry_llm_call_count"] == 0, "No send retry LLM")
    assert_true(report["final_discord_message_sent_count"] == 1, "One final Discord message in final lock fixture")
    assert_true(report["sent_channel_scope"] == "private_test_only", "Private test only")


def test_operations_dashboard_lock_safety_false() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["current_live_gates_off"] is True, "Live gates off")
    assert_true(report["public_team_blocked"] is True, "Public/team blocked")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["embedding_vector_disabled"] is True, "No embedding/vector")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["ready_for_live_runtime"] is False, "No live readiness")


def test_operations_dashboard_lock_phase41b_45a_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase41b_one_shot_available"] is True, "41B available")
    assert_true(report["phase41b_actual_runtime_path_available"] is True, "41B runtime path")
    assert_true(report["phase41b_actual_runtime_executed"] is False, "41B no runtime")
    assert_true(report["phase41b_real_discord_send_adapter_wired"] is True, "41B real adapter wired")
    assert_true(report["phase41b_fake_adapter_contract_passed"] is True, "41B fake contract")
    assert_true(report["phase41b_default_blocked"] is True, "41B blocked")
    assert_true(report["phase41b_message_sent_count"] == 0, "41B no send")
    assert_true(report["phase41c_closeout_available"] is True, "41C available")
    assert_true(report["phase41c_actual_private_test_reply_verified"] is True, "41C success observed")
    assert_true(report["phase41c_message_sent_count"] == 1, "41C observed count 1")
    assert_true(report["phase41c_sent_scope"] == "private_test_only", "41C private scope")
    assert_true(report["phase41c_repeat_send_blocked"] is True, "41C repeat locked")
    assert_true(report["phase41c_discord_api_send_called_during_phase41c"] is False, "41C no API")
    assert_true(report["phase41c_discord_message_sent_during_phase41c"] is False, "41C no message")
    assert_true(report["phase42_session_preflight_available"] is True, "42 available")
    assert_true(report["phase42_actual_runtime_cli_available"] is True, "42 actual CLI")
    assert_true(report["phase42_allow_flag_available"] is True, "42 allow flag")
    assert_true(report["phase42_runtime_default_blocked"] is True, "42 runtime default blocked")
    assert_true(report["phase42_runtime_allow_flag_present"] is False, "42 allow absent")
    assert_true(report["phase42_runtime_message_sent_count"] == 0, "42 runtime no send")
    assert_true(report["phase42_actual_session_closeout_available"] is True, "42 closeout")
    assert_true(report["phase42_actual_supervised_private_test_session_succeeded"] is True, "42 success")
    assert_true(report["phase42_exactly_once_supervised_success_recorded"] is True, "42 exactly once")
    assert_true(report["phase42_success_message_sent_count"] == 1, "42 observed one send")
    assert_true(report["phase42_success_sent_scope"] == "private_test_only", "42 private-test")
    assert_true(report["phase42_success_session_lock_consumed"] is True, "42 lock consumed")
    assert_true(report["phase42_repeat_supervised_session_locked"] is True, "42 repeat locked")
    assert_true(report["phase42_repeat_supervised_session_allowed"] is False, "42 repeat disallowed")
    assert_true(report["phase42_closeout_discord_api_send_called"] is False, "42 closeout no API")
    assert_true(report["phase42_closeout_discord_message_sent"] is False, "42 closeout no message")
    assert_true(report["phase42_closeout_additional_message_sent_count"] == 0, "42 closeout no extra send")
    assert_true(report["phase42_default_blocked"] is True, "42 default blocked")
    assert_true(report["phase42_blocked"] is True, "42 blocked")
    assert_true(report["phase42_manual_gate_required"] is True, "42 manual gate required")
    assert_true(report["phase42_manual_gate_open"] is False, "42 manual gate closed")
    assert_true(report["phase42_actual_supervised_session_executed"] is False, "42 no supervised session")
    assert_true(report["phase42_actual_runtime_executed"] is False, "42 no runtime")
    assert_true(report["phase42_ready_for_manual_supervised_session"] is False, "42 no manual readiness")
    assert_true(report["phase42_ready_for_phase41b_repeat_send"] is False, "42 no 41B repeat")
    assert_true(report["phase42_public_team_blocked"] is True, "42 public/team blocked")
    assert_true(report["phase42_session_lock_active"] is True, "42 session lock")
    assert_true(report["phase42_discord_api_send_called"] is False, "42 no API")
    assert_true(report["phase43_public_team_blocked"] is True, "43 public/team blocked")
    assert_true(report["phase43_phase41b_repeat_send_locked"] is True, "43 41B repeat locked")
    assert_true(report["phase43_phase42_repeat_supervised_session_locked"] is True, "43 42 repeat locked")
    assert_true(report["phase43_phase42_manual_gate_open"] is False, "43 42 gate closed")
    assert_true(report["phase43_ready_for_phase42_actual_supervised_session"] is False, "43 no 42 actual")
    assert_true(report["phase44_actual_llm_api_call"] is False, "44 no LLM")
    assert_true(report["phase44_fake_output_schema_valid"] is True, "44 fake valid")
    assert_true(report["phase45_ready_for_actual_llm_one_shot_call"] in {False, True}, "45 readiness is non-execution")
    assert_true(report["phase45_actual_llm_api_call"] is False, "45 no LLM")
    assert_true(report["phase45_actual_llm_api_call_attempted"] is False, "45 no LLM attempt alias")
    assert_true(report["phase45_actual_llm_api_called"] is False, "45 no LLM called alias")
    assert_true(report["phase45_llm_api_call_count"] == 0, "45 no LLM count")
    assert_true(report["phase45_actual_llm_call_closeout_available"] is True, "45 closeout available")
    assert_true(report["phase45_actual_llm_one_shot_completed"] is True, "45 actual LLM complete")
    assert_true(report["phase45_actual_llm_call_count"] == 1, "45 historical count one")
    assert_true(report["phase45_actual_llm_one_shot_repeat_locked"] is True, "45 repeat locked")
    assert_true(report["phase45_ready_for_repeat_llm_call"] is False, "45 repeat not ready")
    assert_true(report["phase45_output_safety_blocked"] is True, "45 output blocked")
    assert_true(report["phase45_llm_response_packet_created"] is False, "45 no packet")
    assert_true(report["phase45_closeout_discord_api_send_called"] is False, "45 closeout no API send")
    assert_true(report["phase45_closeout_discord_message_sent"] is False, "45 closeout no message")
    assert_true(report["phase45_closeout_message_sent_count"] == 0, "45 closeout message count 0")
    assert_true(report["phase46_blocked_llm_output_review_available"] is True, "46 review available")
    assert_true(report["phase46_metadata_only"] is True, "46 metadata only")
    assert_true(report["phase46_raw_output_included"] is False, "46 no raw output")
    assert_true(report["phase46_full_content_included"] is False, "46 no full content")
    assert_true(report["phase46_automatic_retry_allowed"] is False, "46 no auto retry")
    assert_true(report["phase46_retry_requires_new_manual_gate"] is True, "46 new manual gate")
    assert_true(report["phase46_llm_retry_policy_available"] is True, "46 retry policy")
    assert_true(report["phase46_repeat_phase45_call_allowed"] is False, "46 no repeat")
    assert_true(report["phase46_retry_requires_new_approval_phrase"] is True, "46 new phrase")
    assert_true(report["phase46_retry_requires_cost_guard"] is True, "46 cost guard")
    assert_true(report["phase46_retry_requires_call_count_guard"] is True, "46 count guard")
    assert_true(report["phase46_discord_send_remains_disabled"] is True, "46 Discord disabled")
    assert_true(report["phase46_llm_api_called"] is False, "46 no LLM")
    assert_true(report["phase46_discord_message_sent"] is False, "46 no Discord")
    assert_true(report["phase47_human_review_closeout_available"] is True, "47 closeout")
    assert_true(report["phase47_metadata_only"] is True, "47 metadata")
    assert_true(report["phase47_human_review_required"] is True, "47 human review")
    assert_true(report["phase47_phase45_llm_call_count"] == 1, "47 historical count")
    assert_true(report["phase47_output_safety_blocked"] is True, "47 blocked")
    assert_true(report["phase47_automatic_retry_allowed"] is False, "47 no auto retry")
    assert_true(report["phase47_automatic_send_allowed"] is False, "47 no auto send")
    assert_true(report["phase47_raw_output_included"] is False, "47 no raw")
    assert_true(report["phase47_retry_execution_available"] is False, "47 no retry execution")
    assert_true(report["phase47_disabled_retry_gate_design_available"] is True, "47 retry design")
    assert_true(report["phase47_retry_gate_implemented"] is False, "47 retry gate disabled")
    assert_true(report["phase47_manual_retry_requires_new_phase"] is True, "47 new phase")
    assert_true(report["phase47_manual_retry_requires_new_approval_phrase"] is True, "47 new phrase")
    assert_true(report["phase47_manual_retry_requires_cost_guard"] is True, "47 cost guard")
    assert_true(report["phase47_manual_retry_requires_call_count_guard"] is True, "47 count guard")
    assert_true(report["phase47_repeat_phase45_call_allowed"] is False, "47 no Phase45 repeat")
    assert_true(report["phase47_discord_send_remains_disabled"] is True, "47 Discord disabled")
    assert_true(report["phase48a_final_closeout_available"] is True, "48A final closeout")
    assert_true(report["phase48a_final_closeout_mode"] == "human_review_only", "48A human review")
    assert_true(report["phase48a_external_action_freeze_active"] is True, "48A freeze")


def test_operations_dashboard_lock_phase51_52_foundation_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase51_52_foundation_available"] is True, "51/52 available")
    assert_true(report["phase51_52_continuous_readonly_runtime_foundation_ready"] is True, "51/52 foundation ready")
    assert_true(report["phase51_52_current_automation_level"] == 1, "Automation level 1")
    assert_true(report["phase51_52_review_packet_base_ready"] is True, "Review packet ready")
    assert_true(report["phase51_52_ready_for_manual_gate_readonly_live_runtime"] is True, "Manual gate readiness")
    assert_true(report["phase51_52_manual_gate_needed_for_live_readonly_runtime"] is True, "Manual gate needed")
    assert_true(report["phase51_52_actual_discord_runtime_executed"] is False, "No Discord runtime")
    assert_true(report["phase51_52_discord_api_send_called"] is False, "No Discord send API")
    assert_true(report["phase51_52_discord_message_sent"] is False, "No Discord message")
    assert_true(report["phase51_52_actual_llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["phase51_52_actual_llm_api_called"] is False, "No LLM call")
    assert_true(report["phase51_52_rag_called"] is False, "No RAG")
    assert_true(report["phase51_52_embedding_api_called"] is False, "No embedding")
    assert_true(report["phase51_52_vector_index_created"] is False, "No vector")
    assert_true(report["phase51_52_external_execution"] is False, "No external")
    assert_true(report["phase51_52_scheduler_cron_live_execution"] is False, "No scheduler")
    assert_true(report["phase51_52_ready_for_auto_reply"] is False, "No auto reply")
    assert_true(report["phase51_52_readonly_live_runtime_preflight_available"] is True, "Live preflight available")
    assert_true(report["phase51_52_manual_runtime_gate_required"] is True, "Manual runtime gate")
    assert_true(report["phase51_52_manual_runtime_approval_phrase_defined"] is True, "Approval phrase defined")
    assert_true(report["phase51_52_manual_runtime_approval_phrase_value_logged"] is False, "Phrase hidden")
    assert_true(report["phase51_52_manual_runtime_live_runtime_started"] is False, "No manual runtime start")
    assert_true(report["phase51_52_manual_runtime_discord_message_sent"] is False, "No manual runtime message")
    assert_true(report["phase51_52_launch_packet_available"] is True, "Launch packet")
    assert_true(report["phase51_52_actual_runtime_command_available"] is True, "Runtime command")
    assert_true(report["phase52b_capture_closeout_available"] is True, "52B closeout available")
    assert_true(report["phase52b_manual_readonly_runtime_executed_once"] is True, "52B manual runtime observed")
    assert_true(report["phase52b_gateway_connection_verified"] is True, "52B gateway verified")
    assert_true(report["phase52b_captured_event_count"] == 0, "52B empty capture count")
    assert_true(report["phase52b_empty_capture_handled"] is True, "52B empty capture handled")
    assert_true(report["phase52b_capture_file_metadata_available"] is True, "52B metadata available")
    assert_true(report["phase52b_capture_file_read_attempted"] is False, "52B no capture read")
    assert_true(report["phase52b_capture_closeout_discord_api_send_called"] is False, "52B no API send")
    assert_true(report["phase52b_capture_closeout_discord_message_sent"] is False, "52B no message")
    assert_true(report["phase52b_capture_closeout_llm_api_called"] is False, "52B no LLM")
    assert_true(report["phase52b_capture_closeout_rag_called"] is False, "52B no RAG")
    assert_true(report["phase52b_capture_closeout_raw_content_logged"] is False, "52B no raw content")
    assert_true(report["phase52b_capture_closeout_raw_discord_ids_logged"] is False, "52B no raw IDs")
    assert_true(report["phase53_capture_to_review_packet_replay_ready"] is True, "53 replay ready")
    assert_true(report["phase53_empty_capture_replay_handled"] is True, "53 empty replay handled")
    assert_true(report["phase53_review_packet_count"] == 0, "53 no packets from empty capture")
    assert_true(report["phase53_capture_replay_discord_message_sent"] is False, "53 no message")
    assert_true(report["phase53_capture_replay_raw_content_logged"] is False, "53 no raw content")
    assert_true(report["phase53_capture_replay_raw_discord_ids_logged"] is False, "53 no raw IDs")
    assert_true(report["phase53_next_readonly_capture_canary_plan_available"] is True, "53 canary plan")
    assert_true(report["phase53_ready_for_next_manual_gate"] is True, "53 next manual gate")
    assert_true(report["phase52b_53_review_packet_pipeline_ready_for_real_capture"] is True, "52B/53 pipeline ready")
    assert_true(report["phase48a_actual_discord_reply_completed_once"] is True, "48A 41B once")
    assert_true(report["phase48a_phase41b_reply_count"] == 1, "48A 41B count")
    assert_true(report["phase48a_actual_supervised_discord_session_completed_once"] is True, "48A 42 once")
    assert_true(report["phase48a_phase42_message_sent_count"] == 1, "48A 42 count")
    assert_true(report["phase48a_actual_llm_call_completed_once"] is True, "48A 45 once")
    assert_true(report["phase48a_phase45_llm_call_count"] == 1, "48A 45 count")
    assert_true(report["phase48a_phase45_output_safety_blocked"] is True, "48A 45 blocked")
    assert_true(report["phase48a_blocked_llm_output_raw_included"] is False, "48A no raw")
    assert_true(report["phase48a_discord_send_after_llm"] is False, "48A no Discord after LLM")
    assert_true(report["phase48a_automatic_retry_allowed"] is False, "48A no retry")
    assert_true(report["phase48a_automatic_discord_send_allowed"] is False, "48A no auto Discord")
    assert_true(report["phase48a_unattended_auto_reply_allowed"] is False, "48A no unattended")
    assert_true(report["phase48a_ready_for_production_unattended_mode"] is False, "48A no production unattended")
    assert_true(report["phase48a_future_external_action_requires_new_manual_gate"] is True, "48A future gate")
    assert_true(report["phase48a_operator_handoff_packet_available"] is True, "48A handoff")
    assert_true(report["phase49_target_system"] == "STOXL_Discord_Agent_OS", "49 target")
    assert_true(report["phase49_final_goal_is_operation_automation"] is True, "49 automation goal")
    assert_true(report["phase49_human_review_only_is_not_final_goal"] is True, "49 not archive")
    assert_true(report["phase49_production_unattended_ready"] is False, "49 production false")
    assert_true(report["phase49_current_verified_level"] == 3, "49 level")
    assert_true(report["phase49_current_verified_level_status"] == "prototype_verified", "49 level status")
    assert_true(report["phase49_release_blockers_present"] is True, "49 blockers")
    assert_true(report["phase49_ready_for_continuous_readonly_foundation"] is True, "49 next foundation")
    assert_true(report["phase50_target_system"] == "STOXL_Discord_Agent_OS", "50 target")
    assert_true(report["phase50_architecture_locked"] is True, "50 locked")
    assert_true(report["phase50_required_modules_defined"] is True, "50 modules")
    assert_true(report["phase50_manual_gate_boundary_defined"] is True, "50 manual boundary")
    assert_true(report["phase50_automation_levels_defined"] is True, "50 levels")
    assert_true(report["phase50_production_unattended_ready_now"] is False, "50 production false")
    assert_true(report["phase50_next_safe_bundle"] == "continuous_readonly_runtime_foundation", "50 next")
    assert_true(report["phase50_remaining_safe_mega_bundles"] == 7, "50 bundles")
    assert_true(report["phase50_remaining_manual_gates"] == 5, "50 gates")
    assert_true(report["phase50_manual_gate_count"] == 6, "50 gate count")
    assert_true(report["phase50_release_blockers_present"] is True, "50 blockers")
    assert_true(report["phase50_scheduler_live_execution_blocked"] is True, "50 scheduler blocked")


def test_operations_dashboard_lock_phase45_readiness_is_safe_but_execution_is_not() -> None:
    report = build_operations_dashboard_lock()
    report["phase45_ready_for_actual_llm_one_shot_manual_gate"] = True
    report["phase45_ready_for_actual_llm_one_shot_call"] = True
    assert_operations_dashboard_lock_safe(report)
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase45_actual_llm_api_call_attempted": True}), "45 attempted unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase45_actual_llm_api_called": True}), "45 called unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase45_llm_api_call_count": 1}), "45 call count unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase45_actual_llm_call_count": 2}), "45 historical count must stay one")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase45_ready_for_repeat_llm_call": True}), "45 repeat unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase46_automatic_retry_allowed": True}), "46 auto retry unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase46_llm_api_called": True}), "46 LLM unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase46_retry_requires_new_manual_gate": False}), "46 manual gate required")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase47_automatic_retry_allowed": True}), "47 auto retry unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase47_retry_execution_available": True}), "47 retry execution unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase47_raw_output_included": True}), "47 raw output unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase47_discord_message_sent": True}), "47 Discord unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase47_manual_retry_requires_new_phase": False}), "47 new phase required")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase48a_automatic_retry_allowed": True}), "48A auto retry unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase48a_discord_send_after_llm": True}), "48A Discord after LLM unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase48a_ready_for_production_unattended_mode": True}), "48A production unattended unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase48a_future_external_action_requires_new_manual_gate": False}), "48A future gate required")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase49_production_unattended_ready": True}), "49 production unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase49_current_verified_level": 5}), "49 level unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase50_production_unattended_ready_now": True}), "50 production unsafe")
    assert_raises(lambda: assert_operations_dashboard_lock_safe({**report, "phase50_manual_gate_execution_available_now": True}), "50 gate execution unsafe")


def test_operations_dashboard_lock_phase36_post_call_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase36f_no_send_final_lock_passed"] is True, "36F passed")
    assert_true(report["phase36g_post_llm_dashboard_lock_available"] is True, "36G available")
    assert_true(report["phase36_total_llm_call_count"] == 1, "Phase 36 LLM count")
    assert_true(report["phase36_total_discord_message_sent_count"] == 0, "Phase 36 Discord count")
    assert_true(report["ready_for_phase37_entry_gate"] is True, "Ready for 37 gate")


def test_operations_dashboard_lock_phase38_entry_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase38e_live_send_entry_gate_available"] is True, "38E available")
    assert_true(report["phase39_not_started"] is True, "Phase 39 not started")
    assert_true(report["ready_for_phase39_live_execution"] is False, "No Phase 39 live readiness")


def test_operations_dashboard_lock_phase39a_blocked_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase39a_actual_send_path_available"] is True, "39A path available")
    assert_true(report["phase39a_blocked"] is True, "39A blocked")
    assert_true(report["phase39a_actual_private_test_send_executed"] is False, "39A no actual send")
    assert_true(report["phase39a_discord_message_sent"] is False, "39A no Discord message")
    assert_true(report["ready_for_phase39b_manual_one_shot_send"] is False, "No 39B readiness")


def test_operations_dashboard_lock_phase39b_no_send_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase39b_actual_send_not_executed_yet"] is True, "39B not executed")
    assert_true(report["phase39b_actual_discord_send_count"] == 0, "39B send count 0")
    assert_true(report["phase39b_discord_message_sent"] is False, "39B no message")
    assert_true(report["phase39c_closeout_not_available"] is True, "39C unavailable")
    assert_true(report["ready_for_phase39c_send_closeout"] is False, "No 39C ready")


def test_operations_dashboard_lock_phase39c_closeout_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase39c_closeout_completed"] is True, "39C closeout complete")
    assert_true(report["phase39c_actual_discord_send_count_locked"] == 1, "39C locked count 1")
    assert_true(report["phase39c_repeat_send_allowed"] is False, "39C no repeat")
    assert_true(report["phase39c_automatic_retry_allowed"] is False, "39C no auto retry")
    assert_true(report["phase39c_ready_for_repeat_send"] is False, "39C no repeat readiness")
    assert_true(report["phase39c_gate_off_verified"] is True, "39C gate off")
    assert_true(report["phase39c_additional_send_count"] == 0, "39C no additional send")


def test_operations_dashboard_lock_phase40_runtime_readiness_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase40_runtime_readiness_available"] is True, "40 readiness available")
    assert_true(report["phase40_actual_discord_send_count_locked"] == 1, "40 locked count")
    assert_true(report["phase40_additional_discord_send_count"] == 0, "40 no additional send")
    assert_true(report["phase40_live_runtime_started"] is False, "40 no runtime")
    assert_true(report["phase40_discord_gateway_connected"] is False, "40 no gateway")
    assert_true(report["phase40_discord_api_send_called"] is False, "40 no API send")
    assert_true(report["phase40_discord_message_sent"] is False, "40 no message")
    assert_true(report["phase40_message_sent_count"] == 0, "40 message count 0")
    assert_true(report["phase40_synthetic_replay_only"] is True, "40 synthetic replay")
    assert_true(report["phase40_outbound_queue_enabled"] is False, "40 queue off")
    assert_true(report["phase40_send_worker_enabled"] is False, "40 worker off")
    assert_true(report["phase40_duplicate_message_id_guard"] is True, "40 dedupe")
    assert_true(report["phase40_live_runtime_start_allowed"] is False, "40 live blocked")
    assert_true(report["phase40_ready_for_live_runtime_execution"] is False, "40 no live execution")
    assert_true(report["phase40_safe_to_review_next_morning"] is True, "40 safe overnight")


def test_operations_dashboard_lock_phase40j_n_readonly_entry_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase40j_readonly_preflight_available"] is True, "40J preflight")
    assert_true(report["phase40j_ready_for_manual_readonly_runtime_launch"] is False, "40J not ready")
    assert_true(report["phase40k_manual_launch_only"] is True, "40K manual only")
    assert_true(report["phase40k_codex_must_not_launch"] is True, "40K codex no launch")
    assert_true(report["phase40k_planned_command_executed_by_codex"] is False, "40K command not executed")
    assert_true(report["phase40l_capture_closeout_available"] is True, "40L closeout")
    assert_true(report["phase40l_live_capture_observed"] is False, "40L no capture")
    assert_true(report["phase40l_captured_event_count"] == 0, "40L no events")
    assert_true(report["phase40m_manual_abort_available"] is True, "40M abort")
    assert_true(report["phase40m_abort_on_any_send_attempt"] is True, "40M send abort")
    assert_true(report["phase40n_phase41_reply_runtime_entry_gate_available"] is True, "40N gate")
    assert_true(report["phase40n_phase41_reply_runtime_allowed"] is False, "40N blocked")
    assert_true(report["phase40n_reply_send_allowed"] is False, "40N no reply")
    assert_true(report["phase40n_ready_for_phase41_reply_runtime"] is False, "40N not ready")


def test_operations_dashboard_lock_phase40o_s_review_pipeline_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase40o_manual_launch_only"] is True, "40O manual")
    assert_true(report["phase40o_codex_must_not_launch"] is True, "40O codex no launch")
    assert_true(report["phase40o_ready_for_manual_readonly_runtime_launch"] is False, "40O not ready")
    assert_true(report["phase40p_capture_schema_available"] is True, "40P schema")
    assert_true(report["phase40p_raw_content_logged"] is False, "40P raw false")
    assert_true(report["phase40p_secret_values_logged"] is False, "40P secrets false")
    assert_true(report["phase40q_capture_file_present"] is False, "40Q no file")
    assert_true(report["phase40q_capture_review_completed"] is False, "40Q no review")
    assert_true(report["phase40q_message_sent_count"] == 0, "40Q no send")
    assert_true(report["phase40r_phase41_reply_runtime_allowed"] is False, "40R blocked")
    assert_true(report["phase40r_discord_reply_send_allowed"] is False, "40R no reply")
    assert_true(report["phase40r_llm_reply_allowed"] is False, "40R no LLM")
    assert_true(report["phase40r_rag_reply_allowed"] is False, "40R no RAG")
    assert_true(report["phase40s_safe_to_review_next_morning"] is True, "40S safe")
    assert_true(report["phase40s_requires_user_confirmation"] is True, "40S confirmation")
    assert_true(report["phase40s_additional_discord_send_count"] == 0, "40S no send")
    assert_true(report["phase40t_command_available"] is True, "40T command")
    assert_true(report["phase40t_blocked_by_default"] is True, "40T blocked")
    assert_true(report["phase40t_manual_runtime_launch_allowed"] is False, "40T no launch by default")
    assert_true(report["phase40t_codex_runtime_launch_forbidden"] is True, "40T codex forbidden")
    assert_true(report["phase40t_live_runtime_started"] is False, "40T no live")
    assert_true(report["phase40t_discord_gateway_connected"] is False, "40T no gateway")
    assert_true(report["phase40t_discord_api_send_called"] is False, "40T no API")
    assert_true(report["phase40t_discord_message_sent"] is False, "40T no message")
    assert_true(report["phase40t_message_sent_count"] == 0, "40T count 0")
    assert_true(report["phase40t_preflight_snapshot_preserved"] is True, "40T snapshot")
    assert_true(report["phase40t_presence_consistency_verified"] is True, "40T consistency")
    assert_true(report["phase40t_login_attempt_requires_token_and_channel"] is True, "40T login requires token/channel")
    assert_true(report["phase40t_execution_gate_available"] is True, "40T-1 gate")
    assert_true(report["phase40t_execute_flag_required"] is True, "40T-1 execute required")
    assert_true(report["phase40t_execute_flag_present"] is False, "40T-1 execute absent")
    assert_true(report["phase40t_execution_gate_blocked_by_default"] is True, "40T-1 blocked")
    assert_true(report["phase40t_redacted_capture_only"] is True, "40T-1 redacted")
    assert_true(report["phase40t_capture_raw_content_allowed"] is False, "40T-1 no raw")
    assert_true(report["phase40t_closeout_started"] is False, "40T-1 closeout not started")
    assert_true(report["phase40t_closeout_gateway_connected"] is False, "40T-1 closeout no gateway")
    assert_true(report["phase40t_closeout_message_sent_count"] == 0, "40T-1 closeout no send")
    assert_true(report["phase40t_login_failure_closeout_available"] is True, "40T-2 login failure closeout")
    assert_true(report["phase40t_login_failure_gateway_connected"] is False, "40T-2 no gateway")
    assert_true(report["phase40t_login_failure_discord_api_send_called"] is False, "40T-2 no API")
    assert_true(report["phase40t_login_failure_discord_message_sent"] is False, "40T-2 no message")
    assert_true(report["phase40t_login_failure_message_sent_count"] == 0, "40T-2 count 0")
    assert_true(report["phase40t_login_failure_retry_attempted"] is False, "40T-2 no retry")
    assert_true(report["phase40t_login_failure_traceback_included"] is False, "40T-2 no traceback")
    assert_true(report["phase40t_login_failure_preflight_snapshot_preserved"] is True, "40T-3 failure snapshot")
    assert_true(report["phase40t_login_failure_presence_consistency_verified"] is True, "40T-3 failure consistency")


def test_operations_dashboard_lock_phase40u_41a_state() -> None:
    report = build_operations_dashboard_lock()
    assert_true(report["phase40t_gateway_connect_verified"] is True, "40U Gateway verified")
    assert_true(report["phase40u_closeout_ready"] is True, "40U closeout ready")
    assert_true(report["phase40u_discord_api_send_called"] is False, "40U no API send")
    assert_true(report["phase40u_discord_message_sent"] is False, "40U no message")
    assert_true(report["phase40u_message_sent_count"] == 0, "40U count 0")
    assert_true(report["phase40x_reply_dry_run_ready"] is True, "40X dry-run ready")
    assert_true(report["phase40x_discord_api_send_called"] is False, "40X no API send")
    assert_true(report["phase40x_discord_message_sent"] is False, "40X no message")
    assert_true(report["phase40x_message_sent_count"] == 0, "40X count 0")
    assert_true(report["phase41_actual_reply_default_blocked"] is True, "41 default blocked")
    assert_true(report["phase41_actual_reply_send_executed"] is False, "41 no actual reply")
    assert_true(report["phase41_discord_api_send_called"] is False, "41 no API send")
    assert_true(report["phase41_discord_message_sent"] is False, "41 no message")
    assert_true(report["phase41_message_sent_count"] == 0, "41 count 0")
    assert_true(report["phase40z_handoff_ready"] is True, "40Z handoff ready")
    assert_true(report["phase41a_preflight_default_blocked"] is True, "41A default blocked")
    assert_true(report["phase41a_ready_for_manual_private_test_reply"] is False, "41A not ready")


def test_operations_dashboard_lock_no_sensitive_values() -> None:
    text = json.dumps(build_operations_dashboard_lock(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_operations_dashboard_lock_markdown() -> None:
    assert_true("Operations Dashboard Lock" in render_operations_dashboard_lock_markdown(build_operations_dashboard_lock()), "Markdown")


def main() -> int:
    tests = [
        test_operations_dashboard_lock_success_fixture,
        test_operations_dashboard_lock_final_counts,
        test_operations_dashboard_lock_safety_false,
        test_operations_dashboard_lock_phase41b_45a_state,
        test_operations_dashboard_lock_phase51_52_foundation_state,
        test_operations_dashboard_lock_phase45_readiness_is_safe_but_execution_is_not,
        test_operations_dashboard_lock_phase36_post_call_state,
        test_operations_dashboard_lock_phase38_entry_state,
        test_operations_dashboard_lock_phase39a_blocked_state,
        test_operations_dashboard_lock_phase39b_no_send_state,
        test_operations_dashboard_lock_phase39c_closeout_state,
        test_operations_dashboard_lock_phase40_runtime_readiness_state,
        test_operations_dashboard_lock_phase40j_n_readonly_entry_state,
        test_operations_dashboard_lock_phase40o_s_review_pipeline_state,
        test_operations_dashboard_lock_phase40u_41a_state,
        test_operations_dashboard_lock_no_sensitive_values,
        test_operations_dashboard_lock_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All operations dashboard lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
