from __future__ import annotations

import json
import re
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase39b_manual_send_reentry_packet import build_phase39b_manual_send_reentry_packet, render_phase39b_manual_send_reentry_packet_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase39b_reentry_packet_report_only() -> None:
    report = build_phase39b_manual_send_reentry_packet()
    assert_true(report["report_type"] == "phase39b_manual_send_reentry_packet", "Report type")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["allow_flag_cli_available"] is True, "Allow flag available")
    assert_true(report["allow_flag_parser_error_fixed"] is True, "Parser fixed")
    assert_true(report["codex_session_env_isolated_from_user_powershell"] is True, "Env separation")
    assert_true(report["actual_send_must_be_run_from_same_user_powershell_session"] is True, "Same session required")
    assert_true("--allow-actual-private-test-send" in report["readiness_command"], "Readiness command")
    assert_true("--execute-actual-private-test-send" in report["execution_gate_command"], "Execution gate command")
    assert_true(report["execution_gate_command_report_only"] is True, "Execution gate report only")
    assert_true(report["actual_execution_adapter"] == "mock", "Mock adapter")
    assert_true(report["real_discord_send_execution_env_required_for_future_real_send"] == "HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION", "Future env key")


def test_phase39b_reentry_packet_never_sends() -> None:
    report = build_phase39b_manual_send_reentry_packet()
    for key in (
        "actual_send_executed",
        "actual_private_test_send_executed",
        "discord_live_runtime_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "repeat_send_allowed",
        "automatic_retry_allowed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "ready_for_phase39b_actual_send_manual_attempt",
        "ready_for_phase39c_send_closeout",
    ):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase39b_reentry_packet_no_sensitive_values() -> None:
    report = build_phase39b_manual_send_reentry_packet()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("i_approve_" not in text, "No approval phrase value")
    assert_true("sk-" not in text, "No API key")
    assert_true("token:" not in text, "No token")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw long IDs")


def test_phase39b_reentry_packet_markdown() -> None:
    markdown = render_phase39b_manual_send_reentry_packet_markdown(build_phase39b_manual_send_reentry_packet())
    assert_true("Phase 39B Manual Send Re-entry Packet" in markdown, "Markdown title")
    assert_true("Discord API send called: false" in markdown, "Markdown no send")


def main() -> int:
    tests = [
        test_phase39b_reentry_packet_report_only,
        test_phase39b_reentry_packet_never_sends,
        test_phase39b_reentry_packet_no_sensitive_values,
        test_phase39b_reentry_packet_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39B manual send re-entry packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
