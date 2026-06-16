from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40k_readonly_runtime_launch_packet import PLANNED_COMMAND, build_phase40k_readonly_runtime_launch_packet, render_phase40k_readonly_runtime_launch_packet_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40k_launch_packet_manual_only() -> None:
    report = build_phase40k_readonly_runtime_launch_packet()
    assert_true(report["manual_launch_only"] is True, "Manual only")
    assert_true(report["codex_must_not_launch"] is True, "Codex must not launch")
    assert_true(report["planned_command"] == PLANNED_COMMAND, "Planned command")
    assert_true(report["planned_command_executed_by_codex"] is False, "Codex did not execute")
    assert_true(report["ready_for_manual_readonly_runtime_launch"] is False, "Not ready yet")
    assert_true(report["next_human_confirmation_required"] is True, "Human confirmation")


def test_phase40k_readonly_conditions() -> None:
    report = build_phase40k_readonly_runtime_launch_packet()
    assert_true(report["runtime_scope"] == "private_test_readonly", "Readonly scope")
    assert_true(report["send_messages_required_false"] is True, "Send false")
    assert_true(report["private_test_reply_required_false"] is True, "Reply false")
    assert_true(report["reply_mode"] == "readonly_private_test_only", "Readonly mode")
    for key in ("live_runtime_started", "discord_gateway_connected", "discord_api_send_called", "discord_message_sent", "reply_send_allowed", "llm_api_call_attempted", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase40k_markdown() -> None:
    assert_true("Phase 40K" in render_phase40k_readonly_runtime_launch_packet_markdown(build_phase40k_readonly_runtime_launch_packet()), "Markdown")


def main() -> int:
    for test in (test_phase40k_launch_packet_manual_only, test_phase40k_readonly_conditions, test_phase40k_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40K launch packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
