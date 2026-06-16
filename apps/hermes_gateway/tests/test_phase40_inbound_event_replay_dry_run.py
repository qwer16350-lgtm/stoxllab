from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_inbound_event_replay_dry_run import build_phase40_inbound_event_replay_dry_run, render_phase40_inbound_event_replay_dry_run_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40c_uses_synthetic_replay_only() -> None:
    report = build_phase40_inbound_event_replay_dry_run()
    assert_true(report["uses_recorded_or_synthetic_events_only"] is True, "Synthetic only")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["live_runtime_started"] is False, "No runtime")
    assert_true(report["message_sent_count"] == 0, "No send count")


def test_phase40c_replay_decisions_are_safe() -> None:
    report = build_phase40_inbound_event_replay_dry_run()
    for key in ("synthetic_human_message_processed", "synthetic_self_message_skipped", "synthetic_bot_message_skipped", "synthetic_duplicate_message_skipped", "synthetic_public_channel_message_blocked", "synthetic_team_channel_message_blocked"):
        assert_true(report[key] is True, f"{key} true")
    assert_true(report["discord_api_send_called"] is False, "No send API")
    assert_true(report["discord_message_sent"] is False, "No message sent")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM")
    assert_true(report["rag_called"] is False, "No RAG")


def test_phase40c_markdown() -> None:
    assert_true("Phase 40C" in render_phase40_inbound_event_replay_dry_run_markdown(build_phase40_inbound_event_replay_dry_run()), "Markdown")


def main() -> int:
    for test in (test_phase40c_uses_synthetic_replay_only, test_phase40c_replay_decisions_are_safe, test_phase40c_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40C inbound event replay dry-run tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
