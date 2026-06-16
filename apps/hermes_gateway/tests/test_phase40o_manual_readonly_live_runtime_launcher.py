from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40k_readonly_runtime_launch_packet import PLANNED_COMMAND
from phase40o_manual_readonly_live_runtime_launcher import build_phase40o_manual_readonly_live_runtime_launcher, render_phase40o_manual_readonly_live_runtime_launcher_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40o_launcher_report_only() -> None:
    report = build_phase40o_manual_readonly_live_runtime_launcher()
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["manual_launch_only"] is True, "Manual launch")
    assert_true(report["codex_must_not_launch"] is True, "Codex no launch")
    assert_true(report["planned_command"] == PLANNED_COMMAND, "Planned command")
    assert_true(report["planned_command_executed_by_codex"] is False, "Not executed")


def test_phase40o_no_live_or_send() -> None:
    report = build_phase40o_manual_readonly_live_runtime_launcher()
    for key in ("live_runtime_started", "discord_gateway_connected", "discord_api_send_called", "discord_message_sent", "ready_for_manual_readonly_runtime_launch", "ready_for_reply_send", "reply_send_allowed", "llm_api_call_attempted", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["phase39_actual_send_count_locked"] == 1, "Phase39 count")
    assert_true(report["additional_send_count"] == 0, "No additional")
    assert_true(report["message_sent_count"] == 0, "No message")


def test_phase40o_markdown() -> None:
    assert_true("Phase 40O" in render_phase40o_manual_readonly_live_runtime_launcher_markdown(build_phase40o_manual_readonly_live_runtime_launcher()), "Markdown")


def main() -> int:
    for test in (test_phase40o_launcher_report_only, test_phase40o_no_live_or_send, test_phase40o_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40O launcher tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
