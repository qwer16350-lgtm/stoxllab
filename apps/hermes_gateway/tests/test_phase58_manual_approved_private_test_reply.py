from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase58_manual_approved_private_test_reply import (
    APPROVAL_PHRASE,
    Phase58SendResult,
    REPLY_MODE,
    build_actual_phase58_manual_approved_private_test_reply,
    build_phase58_manual_approved_private_test_reply_closeout,
    build_phase58_manual_approved_private_test_reply_no_repeat_lock,
    build_phase58_manual_approved_private_test_reply_blocked_report,
    build_phase58_manual_approved_private_test_reply_preflight,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def opened_env() -> dict[str, str]:
    return {
        "HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVED": "true",
        "HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVAL_PHRASE": APPROVAL_PHRASE,
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


class FakePhase58Sender:
    def __init__(self) -> None:
        self.calls = 0

    def send_deterministic_reply(self, content: str) -> Phase58SendResult:
        self.calls += 1
        assert_true("Phase58" in content, "Deterministic content")
        return Phase58SendResult(api_send_called=True, message_sent=True, message_sent_count=1, status_code=200)


def test_closed_preflight_not_ready() -> None:
    report = build_phase58_manual_approved_private_test_reply_preflight({})
    assert_true(report["report_type"] == "phase58_manual_approved_private_test_reply_preflight", "Report type")
    assert_true(report["manual_gate_required"] is True, "Manual gate")
    assert_true(report["phase58_actual_path_available"] is True, "Actual path")
    assert_true(report["captured_event_count"] == 1, "Capture count")
    assert_true(report["review_packet_count"] == 1, "Review packet count")
    assert_true(report["mock_reply_packet_created"] is True, "Mock packet")
    assert_true(report["ready_for_actual_phase58_manual_reply"] is False, "Closed gate not ready")


def test_opened_fixture_preflight_ready() -> None:
    report = build_phase58_manual_approved_private_test_reply_preflight(opened_env(), phase58_reply_already_consumed=False)
    assert_true(report["approval_phrase_present"] is True, "Phrase present")
    assert_true(report["approval_phrase_exact_match"] is True, "Phrase match")
    assert_true(report["approval_phrase_value_logged"] is False, "Phrase hidden")
    assert_true(report["ready_for_actual_phase58_manual_reply"] is True, "Open fixture ready")


def test_actual_path_without_allow_flag_blocked() -> None:
    report = build_actual_phase58_manual_approved_private_test_reply(env=opened_env(), phase58_reply_already_consumed=False)
    assert_true(report["report_type"] == "phase58_manual_approved_private_test_reply_blocked", "Blocked report")
    assert_true(report["allow_flag_present"] is False, "No allow")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["blocked_reasons"] == ["allow_flag_missing"], "Allow missing")
    assert_true(report["actual_send_executed"] is False, "No send")
    assert_true(report["ready_for_repeat_send"] is False, "No repeat")


def test_manual_approval_missing_blocked() -> None:
    env = opened_env()
    env["HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVED"] = "false"
    report = build_actual_phase58_manual_approved_private_test_reply(allow_flag_present=True, env=env)
    assert_true(report["blocked"] is True, "Blocked")
    assert_true("manual_approval_not_approved" in report["blocked_reasons"], "Manual approval missing")
    assert_true(report["actual_send_executed"] is False, "No send")
    assert_true(report["message_sent_count"] == 0, "No message")


def test_safe_hotfix_never_sends_or_calls_external_services() -> None:
    report = build_phase58_manual_approved_private_test_reply_blocked_report(allow_flag_present=True, env=opened_env())
    for key in (
        "discord_api_send_called",
        "discord_message_sent",
        "actual_send_executed",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_live_execution",
    ):
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "No message")


def test_fake_sender_actual_path_succeeds_exactly_once() -> None:
    sender = FakePhase58Sender()
    report = build_actual_phase58_manual_approved_private_test_reply(
        allow_flag_present=True,
        env=opened_env(),
        send_adapter=sender,
        phase58_reply_already_consumed=False,
    )
    assert_true(sender.calls == 1, "Fake sender called once")
    assert_true(report["report_type"] == "phase58_manual_approved_private_test_reply_actual_send", "Actual report")
    assert_true(report["blocked"] is False, "Not blocked")
    assert_true(report["actual_send_executed"] is True, "Actual path executed")
    assert_true(report["sent_scope"] == "private_test_only", "Private scope")
    assert_true(report["reply_text_source"] == "deterministic_template", "Deterministic")
    assert_true(report["discord_api_send_called"] is True, "Fake API called")
    assert_true(report["discord_message_sent"] is True, "Fake sent")
    assert_true(report["message_sent_count"] == 1, "Exactly one")
    assert_true(report["ready_for_phase58_closeout"] is True, "Closeout ready")
    assert_true(report["ready_for_repeat_send"] is False, "No repeat")
    for key in ("llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "external_execution", "raw_content_logged", "raw_discord_ids_logged", "secret_values_logged"):
        assert_true(report[key] is False, key)


def test_deterministic_private_test_no_raw_values_and_count_invariant() -> None:
    report = build_phase58_manual_approved_private_test_reply_preflight(opened_env(), phase58_reply_already_consumed=False)
    assert_true(report["reply_text_source"] == "deterministic_template", "Deterministic")
    assert_true(report["private_test_only"] is True, "Private test")
    assert_true(report["raw_user_content_included"] is False, "No raw user content")
    assert_true(report["raw_content_logged"] is False, "No raw content")
    assert_true(report["raw_discord_ids_logged"] is False, "No raw IDs")
    assert_true(report["secret_values_logged"] is False, "No secrets")
    assert_true(report["message_sent_count"] <= 1, "Message max one")
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secret markers")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_phase58_closeout_metadata_and_no_repeat_lock() -> None:
    closeout = build_phase58_manual_approved_private_test_reply_closeout()
    assert_true(closeout["report_type"] == "phase58_manual_approved_private_test_reply_closeout", "Closeout report")
    assert_true(closeout["actual_phase58_reply_sent"] is True, "Historical send recorded")
    assert_true(closeout["message_sent_count"] == 1, "Historical count fixed")
    assert_true(closeout["discord_api_send_called"] is False, "Closeout no API")
    assert_true(closeout["discord_message_sent"] is False, "Closeout no message")
    assert_true(closeout["repeat_send_locked"] is True, "Repeat locked")
    assert_true(closeout["ready_for_repeat_send"] is False, "No repeat readiness")
    assert_true(closeout["ready_for_supervised_private_test_auto_reply_gate"] is True, "Next gate")
    lock = build_phase58_manual_approved_private_test_reply_no_repeat_lock()
    assert_true(lock["blocked_reasons"] == ["phase58_actual_manual_reply_already_consumed"], "Consumed reason")


def test_actual_command_blocks_after_phase58_consumed() -> None:
    report = build_actual_phase58_manual_approved_private_test_reply(
        allow_flag_present=True,
        env=opened_env(),
    )
    assert_true(report["blocked"] is True, "Consumed blocked")
    assert_true("phase58_actual_manual_reply_already_consumed" in report["blocked_reasons"], "Consumed reason")
    assert_true(report["actual_send_executed"] is False, "No repeat send")
    assert_true(report["message_sent_count"] == 0, "No repeat count")


def main() -> int:
    tests = [
        test_closed_preflight_not_ready,
        test_opened_fixture_preflight_ready,
        test_actual_path_without_allow_flag_blocked,
        test_manual_approval_missing_blocked,
        test_safe_hotfix_never_sends_or_calls_external_services,
        test_fake_sender_actual_path_succeeds_exactly_once,
        test_deterministic_private_test_no_raw_values_and_count_invariant,
        test_phase58_closeout_metadata_and_no_repeat_lock,
        test_actual_command_blocks_after_phase58_consumed,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase58 manual-approved private-test reply tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
