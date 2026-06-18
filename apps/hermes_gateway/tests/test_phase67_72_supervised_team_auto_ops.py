from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase67_72_supervised_team_auto_ops import (
    APPROVAL_PHRASE,
    REPLY_MODE,
    Phase67TeamAutoOpsSendResult,
    build_actual_phase67_team_auto_ops,
    build_phase67_72_supervised_team_auto_ops,
    build_phase67_team_auto_ops_closeout,
    build_phase67_team_auto_ops_preflight,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def opened_env() -> dict[str, str]:
    return {
        "HERMES_PHASE67_TEAM_AUTO_OPS_APPROVED": "true",
        "HERMES_PHASE67_TEAM_AUTO_OPS_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_PHASE67_TEAM_AUTO_OPS_CHANNEL_ID": "team-auto-ops",
        "HERMES_PHASE67_TEAM_AUTO_OPS_KILL_SWITCH_READY": "true",
        "HERMES_PHASE67_TEAM_AUTO_OPS_MAX_SESSION_SECONDS": "300",
        "HERMES_PHASE67_TEAM_AUTO_OPS_MAX_SEND_COUNT": "1",
        "HERMES_PHASE67_TEAM_AUTO_OPS_MAX_REPLY_COUNT": "1",
        "HERMES_PHASE67_TEAM_AUTO_OPS_COOLDOWN_SECONDS": "30",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_REPLY_MODE": REPLY_MODE,
        "HERMES_DISCORD_LLM_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_EMBEDDING_ENABLED": "false",
        "HERMES_VECTOR_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "DISCORD_BOT_TOKEN": "present",
    }


class FakeTeamAutoOpsSender:
    def __init__(self) -> None:
        self.calls = 0

    def send_team_auto_ops(self, content: str) -> Phase67TeamAutoOpsSendResult:
        self.calls += 1
        assert_true("Phase67" in content, "Deterministic content")
        return Phase67TeamAutoOpsSendResult(api_send_called=True, message_sent=True, message_sent_count=1, status_code=200)


def test_phase67_path_available_and_default_blocked() -> None:
    preflight = build_phase67_team_auto_ops_preflight({})
    assert_true(preflight["phase67_supervised_team_auto_ops_path_available"] is True, "Path available")
    assert_true(preflight["team_auto_ops_manual_gate_required"] is True, "Manual gate")
    assert_true(preflight["ops_queue_available"] is True, "Ops queue")
    assert_true(preflight["review_packet_required"] is True, "Review packet")
    assert_true(preflight["ready_for_phase67_team_auto_ops_manual_gate"] is False, "Closed gate")
    blocked = build_actual_phase67_team_auto_ops(env=opened_env())
    assert_true(blocked["blocked"] is True, "Default blocked")
    assert_true(blocked["blocked_reasons"] == ["phase67_team_auto_ops_already_consumed"], "Consumed lock")
    assert_true(blocked["actual_team_auto_ops_executed"] is False, "No execution")
    assert_true(blocked["discord_api_send_called"] is False, "No API")
    assert_true(blocked["discord_message_sent"] is False, "No message")
    assert_true(blocked["message_sent_count"] == 0, "No count")


def test_fake_sender_success_exactly_once() -> None:
    sender = FakeTeamAutoOpsSender()
    report = build_actual_phase67_team_auto_ops(
        allow_flag_present=True,
        env=opened_env(),
        send_adapter=sender,
        phase67_team_auto_ops_already_consumed=False,
    )
    assert_true(sender.calls == 1, "One fake send")
    assert_true(report["blocked"] is False, "Not blocked")
    assert_true(report["actual_team_auto_ops_executed"] is True, "Executed")
    assert_true(report["sent_scope"] == "known_team_channel_only", "Team scope")
    assert_true(report["reply_text_source"] == "deterministic_template", "Deterministic")
    assert_true(report["discord_api_send_called"] is True, "Fake API")
    assert_true(report["discord_message_sent"] is True, "Fake sent")
    assert_true(report["message_sent_count"] == 1, "Exactly one")
    assert_true(report["ready_for_repeat_team_auto_ops"] is False, "No repeat")
    assert_true(report["public_channel_send_allowed"] is False, "No public")
    assert_true(report["unknown_channel_send_allowed"] is False, "No unknown")


def test_phase67_actual_success_historical_closeout() -> None:
    report = build_phase67_team_auto_ops_closeout()
    assert_true(report["report_type"] == "phase67_team_auto_ops_closeout", "Closeout report")
    assert_true(report["phase67_team_auto_ops_closed_out"] is True, "Closed out")
    assert_true(report["phase67_actual_team_auto_ops_sent"] is True, "Historical sent")
    assert_true(report["historical_message_sent_count"] == 1, "Historical count")
    assert_true(report["real_team_auto_ops_send_performed"] is True, "Historical real send semantic")
    assert_true(report["phase67_repeat_team_auto_ops_locked"] is True, "Repeat locked")
    assert_true(report["ready_for_repeat_team_auto_ops"] is False, "No repeat")
    assert_true(report["previous_verified_level"] == "level4_low_risk_team_channel_canary_verified_once", "Previous")
    assert_true(report["current_verified_level"] == "level4_supervised_team_channel_auto_ops_verified_once", "Current")
    assert_true(report["next_target_level"] == "level4_limited_auto_mode_prep", "Next")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    assert_true(report["discord_api_send_called"] is False, "Closeout no API")
    assert_true(report["discord_message_sent"] is False, "Closeout no send")
    assert_true(report["message_sent_count"] == 0, "Closeout no new message")


def test_repeat_actual_blocks_even_with_open_gate() -> None:
    sender = FakeTeamAutoOpsSender()
    report = build_actual_phase67_team_auto_ops(
        allow_flag_present=True,
        env=opened_env(),
        send_adapter=sender,
    )
    assert_true(sender.calls == 0, "Consumed auto-ops must not call sender")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["blocked_reasons"] == ["phase67_team_auto_ops_already_consumed"], "Consumed reason")
    assert_true(report["actual_team_auto_ops_executed"] is False, "No execution")
    assert_true(report["real_team_auto_ops_send_performed"] is False, "No real send")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")
    assert_true(report["ready_for_repeat_team_auto_ops"] is False, "No repeat")


def test_public_unknown_high_risk_and_multi_message_blocked() -> None:
    cases = (
        ({"channel_scope": "public"}, "public_channel_blocked"),
        ({"channel_scope": "unknown", "known_team_channel": False}, "known_team_channel_required"),
        ({"intent": "legal_financial_advice"}, "high_risk_intent_blocked"),
        ({"message_count": 2}, "max_one_reply_per_event_required"),
    )
    for event, reason in cases:
        report = build_actual_phase67_team_auto_ops(
            allow_flag_present=True,
            env=opened_env(),
            event=event,
            phase67_team_auto_ops_already_consumed=False,
        )
        assert_true(report["blocked"] is True, "Blocked")
        assert_true(reason in report["blocked_reasons"], reason)
        assert_true(report["actual_team_auto_ops_executed"] is False, "No execution")
        assert_true(report["message_sent_count"] == 0, "No send")


def test_phase60_lock_and_level_matrix() -> None:
    report = build_phase67_72_supervised_team_auto_ops()
    assert_true(report["phase60_team_canary_verified_once"] is True, "Phase60 verified")
    assert_true(report["phase60_repeat_team_canary_locked"] is True, "Phase60 lock")
    assert_true(report["current_verified_level"] == "level4_low_risk_team_channel_canary_verified_once", "Current level")
    assert_true(report["next_target_level"] == "level4_supervised_team_channel_auto_ops", "Next target")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")
    assert_true(report["autonomy_matrix"]["level_4_auto_ops"] == "supervised_team_channel_auto_ops_prepared_not_executed", "Level 4 prep")


def test_no_external_or_sensitive_values() -> None:
    report = build_phase67_72_supervised_team_auto_ops()
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
        "team_channel_id_value_logged",
    ):
        assert_true(report[key] is False, key)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase67_path_available_and_default_blocked,
        test_fake_sender_success_exactly_once,
        test_phase67_actual_success_historical_closeout,
        test_repeat_actual_blocks_even_with_open_gate,
        test_public_unknown_high_risk_and_multi_message_blocked,
        test_phase60_lock_and_level_matrix,
        test_no_external_or_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase67-72 supervised team auto-ops tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
