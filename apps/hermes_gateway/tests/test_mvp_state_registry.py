from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from mvp_state_registry import (
    build_hermes_manual_gate_inventory,
    build_hermes_mvp_state_report,
    build_hermes_post_mvp_compaction_plan,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_mvp_state_report() -> None:
    report = build_hermes_mvp_state_report()
    assert_true(report["report_type"] == "hermes_mvp_state_report", "Report type")
    assert_true(report["mvp_supervised_discord_agent_os_complete"] is True, "MVP complete")
    assert_true(report["ready_for_production_unattended"] is False, "Production unattended false")
    assert_true(report["current_verified_level"] == "level4_limited_auto_mode_short_run_verified_once", "Current level")
    assert_true(report["next_target_level"] == "production_hardening_refactor_compaction", "Next target")
    assert_true(report["verified_levels"]["level_4_limited_auto"] == "limited_auto_mode_short_run_verified_once", "Limited auto")
    assert_true(report["verified_levels"]["level_5"] == "production_unattended_not_ready", "Level 5")
    for lock_name in (
        "phase58_private_test_reply",
        "phase59_supervised_private_test_auto_reply",
        "phase60_team_canary",
        "phase67_team_auto_ops",
        "phase74_limited_auto_mode",
    ):
        assert_true(report["consumed_locks"][lock_name] is True, lock_name)


def test_manual_gate_inventory() -> None:
    report = build_hermes_manual_gate_inventory()
    names = {gate["name"] for gate in report["manual_gates"]}
    for expected in (
        "phase39_private_test_one_shot_send",
        "phase41_private_test_reply",
        "phase42_supervised_private_test_session",
        "phase45_llm_one_shot",
        "phase58_private_test_reply",
        "phase59_supervised_private_test_auto_reply",
        "phase60_team_canary",
        "phase67_supervised_team_auto_ops",
        "phase74_limited_auto_mode_short_run",
    ):
        assert_true(expected in names, expected)
    assert_true(all(gate["status"] == "consumed_locked" for gate in report["manual_gates"]), "Consumed locked")
    assert_true(report["approval_phrase_values_logged"] is False, "No approval values")
    assert_true(report["token_values_logged"] is False, "No token values")
    assert_true(report["channel_id_values_logged"] is False, "No channel values")


def test_compaction_plan_safeguards() -> None:
    report = build_hermes_post_mvp_compaction_plan()
    assert_true(report["report_type"] == "hermes_post_mvp_compaction_plan", "Report type")
    assert_true(report["safe_to_start_compaction"] is True, "Safe to plan")
    assert_true(report["delete_files_now"] is False, "No delete")
    assert_true(report["move_files_now"] is False, "No move")
    assert_true(report["production_unattended_ready"] is False, "Production unattended false")
    for safeguard in (
        "manual gate required behavior",
        "consumed/no-repeat locks",
        "secret redaction",
        "public/unknown/high-risk blocking",
        "LLM/RAG/external disabled by default",
        "scheduler live disabled by default",
    ):
        assert_true(safeguard in report["do_not_change"], safeguard)
    assert_true("centralize consumed lock policy" in report["recommended_next_steps"], "Consumed lock target")


def test_no_runtime_send_or_sensitive_values() -> None:
    reports = [
        build_hermes_mvp_state_report(),
        build_hermes_manual_gate_inventory(),
        build_hermes_post_mvp_compaction_plan(),
    ]
    for report in reports:
        for key in (
            "actual_discord_runtime_executed",
            "discord_gateway_live_connection_executed",
            "discord_api_send_called",
            "discord_message_sent",
            "llm_api_call_attempted",
            "llm_api_called",
            "rag_called",
            "embedding_api_called",
            "vector_index_created",
            "external_execution",
            "scheduler_live_execution",
            "cron_started",
            "raw_content_logged",
            "raw_discord_ids_logged",
            "secret_values_logged",
            "approval_phrase_value_logged",
            "team_channel_id_value_logged",
        ):
            assert_true(report[key] is False, key)
        assert_true(report["message_sent_count"] == 0, "No message")
        assert_true(report["reply_count"] == 0, "No reply")
        text = json.dumps(report, ensure_ascii=False).lower()
        assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
        assert_true("i_approve_" not in text, "No approval phrase")
        assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_mvp_state_report,
        test_manual_gate_inventory,
        test_compaction_plan_safeguards,
        test_no_runtime_send_or_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All MVP state registry tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
