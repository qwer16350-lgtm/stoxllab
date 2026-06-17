from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase59_63_agent_os_supervised_closeout import build_phase59_63_agent_os_supervised_closeout
from phase59_supervised_private_test_auto_reply import (
    APPROVAL_PHRASE,
    REPLY_MODE,
    Phase59SendResult,
    build_actual_phase59_supervised_private_test_auto_reply,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def opened_env() -> dict[str, str]:
    return {
        "HERMES_PHASE59_SUPERVISED_AUTO_REPLY_APPROVED": "true",
        "HERMES_PHASE59_SUPERVISED_AUTO_REPLY_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_PHASE59_MAX_SESSION_SECONDS": "300",
        "HERMES_PHASE59_MAX_REPLY_COUNT": "1",
        "HERMES_PHASE59_MAX_SEND_COUNT": "1",
        "HERMES_PHASE59_COOLDOWN_SECONDS": "30",
        "HERMES_PHASE59_KILL_SWITCH_READY": "true",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": REPLY_MODE,
        "HERMES_DISCORD_LLM_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_EMBEDDING_ENABLED": "false",
        "HERMES_VECTOR_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "DISCORD_BOT_TOKEN": "present",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private-test",
    }


class FakeSenderMustNotRun:
    def __init__(self) -> None:
        self.calls = 0

    def send_supervised_reply(self, content: str) -> Phase59SendResult:
        self.calls += 1
        return Phase59SendResult(api_send_called=True, message_sent=True, message_sent_count=1)


def test_phase59_closeout_and_no_repeat_lock() -> None:
    report = build_phase59_63_agent_os_supervised_closeout()
    assert_true(report["report_type"] == "phase59_63_agent_os_supervised_closeout", "Report type")
    assert_true(report["phase59_supervised_auto_reply_closed_out"] is True, "Phase59 closeout")
    assert_true(report["phase59_actual_session_sent"] is True, "Historical session sent")
    assert_true(report["historical_message_sent_count"] == 1, "Historical count fixed")
    assert_true(report["message_sent_count"] == 0, "No new send")
    assert_true(report["phase59_repeat_session_locked"] is True, "Repeat locked")
    assert_true(report["ready_for_repeat_session"] is False, "No repeat readiness")
    assert_true(
        report["phase59_repeat_block_reason"] == "phase59_supervised_auto_reply_session_already_consumed",
        "Repeat block reason",
    )


def test_actual_phase59_blocks_when_consumed_even_with_open_gate() -> None:
    sender = FakeSenderMustNotRun()
    report = build_actual_phase59_supervised_private_test_auto_reply(
        allow_flag_present=True,
        env=opened_env(),
        send_adapter=sender,
    )
    assert_true(sender.calls == 0, "Consumed session must not call sender")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(
        "phase59_supervised_auto_reply_session_already_consumed" in report["blocked_reasons"],
        "Consumed reason",
    )
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No send count")


def test_phase60_61_62_63_state() -> None:
    report = build_phase59_63_agent_os_supervised_closeout()
    assert_true(report["phase60_low_risk_team_canary_path_available"] is True, "Team path")
    assert_true(report["team_channel_auto_ops_executed"] is False, "No team execution")
    assert_true(report["public_channel_send_allowed"] is False, "No public send")
    assert_true(report["ready_for_phase60_team_canary_manual_gate"] is False, "Team gate not ready")
    assert_true(report["phase61_scheduler_gate_available"] is True, "Scheduler gate")
    assert_true(report["scheduler_dry_run_control_available"] is True, "Scheduler dry-run")
    assert_true(report["scheduler_live_execution"] is False, "No scheduler live")
    assert_true(report["phase62_autonomy_matrix_updated"] is True, "Autonomy updated")
    assert_true(report["current_verified_level"] == "level3_supervised_private_test_auto_reply_verified", "Level 3")
    assert_true(report["next_target_level"] == "level4_low_risk_team_channel_canary", "Next target")
    assert_true(report["ready_for_production_unattended"] is False, "Production not ready")


def test_no_external_or_sensitive_values() -> None:
    report = build_phase59_63_agent_os_supervised_closeout()
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
    ):
        assert_true(report[key] is False, key)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase59_closeout_and_no_repeat_lock,
        test_actual_phase59_blocks_when_consumed_even_with_open_gate,
        test_phase60_61_62_63_state,
        test_no_external_or_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase59-63 Agent OS supervised closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
