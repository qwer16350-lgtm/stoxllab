from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase59_62_agent_os_autonomy_stage import build_phase59_62_agent_os_autonomy_stage


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase59_sender_adapter_and_next_gate() -> None:
    report = build_phase59_62_agent_os_autonomy_stage()
    assert_true(report["report_type"] == "phase59_62_agent_os_autonomy_stage", "Report type")
    assert_true(report["phase59_sender_adapter_wired"] is True, "Sender adapter wired")
    assert_true(report["phase59_send_adapter_required_block_resolved"] is True, "Adapter block resolved")
    assert_true(report["phase59_ready_for_manual_gate_short_session"] is True, "Manual Gate ready")
    assert_true(report["phase59_ready_for_repeat_session"] is False, "No repeat session")
    assert_true(report["phase59_max_reply_count"] == 1, "Max reply one")
    assert_true(report["phase59_max_send_count"] == 1, "Max send one")


def test_team_scheduler_autonomy_sync() -> None:
    report = build_phase59_62_agent_os_autonomy_stage()
    assert_true(report["phase60_low_risk_team_canary_policy_synced"] is True, "Team policy")
    assert_true(report["phase60_ready_for_team_auto_ops"] is False, "Team not ready")
    assert_true(report["phase61_scheduler_dry_run_control_synced"] is True, "Scheduler dry-run")
    assert_true(report["phase61_scheduler_live_execution"] is False, "No scheduler live")
    assert_true(report["phase62_autonomy_matrix_updated"] is True, "Autonomy matrix")
    assert_true(report["autonomy_matrix"]["level_2"] == "manual_gate_deterministic_reply_verified", "Level 2")
    assert_true(
        report["autonomy_matrix"]["level_3"] == "supervised_private_test_auto_reply_path_nearly_ready_sender_wired",
        "Level 3",
    )
    assert_true(report["autonomy_matrix"]["level_4"] == "team_auto_ops_not_ready", "Level 4")
    assert_true(report["autonomy_matrix"]["level_5"] == "production_unattended_not_ready", "Level 5")


def test_no_external_or_sensitive_values() -> None:
    report = build_phase59_62_agent_os_autonomy_stage()
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
        "unattended_auto_reply_executed",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
    ):
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "Bundle sends no message")
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase59_sender_adapter_and_next_gate,
        test_team_scheduler_autonomy_sync,
        test_no_external_or_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase59-62 Agent OS autonomy stage tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
