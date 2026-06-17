from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase49_production_readiness_audit import build_phase49_production_readiness_audit


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase49_contract() -> None:
    report = build_phase49_production_readiness_audit()
    assert_true(report["report_type"] == "phase49_production_readiness_audit", "Report type")
    assert_true(report["target_system"] == "STOXL_Discord_Agent_OS", "Target")
    assert_true(report["final_goal_is_operation_automation"] is True, "Automation goal")
    assert_true(report["human_review_only_is_not_final_goal"] is True, "Not archive")
    assert_true(report["production_unattended_ready"] is False, "No production unattended")
    assert_true(report["safe_for_human_review_only"] is True, "Human review safe")
    assert_true(report["external_action_freeze_active"] is True, "Freeze")
    assert_true(report["manual_gate_required_for_any_future_external_action"] is True, "Manual gate")


def test_phase49_levels_and_history() -> None:
    report = build_phase49_production_readiness_audit()
    levels = report["automation_levels"]
    history = report["actual_external_action_history"]
    assert_true(levels["level_0_human_review_only"] is True, "Level 0")
    assert_true(levels["level_1_read_only_observation"] == "partially_verified", "Level 1")
    assert_true(levels["level_2_manual_gate_one_shot_execution"] is True, "Level 2")
    assert_true(levels["level_3_supervised_private_test_auto_reply"] == "prototype_verified", "Level 3")
    assert_true(levels["level_4_low_risk_team_auto_ops"] is False, "Level 4")
    assert_true(levels["level_5_limited_production_unattended"] is False, "Level 5")
    assert_true(report["current_verified_level"] == 3, "Current level")
    assert_true(history["phase41b_discord_reply_completed_once"] is True, "41B")
    assert_true(history["phase42_supervised_session_completed_once"] is True, "42")
    assert_true(history["phase45_llm_call_completed_once"] is True, "45")
    assert_true(history["discord_send_after_llm"] is False, "No Discord after LLM")
    assert_true(history["blocked_llm_output_sent"] is False, "Blocked output not sent")


def test_phase49_readiness_and_no_execution() -> None:
    report = build_phase49_production_readiness_audit()
    assert_true(report["release_blockers_present"] is True, "Blockers")
    assert_true(report["ready_for_architecture_lock"] is True, "Architecture")
    assert_true(report["ready_for_continuous_readonly_foundation"] is True, "Read-only foundation")
    assert_true(report["ready_for_rag_foundation"] is False, "RAG not ready")
    assert_true(report["ready_for_low_risk_team_auto_ops"] is False, "Team ops not ready")
    assert_true(report["ready_for_limited_production_unattended"] is False, "Production not ready")
    for key in ("llm_api_call_attempted", "llm_api_called", "discord_api_send_called", "discord_message_sent", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "scheduler_cron_live_execution"):
        assert_true(report[key] is False, key)


def test_phase49_no_sensitive_values() -> None:
    text = json.dumps(build_phase49_production_readiness_audit(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase49_contract, test_phase49_levels_and_history, test_phase49_readiness_and_no_execution, test_phase49_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase49 production readiness audit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
