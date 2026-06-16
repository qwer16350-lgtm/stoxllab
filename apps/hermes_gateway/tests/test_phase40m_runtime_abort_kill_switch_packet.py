from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40m_runtime_abort_kill_switch_packet import build_phase40m_runtime_abort_kill_switch_packet, render_phase40m_runtime_abort_kill_switch_packet_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40m_abort_guards_present() -> None:
    report = build_phase40m_runtime_abort_kill_switch_packet()
    for key in ("manual_abort_available", "abort_on_any_send_attempt", "abort_on_public_team_channel_event", "abort_on_unexpected_reply_mode", "abort_on_llm_enabled", "abort_on_rag_enabled", "abort_on_external_execution_enabled"):
        assert_true(report[key] is True, f"{key} true")
    assert_true("HERMES_DISCORD_SEND_MESSAGES=false" in report["kill_switch_envs"], "Send kill switch")
    assert_true("HERMES_DISCORD_PRIVATE_TEST_REPLY=false" in report["kill_switch_envs"], "Reply kill switch")


def test_phase40m_no_send_or_runtime() -> None:
    report = build_phase40m_runtime_abort_kill_switch_packet()
    for key in ("live_runtime_started", "discord_gateway_connected", "discord_api_send_called", "discord_message_sent", "reply_send_allowed", "llm_api_call_attempted", "rag_called", "external_execution", "unattended_auto_reply_allowed"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase40m_markdown() -> None:
    assert_true("Phase 40M" in render_phase40m_runtime_abort_kill_switch_packet_markdown(build_phase40m_runtime_abort_kill_switch_packet()), "Markdown")


def main() -> int:
    for test in (test_phase40m_abort_guards_present, test_phase40m_no_send_or_runtime, test_phase40m_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40M kill-switch tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
