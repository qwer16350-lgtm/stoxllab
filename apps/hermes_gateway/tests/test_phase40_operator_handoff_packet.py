from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_operator_handoff_packet import build_phase40_operator_handoff_packet, render_phase40_operator_handoff_packet_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40g_operator_confirmations_required() -> None:
    report = build_phase40_operator_handoff_packet()
    assert_true(report["operator_must_confirm_before_live_runtime"] is True, "Live confirmation")
    assert_true(report["operator_must_confirm_before_any_reply_send"] is True, "Reply confirmation")
    for item in ("start_private_test_live_runtime", "allow_one_private_test_reply", "enable_llm_for_private_test_reply", "enable_rag_for_private_test_reply"):
        assert_true(item in report["required_future_confirmations"], f"{item} required")
    assert_true(report["safe_current_state"] is True, "Safe state")
    assert_true(report["ready_for_live_runtime_execution"] is False, "No live execution")


def test_phase40g_no_runtime_or_send() -> None:
    report = build_phase40_operator_handoff_packet()
    for key in ("discord_gateway_connected", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase40g_markdown() -> None:
    assert_true("Phase 40G" in render_phase40_operator_handoff_packet_markdown(build_phase40_operator_handoff_packet()), "Markdown")


def main() -> int:
    for test in (test_phase40g_operator_confirmations_required, test_phase40g_no_runtime_or_send, test_phase40g_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40G operator handoff tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
