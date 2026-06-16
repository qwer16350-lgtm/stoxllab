from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40r_phase41_reply_preflight_matrix import build_phase40r_phase41_reply_preflight_matrix, render_phase40r_phase41_reply_preflight_matrix_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40r_blocked_by_default() -> None:
    report = build_phase40r_phase41_reply_preflight_matrix()
    assert_true(report["phase41_reply_runtime_entry_available"] is True, "Entry available")
    assert_true(report["phase41_reply_runtime_allowed"] is False, "Phase41 blocked")
    assert_true(report["ready_for_phase41_reply_runtime"] is False, "Not ready")
    assert_true("Phase 40Q capture review closeout completed" in report["required_before_phase41_reply"], "Capture required")


def test_phase40r_reply_llm_rag_send_false() -> None:
    report = build_phase40r_phase41_reply_preflight_matrix()
    for key in ("reply_text_generation_allowed", "llm_reply_allowed", "rag_reply_allowed", "discord_reply_send_allowed", "reply_send_allowed", "unattended_auto_reply_allowed", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message")


def test_phase40r_markdown() -> None:
    assert_true("Phase 40R" in render_phase40r_phase41_reply_preflight_matrix_markdown(build_phase40r_phase41_reply_preflight_matrix()), "Markdown")


def main() -> int:
    for test in (test_phase40r_blocked_by_default, test_phase40r_reply_llm_rag_send_false, test_phase40r_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40R matrix tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
