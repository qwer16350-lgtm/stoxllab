from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase74_limited_auto_mode_prep import (
    APPROVAL_PHRASE,
    REPLY_MODE,
    Phase74LimitedAutoSessionResult,
    build_actual_phase74_limited_auto_mode,
    build_phase74_limited_auto_mode_preflight,
    build_phase74_limited_auto_mode_prep,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def opened_env() -> dict[str, str]:
    return {
        "HERMES_PHASE74_LIMITED_AUTO_APPROVED": "true",
        "HERMES_PHASE74_LIMITED_AUTO_APPROVAL_PHRASE": APPROVAL_PHRASE,
        "HERMES_PHASE74_LIMITED_AUTO_CHANNEL_ID": "known-team-channel",
        "HERMES_PHASE74_LIMITED_AUTO_KILL_SWITCH_READY": "true",
        "HERMES_PHASE74_LIMITED_AUTO_MAX_SESSION_SECONDS": "60",
        "HERMES_PHASE74_LIMITED_AUTO_MAX_SEND_COUNT": "1",
        "HERMES_PHASE74_LIMITED_AUTO_MAX_REPLY_COUNT": "1",
        "HERMES_PHASE74_LIMITED_AUTO_COOLDOWN_SECONDS": "30",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_REPLY_MODE": REPLY_MODE,
        "HERMES_DISCORD_LLM_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_EMBEDDING_ENABLED": "false",
        "HERMES_VECTOR_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "HERMES_SCHEDULER_LIVE_ENABLED": "false",
    }


class FakeLimitedAutoSession:
    def __init__(self) -> None:
        self.calls = 0

    def run_limited_auto_session(self, content: str, *, max_session_seconds: int) -> Phase74LimitedAutoSessionResult:
        self.calls += 1
        assert_true("Phase74" in content, "Deterministic content")
        assert_true(max_session_seconds == 60, "Bounded seconds passed")
        return Phase74LimitedAutoSessionResult(
            api_send_called=True,
            message_sent=True,
            message_sent_count=1,
            reply_count=1,
            session_seconds=10,
            cooldown_respected=True,
        )


def test_phase74_limited_auto_path_and_policy_capsule() -> None:
    report = build_phase74_limited_auto_mode_prep()
    assert_true(report["phase74_limited_auto_mode_path_available"] is True, "Path available")
    assert_true(report["policy_capsule_available"] is True, "Policy capsule")
    assert_true(report["limited_auto_mode_manual_gate_required"] is True, "Manual gate")
    assert_true(report["known_team_channel_required"] is True, "Known team channel required")
    assert_true(report["low_risk_intent_required"] is True, "Low risk required")
    assert_true(report["deterministic_template_only"] is True, "Deterministic")
    assert_true(report["ops_queue_required"] is True, "Ops queue")
    assert_true(report["review_packet_required"] is True, "Review packet")
    assert_true(report["human_override_available"] is True, "Human override")
    assert_true(report["kill_switch_required"] is True, "Kill switch")
    assert_true(report["session_bounds_required"] is True, "Session bounds")
    assert_true(report["cooldown_required"] is True, "Cooldown")


def test_default_actual_blocked_without_send() -> None:
    report = build_actual_phase74_limited_auto_mode(env=opened_env())
    assert_true(report["report_type"] == "phase74_limited_auto_mode_blocked", "Blocked report")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["actual_limited_auto_mode_executed"] is False, "No execution")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No count")
    assert_true(report["session_executed"] is False, "No session")


def test_manual_gate_preflight_requirements() -> None:
    report = build_phase74_limited_auto_mode_preflight(env=opened_env())
    assert_true(report["preflight_passed"] is True, "Preflight")
    assert_true(report["manual_gate_required"] is True, "Manual gate")
    assert_true(report["known_team_channel_only"] is True, "Known")
    assert_true(report["low_risk_intent"] is True, "Low risk")
    assert_true(report["session_seconds_bounded"] is True, "Bounded")
    assert_true(report["max_send_count_configured"] is True, "Max send")
    assert_true(report["max_reply_count_configured"] is True, "Max reply")
    assert_true(report["cooldown_configured"] is True, "Cooldown")
    assert_true(report["kill_switch_ready"] is True, "Kill switch")


def test_fake_limited_session_exactly_once() -> None:
    session = FakeLimitedAutoSession()
    report = build_actual_phase74_limited_auto_mode(
        allow_flag_present=True,
        env=opened_env(),
        session_adapter=session,
        force_separate_manual_gate=False,
    )
    assert_true(session.calls == 1, "One fake session")
    assert_true(report["blocked"] is False, "Not blocked")
    assert_true(report["fake_limited_auto_session_executed"] is True, "Fake executed")
    assert_true(report["actual_limited_auto_mode_executed"] is True, "Executed semantic")
    assert_true(report["sent_scope"] == "known_team_channel_only", "Team scope")
    assert_true(report["reply_text_source"] == "deterministic_template", "Template")
    assert_true(report["discord_api_send_called"] is True, "Fake API")
    assert_true(report["discord_message_sent"] is True, "Fake message")
    assert_true(report["message_sent_count"] == 1, "Max one send")
    assert_true(report["reply_count"] == 1, "Max one reply")
    assert_true(report["session_seconds_bounded"] is True, "Bounded")
    assert_true(report["cooldown_respected"] is True, "Cooldown")
    assert_true(report["ready_for_repeat_limited_auto_mode"] is False, "No repeat")
    assert_true(report["public_channel_send_allowed"] is False, "No public")
    assert_true(report["unknown_channel_send_allowed"] is False, "No unknown")


def test_public_unknown_high_risk_and_multi_message_blocked() -> None:
    cases = (
        ({"channel_scope": "public"}, "known_team_channel_required"),
        ({"channel_scope": "unknown", "known_team_channel": False}, "known_team_channel_required"),
        ({"intent": "legal_financial_advice"}, "high_risk_intent_blocked"),
        ({"message_count": 2}, "max_one_reply_per_event_required"),
    )
    for event, reason in cases:
        report = build_actual_phase74_limited_auto_mode(
            allow_flag_present=True,
            env=opened_env(),
            event=event,
            force_separate_manual_gate=False,
        )
        assert_true(report["blocked"] is True, "Blocked")
        assert_true(reason in report["blocked_reasons"], reason)
        assert_true(report["actual_limited_auto_mode_executed"] is False, "No execution")
        assert_true(report["message_sent_count"] == 0, "No send")


def test_phase67_lock_level_matrix_and_production_false() -> None:
    report = build_phase74_limited_auto_mode_prep()
    assert_true(report["phase67_team_auto_ops_verified_once"] is True, "Phase67 verified")
    assert_true(report["phase67_repeat_team_auto_ops_locked"] is True, "Phase67 lock")
    assert_true(report["current_verified_level"] == "level4_supervised_team_channel_auto_ops_verified_once", "Current")
    assert_true(report["next_target_level"] == "level4_limited_auto_mode_short_run", "Next")
    assert_true(report["autonomy_level_matrix"]["level_1"] == "read_only_observation_verified", "Level 1")
    assert_true(report["autonomy_level_matrix"]["level_2"] == "manual_deterministic_reply_verified", "Level 2")
    assert_true(report["autonomy_level_matrix"]["level_3"] == "supervised_private_test_auto_reply_verified", "Level 3")
    assert_true(report["autonomy_level_matrix"]["level_4_canary"] == "low_risk_team_channel_canary_verified_once", "Level 4 canary")
    assert_true(report["autonomy_level_matrix"]["level_4_auto_ops"] == "supervised_team_channel_auto_ops_verified_once", "Level 4 auto ops")
    assert_true(report["autonomy_level_matrix"]["level_4_limited_auto"] == "limited_auto_mode_prepared_not_executed", "Level 4 limited")
    assert_true(report["autonomy_level_matrix"]["level_5"] == "production_unattended_not_ready", "Level 5")
    assert_true(report["ready_for_production_unattended"] is False, "Production false")


def test_no_external_or_sensitive_values_in_cli_reports() -> None:
    reports = [
        build_phase74_limited_auto_mode_preflight(),
        build_actual_phase74_limited_auto_mode(env=opened_env(), allow_flag_present=True),
        build_phase74_limited_auto_mode_prep(),
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
            "team_channel_id_value_logged",
        ):
            assert_true(report[key] is False, key)
        assert_true(report["message_sent_count"] == 0, "No CLI send")
        text = json.dumps(report, ensure_ascii=False).lower()
        assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
        assert_true("i_approve_" not in text, "No approval phrase")
        assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase74_limited_auto_path_and_policy_capsule,
        test_default_actual_blocked_without_send,
        test_manual_gate_preflight_requirements,
        test_fake_limited_session_exactly_once,
        test_public_unknown_high_risk_and_multi_message_blocked,
        test_phase67_lock_level_matrix_and_production_false,
        test_no_external_or_sensitive_values_in_cli_reports,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase74 limited auto mode prep tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
