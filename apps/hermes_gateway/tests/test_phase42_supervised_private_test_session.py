from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase42_supervised_private_test_session import build_phase42_supervised_private_test_session_preflight


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase42_default_blocked_no_runtime() -> None:
    report = build_phase42_supervised_private_test_session_preflight()
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["manual_gate_required"] is True, "Manual gate required")
    assert_true(report["manual_gate_open"] is False, "Manual gate closed")
    assert_true(report["actual_supervised_session_executed"] is False, "No supervised session")
    assert_true("max_reply_count_required" in report["blocked_reasons"], "Max count required")
    assert_true("max_session_messages_required" in report["blocked_reasons"], "Max session messages required")
    assert_true("max_send_count_required" in report["blocked_reasons"], "Max send count required")
    assert_true("timeout_required" in report["blocked_reasons"], "Timeout required")
    assert_true("cooldown_required" in report["blocked_reasons"], "Cooldown required")
    assert_true(report["private_test_channel_only"] is True, "Private-test only")
    assert_true(report["public_team_blocked"] is True, "Public/team blocked")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["ready_for_phase42_manual_supervised_session"] is False, "No manual readiness")
    assert_true(report["ready_for_phase41b_repeat_send"] is False, "No 41B repeat")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["actual_runtime_executed"] is False, "No runtime")


def test_phase42_gate_values_do_not_open_runtime() -> None:
    report = build_phase42_supervised_private_test_session_preflight(
        {
            "HERMES_PHASE42_SUPERVISED_SESSION_APPROVED": "true",
            "HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE": "I_APPROVE_PHASE42_SUPERVISED_PRIVATE_TEST_SESSION",
            "HERMES_PHASE42_MAX_SESSION_MESSAGES": "3",
            "HERMES_PHASE42_MAX_REPLY_COUNT": "2",
            "HERMES_PHASE42_MAX_SEND_COUNT": "2",
            "HERMES_PHASE42_TIMEOUT_SECONDS": "60",
            "HERMES_PHASE42_COOLDOWN_SECONDS": "5",
            "HERMES_DISCORD_REPLY_MODE": "private_test_only",
            "HERMES_PHASE42_DETERMINISTIC_REPLY_ONLY": "true",
            "HERMES_PHASE42_FROZEN_REPLY_ONLY": "true",
        }
    )
    assert_true(report["gate_checks_ready"] is True, "Gate checks ready")
    assert_true(report["blocked"] is True, "Still blocked")
    assert_true(report["manual_gate_open"] is False, "Manual gate not opened by preflight")
    assert_true(report["ready_for_phase42_manual_supervised_session"] is False, "Separate manual gate required")
    assert_true(report["actual_supervised_session_executed"] is False, "No runtime")
    assert_true(report["discord_message_sent"] is False, "No message")


def main() -> int:
    for test in (test_phase42_default_blocked_no_runtime, test_phase42_gate_values_do_not_open_runtime):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 42 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
