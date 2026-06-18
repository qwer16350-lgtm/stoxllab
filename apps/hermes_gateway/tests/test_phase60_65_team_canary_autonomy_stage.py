from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase60_65_team_canary_autonomy_stage import (
    APPROVAL_PHRASE,
    REPLY_MODE,
    Phase60TeamCanarySendResult,
    build_actual_phase60_team_canary,
    build_phase60_65_team_canary_autonomy_stage,
    build_phase60_team_canary_blocked_report,
    build_phase60_team_canary_closeout,
    build_phase60_team_canary_preflight,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def opened_env() -> dict[str, str]:
    return {
        "HERMES_PHASE60_TEAM_CANARY_APPROVED": "true",
        "HERMES_PHASE60_TEAM_CANARY_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_PHASE60_TEAM_CANARY_KILL_SWITCH_READY": "true",
        "HERMES_PHASE60_TEAM_CANARY_MAX_SEND_COUNT": "1",
        "HERMES_PHASE60_TEAM_CANARY_MAX_REPLY_COUNT": "1",
        "HERMES_PHASE60_TEAM_CANARY_COOLDOWN_SECONDS": "30",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_REPLY_MODE": REPLY_MODE,
        "HERMES_DISCORD_LLM_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_EMBEDDING_ENABLED": "false",
        "HERMES_VECTOR_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "DISCORD_BOT_TOKEN": "present",
        "HERMES_PHASE60_TEAM_CANARY_CHANNEL_ID": "team-canary",
    }


class FakeTeamCanarySender:
    def __init__(self) -> None:
        self.calls = 0

    def send_team_canary(self, content: str) -> Phase60TeamCanarySendResult:
        self.calls += 1
        assert_true("Phase60" in content, "Deterministic content")
        return Phase60TeamCanarySendResult(api_send_called=True, message_sent=True, message_sent_count=1, status_code=200)


def test_phase60_path_available_and_default_blocked() -> None:
    preflight = build_phase60_team_canary_preflight({})
    assert_true(preflight["phase60_low_risk_team_canary_path_available"] is True, "Path available")
    assert_true(preflight["team_canary_manual_gate_required"] is True, "Manual gate")
    assert_true(preflight["ready_for_phase60_team_canary_manual_gate"] is False, "Closed gate")
    assert_true(preflight["team_canary_channel_id_present"] is False, "No channel env")
    assert_true(preflight["team_canary_channel_id_value_logged"] is False, "No channel value")
    blocked = build_actual_phase60_team_canary(env=opened_env())
    assert_true(blocked["blocked"] is True, "Default blocked")
    assert_true(blocked["blocked_reasons"] == ["phase60_team_canary_already_consumed"], "Consumed lock")
    assert_true(blocked["team_canary_channel_id_present"] is True, "Channel present")
    assert_true(blocked["team_canary_channel_id_value_logged"] is False, "Channel hidden")
    assert_true(blocked["actual_team_canary_executed"] is False, "No execution")
    assert_true(blocked["discord_api_send_called"] is False, "No API")
    assert_true(blocked["discord_message_sent"] is False, "No message")
    assert_true(blocked["message_sent_count"] == 0, "No count")


def test_fake_sender_success_exactly_once() -> None:
    sender = FakeTeamCanarySender()
    report = build_actual_phase60_team_canary(
        allow_flag_present=True,
        env=opened_env(),
        send_adapter=sender,
        phase60_team_canary_already_consumed=False,
    )
    assert_true(sender.calls == 1, "One fake send")
    assert_true(report["blocked"] is False, "Not blocked")
    assert_true(report["team_canary_channel_id_present"] is True, "Channel present")
    assert_true(report["team_canary_channel_id_value_logged"] is False, "Channel hidden")
    assert_true(report["actual_team_canary_executed"] is True, "Executed")
    assert_true(report["sent_scope"] == "known_team_channel_only", "Team scope")
    assert_true(report["reply_text_source"] == "deterministic_template", "Deterministic")
    assert_true(report["discord_api_send_called"] is True, "Fake API")
    assert_true(report["discord_message_sent"] is True, "Fake sent")
    assert_true(report["message_sent_count"] == 1, "Exactly one")
    assert_true(report["ready_for_repeat_team_canary"] is False, "No repeat")
    assert_true(report["public_channel_send_allowed"] is False, "No public")
    assert_true(report["unknown_channel_send_allowed"] is False, "No unknown")


def test_phase60_actual_success_historical_closeout() -> None:
    report = build_phase60_team_canary_closeout()
    assert_true(report["report_type"] == "phase60_team_canary_closeout", "Closeout report")
    assert_true(report["phase60_team_canary_closed_out"] is True, "Closed out")
    assert_true(report["phase60_actual_team_canary_sent"] is True, "Historical sent")
    assert_true(report["historical_message_sent_count"] == 1, "Historical count")
    assert_true(report["real_team_discord_send_performed"] is True, "Historical real send semantic")
    assert_true(report["phase60_repeat_team_canary_locked"] is True, "Repeat locked")
    assert_true(report["ready_for_repeat_team_canary"] is False, "No repeat")
    assert_true(report["current_verified_level"] == "level4_low_risk_team_channel_canary_verified_once", "Level 4")
    assert_true(report["previous_verified_level"] == "level3_supervised_private_test_auto_reply_verified", "Previous level")
    assert_true(report["next_target_level"] == "level4_supervised_team_channel_auto_ops", "Next target")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    assert_true(report["discord_api_send_called"] is False, "Closeout no API")
    assert_true(report["discord_message_sent"] is False, "Closeout no send")
    assert_true(report["message_sent_count"] == 0, "Closeout no new message")


def test_repeat_actual_blocks_even_with_open_gate() -> None:
    sender = FakeTeamCanarySender()
    report = build_actual_phase60_team_canary(
        allow_flag_present=True,
        env=opened_env(),
        send_adapter=sender,
    )
    assert_true(sender.calls == 0, "Consumed canary must not call sender")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["blocked_reasons"] == ["phase60_team_canary_already_consumed"], "Consumed reason only")
    assert_true(report["actual_team_canary_executed"] is False, "No execution")
    assert_true(report["real_team_discord_send_performed"] is False, "No real send")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")
    assert_true(report["ready_for_repeat_team_canary"] is False, "No repeat")


def test_public_unknown_high_risk_and_multi_message_blocked() -> None:
    cases = (
        ({"channel_scope": "public"}, "public_channel_blocked"),
        ({"channel_scope": "unknown", "known_team_channel": False}, "known_team_channel_required"),
        ({"intent": "legal_financial_advice"}, "high_risk_intent_blocked"),
        ({"message_count": 2}, "max_one_reply_per_event_required"),
    )
    for event, reason in cases:
        report = build_phase60_team_canary_blocked_report(allow_flag_present=True, env=opened_env(), event=event)
        assert_true(report["blocked"] is True, "Blocked")
        assert_true(reason in report["blocked_reasons"], reason)
        assert_true(report["actual_team_canary_executed"] is False, "No execution")
        assert_true(report["message_sent_count"] == 0, "No send")


def test_phase61_scheduler_and_phase62_65_matrix() -> None:
    report = build_phase60_65_team_canary_autonomy_stage()
    assert_true(report["phase61_scheduler_gate_available"] is True, "Scheduler gate")
    assert_true(report["scheduler_dry_run_control_available"] is True, "Scheduler dry-run")
    assert_true(report["scheduler_live_execution"] is False, "No scheduler live")
    assert_true(report["cron_started"] is False, "No cron")
    assert_true(report["phase62_65_autonomy_matrix_updated"] is True, "Matrix")
    assert_true(report["current_verified_level"] == "level3_supervised_private_test_auto_reply_verified", "Level 3")
    assert_true(report["next_target_level"] == "level4_low_risk_team_channel_canary", "Level 4 target")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")


def test_no_external_or_sensitive_values() -> None:
    report = build_phase60_65_team_canary_autonomy_stage()
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
        test_phase60_path_available_and_default_blocked,
        test_fake_sender_success_exactly_once,
        test_phase60_actual_success_historical_closeout,
        test_repeat_actual_blocks_even_with_open_gate,
        test_public_unknown_high_risk_and_multi_message_blocked,
        test_phase61_scheduler_and_phase62_65_matrix,
        test_no_external_or_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase60-65 team canary autonomy stage tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
