from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40n_phase41_reply_runtime_entry_gate import build_phase40n_phase41_reply_runtime_entry_gate, render_phase40n_phase41_reply_runtime_entry_gate_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40n_phase41_gate_blocked_by_default() -> None:
    report = build_phase40n_phase41_reply_runtime_entry_gate()
    assert_true(report["phase41_reply_runtime_entry_gate_available"] is True, "Gate available")
    assert_true(report["phase41_reply_runtime_allowed"] is False, "Phase 41 blocked")
    assert_true(report["ready_for_phase41_reply_runtime"] is False, "Not ready")
    for item in ("phase40j manual readonly runtime completed", "phase40l live capture closeout completed", "no additional send during readonly runtime", "captured event audit passed", "operator approves one private-test reply runtime"):
        assert_true(item in report["required_before_phase41"], f"{item} required")


def test_phase40n_reply_llm_rag_blocked() -> None:
    report = build_phase40n_phase41_reply_runtime_entry_gate()
    for key in ("reply_send_allowed", "llm_reply_allowed", "rag_reply_allowed", "unattended_auto_reply_allowed", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase40n_markdown() -> None:
    assert_true("Phase 40N" in render_phase40n_phase41_reply_runtime_entry_gate_markdown(build_phase40n_phase41_reply_runtime_entry_gate()), "Markdown")


def main() -> int:
    for test in (test_phase40n_phase41_gate_blocked_by_default, test_phase40n_reply_llm_rag_blocked, test_phase40n_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40N Phase 41 gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
