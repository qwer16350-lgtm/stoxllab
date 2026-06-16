from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40s_morning_review_operator_decision_packet import build_phase40s_morning_review_operator_decision_packet, render_phase40s_morning_review_operator_decision_packet_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40s_morning_review_requires_confirmation() -> None:
    report = build_phase40s_morning_review_operator_decision_packet()
    assert_true(report["safe_to_review_next_morning"] is True, "Safe")
    assert_true(report["requires_user_confirmation"] is True, "Confirmation")
    assert_true(report["phase39_actual_send_count_locked"] == 1, "Phase39 count")
    assert_true(report["additional_discord_send_count"] == 0, "No additional")
    assert_true(report["recommended_next_phase"] == "Phase 40O manual read-only live runtime launch by user", "Recommended")


def test_phase40s_no_overnight_side_effects() -> None:
    report = build_phase40s_morning_review_operator_decision_packet()
    for key in ("overnight_external_actions_executed_by_codex", "live_runtime_started_by_codex", "reply_send_allowed", "phase41_reply_runtime_allowed", "discord_gateway_connected", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "rag_called", "external_execution", "raw_content_logged", "raw_discord_ids_logged", "secret_values_logged"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message")


def test_phase40s_markdown() -> None:
    assert_true("Phase 40S" in render_phase40s_morning_review_operator_decision_packet_markdown(build_phase40s_morning_review_operator_decision_packet()), "Markdown")


def main() -> int:
    for test in (test_phase40s_morning_review_requires_confirmation, test_phase40s_no_overnight_side_effects, test_phase40s_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40S morning review tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
