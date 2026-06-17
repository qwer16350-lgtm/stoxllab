from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase59_supervised_private_test_auto_reply import (
    APPROVAL_PHRASE,
    REPLY_MODE,
    Phase59SendResult,
    build_actual_phase59_supervised_private_test_auto_reply,
    build_phase59_supervised_private_test_auto_reply_blocked_report,
    build_phase59_supervised_private_test_auto_reply_preflight,
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


class FakePhase59Sender:
    def __init__(self) -> None:
        self.calls = 0

    def send_supervised_reply(self, content: str) -> Phase59SendResult:
        self.calls += 1
        assert_true("Phase59" in content, "Deterministic content")
        return Phase59SendResult(api_send_called=True, message_sent=True, message_sent_count=1, status_code=200)


def test_closed_gate_blocked() -> None:
    report = build_phase59_supervised_private_test_auto_reply_preflight({})
    assert_true(report["report_type"] == "phase59_supervised_private_test_auto_reply_preflight", "Report type")
    assert_true(report["phase59_actual_path_available"] is True, "Actual path")
    assert_true(report["phase59_sender_adapter_wired"] is True, "Sender adapter wired")
    assert_true(report["manual_gate_required"] is True, "Manual gate")
    assert_true(report["private_test_only"] is True, "Private test")
    assert_true(report["ready_for_actual_phase59_supervised_auto_reply"] is False, "Closed gate")
    assert_true(report["message_sent_count"] == 0, "No send")


def test_allow_missing_blocked() -> None:
    report = build_actual_phase59_supervised_private_test_auto_reply(env=opened_env())
    assert_true(report["blocked"] is True, "Blocked")
    assert_true("allow_flag_missing" in report["blocked_reasons"], "Allow missing")
    assert_true("send_adapter_required_for_actual_manual_gate" not in report["blocked_reasons"], "Sender adapter is wired")
    assert_true(report["actual_supervised_auto_reply_executed"] is False, "No execution")


def test_env_missing_blocked() -> None:
    report = build_phase59_supervised_private_test_auto_reply_blocked_report(allow_flag_present=True, env={})
    assert_true(report["blocked"] is True, "Blocked")
    assert_true("manual_approval_not_approved" in report["blocked_reasons"], "Env missing")
    assert_true(report["message_sent_count"] == 0, "No send")


def test_fake_sender_success_exactly_once() -> None:
    sender = FakePhase59Sender()
    report = build_actual_phase59_supervised_private_test_auto_reply(
        allow_flag_present=True,
        env=opened_env(),
        send_adapter=sender,
        phase59_session_already_consumed=False,
    )
    assert_true(sender.calls == 1, "One fake send")
    assert_true(report["blocked"] is False, "Not blocked")
    assert_true(report["fake_sender_adapter_used"] is True, "Fake sender used")
    assert_true(report["real_discord_sender_adapter_selected"] is False, "Real sender not selected in test")
    assert_true(report["actual_supervised_auto_reply_executed"] is True, "Executed")
    assert_true(report["sent_scope"] == "private_test_only", "Private scope")
    assert_true(report["reply_text_source"] == "deterministic_template", "Deterministic")
    assert_true(report["discord_api_send_called"] is True, "Fake API")
    assert_true(report["discord_message_sent"] is True, "Fake sent")
    assert_true(report["message_sent_count"] == 1, "Exactly one")
    assert_true(report["max_reply_count_respected"] is True, "Reply max")
    assert_true(report["max_send_count_respected"] is True, "Send max")
    assert_true(report["self_loop_guard_active"] is True, "Self guard")
    assert_true(report["duplicate_guard_active"] is True, "Duplicate guard")
    assert_true(report["bot_message_guard_active"] is True, "Bot guard")
    assert_true(report["ready_for_repeat_session"] is False, "No repeat")
    assert_true(report["ready_for_phase59_manual_gate"] is True, "Manual gate")


def test_guards_skip_self_bot_duplicate() -> None:
    for event in ({"author_type": "self"}, {"author_type": "bot"}, {"duplicate": True}, {"channel_scope": "team"}):
        report = build_actual_phase59_supervised_private_test_auto_reply(allow_flag_present=True, env=opened_env(), event=event)
        assert_true(report["blocked"] is True, "Guard blocks")
        assert_true(report["actual_supervised_auto_reply_executed"] is False, "No execution")
        assert_true(report["message_sent_count"] == 0, "No send")


def test_no_external_or_raw_values() -> None:
    report = build_phase59_supervised_private_test_auto_reply_preflight(opened_env())
    for key in (
        "actual_discord_runtime_executed",
        "discord_gateway_connected",
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
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_closed_gate_blocked,
        test_allow_missing_blocked,
        test_env_missing_blocked,
        test_fake_sender_success_exactly_once,
        test_guards_skip_self_bot_duplicate,
        test_no_external_or_raw_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase59 supervised private-test auto-reply tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
