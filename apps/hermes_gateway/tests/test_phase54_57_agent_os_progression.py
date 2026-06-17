from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase54_57_agent_os_progression import build_phase54_57_agent_os_progression


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase54_57_capture_and_replay_contract() -> None:
    report = build_phase54_57_agent_os_progression()
    assert_true(report["report_type"] == "phase54_57_agent_os_progression", "Report type")
    assert_true(report["real_readonly_canary_closed_out"] is True, "Canary closeout")
    assert_true(report["gateway_connection_verified"] is True, "Gateway verified")
    assert_true(report["captured_event_count"] == 1, "Captured event count")
    assert_true(report["captured_private_test_human_message_count"] == 1, "Human message count")
    assert_true(report["capture_file_written"] is True, "Capture file written")
    assert_true(report["capture_file_metadata_only"] is True, "Metadata only")
    assert_true(report["real_capture_to_review_packet_replay_ready"] is True, "Replay ready")
    assert_true(report["review_packet_count"] == 1, "Review packet count")
    assert_true(report["requires_human_review"] is True, "Human review")
    assert_true(report["recommended_next_action"] == "manual_approved_reply_preflight", "Next action")


def test_phase54_57_reply_and_auto_reply_prep() -> None:
    report = build_phase54_57_agent_os_progression()
    assert_true(report["manual_approved_reply_preflight_available"] is True, "Manual preflight")
    assert_true(report["manual_gate_required"] is True, "Manual gate")
    assert_true(report["approval_phrase_present"] is True, "Approval phrase presence")
    assert_true(report["approval_phrase_value_logged"] is False, "Approval value hidden")
    assert_true(report["ready_for_actual_private_test_manual_reply"] is False, "No direct reply")
    assert_true(report["ready_for_actual_private_test_manual_reply_gate"] is True, "Manual reply gate")
    assert_true(report["mock_reply_packet_created"] is True, "Mock reply")
    assert_true(report["reply_text_source"] == "deterministic_template", "Template")
    assert_true(report["raw_user_content_included"] is False, "No raw user content")
    assert_true(report["ready_for_manual_reply_send_gate"] is True, "Send gate prep")
    assert_true(report["supervised_private_test_auto_reply_prep_ready"] is True, "Auto-reply prep")
    assert_true(report["actual_auto_reply_executed"] is False, "No auto reply")
    assert_true(report["ready_for_supervised_private_test_auto_reply_manual_gate"] is True, "Supervised gate")


def test_phase54_57_team_and_scheduler_policies() -> None:
    report = build_phase54_57_agent_os_progression()
    assert_true(report["low_risk_team_auto_ops_policy_defined"] is True, "Team policy")
    assert_true(report["team_channel_auto_ops_executed"] is False, "Team not executed")
    assert_true(report["ready_for_team_channel_auto_ops"] is False, "Team not ready")
    assert_true(report["manual_gate_required_for_team_canary"] is True, "Team gate")
    assert_true(report["scheduler_dry_run_policy_defined"] is True, "Scheduler policy")
    assert_true(report["scheduler_live_execution"] is False, "No scheduler")
    assert_true(report["cron_started"] is False, "No cron")
    assert_true(report["ready_for_scheduler_manual_gate"] is False, "No scheduler gate")


def test_phase54_57_no_external_actions_or_raw_values() -> None:
    report = build_phase54_57_agent_os_progression()
    for key in (
        "actual_discord_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_live_execution",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
    ):
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "No messages")


def test_phase54_57_no_sensitive_values() -> None:
    text = json.dumps(build_phase54_57_agent_os_progression(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase54_57_capture_and_replay_contract,
        test_phase54_57_reply_and_auto_reply_prep,
        test_phase54_57_team_and_scheduler_policies,
        test_phase54_57_no_external_actions_or_raw_values,
        test_phase54_57_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase54-57 Agent OS progression tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
