from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase51_52_continuous_readonly_foundation import build_phase51_52_continuous_readonly_foundation


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase51_52_foundation_contract() -> None:
    report = build_phase51_52_continuous_readonly_foundation()
    assert_true(report["report_type"] == "phase51_52_continuous_readonly_foundation", "Report type")
    assert_true(report["continuous_readonly_runtime_foundation_ready"] is True, "Foundation ready")
    assert_true(report["review_packet_base_ready"] is True, "Review packet ready")
    assert_true(report["event_schema_ready"] is True, "Schema")
    assert_true(report["event_guard_ready"] is True, "Guard")
    assert_true(report["session_context_store_ready"] is True, "Session")
    assert_true(report["synthetic_replay_passed"] is True, "Replay")
    assert_true(report["ready_for_manual_gate_readonly_live_runtime"] is True, "Manual gate")
    assert_true(report["ready_for_auto_reply"] is False, "No auto reply")
    assert_true(report["ready_for_team_channel_auto_ops"] is False, "No team ops")
    assert_true(report["ready_for_production_unattended"] is False, "No production")


def test_phase51_52_foundation_no_external_actions() -> None:
    report = build_phase51_52_continuous_readonly_foundation()
    for key in ("actual_discord_runtime_executed", "discord_api_send_called", "discord_message_sent", "actual_llm_api_call_attempted", "actual_llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "scheduler_cron_live_execution", "unattended_auto_reply_implemented"):
        assert_true(report[key] is False, key)


def test_phase51_52_foundation_no_sensitive_values() -> None:
    text = json.dumps(build_phase51_52_continuous_readonly_foundation(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase51_52_foundation_contract, test_phase51_52_foundation_no_external_actions, test_phase51_52_foundation_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase51/52 continuous read-only foundation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
