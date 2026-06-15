from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase39c_no_repeat_send_lock import build_phase39c_no_repeat_send_lock, render_phase39c_no_repeat_send_lock_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_no_repeat_lock_counts() -> None:
    report = build_phase39c_no_repeat_send_lock()
    assert_true(report["actual_discord_send_count_locked"] == 1, "Locked count")
    assert_true(report["max_allowed_actual_send_count"] == 1, "Max count")
    assert_true(report["phase39c_closeout_completed"] is True, "Closeout complete")


def test_no_repeat_lock_blocks_repeat_retry_unattended() -> None:
    report = build_phase39c_no_repeat_send_lock()
    for key in ("repeat_send_allowed", "automatic_retry_allowed", "manual_retry_allowed", "unattended_auto_reply_allowed", "ready_for_repeat_send"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["send_gate_must_remain_off"] is True, "Send gate off")
    assert_true(report["real_execution_env_must_remain_off"] is True, "Real env off")
    assert_true(report["approval_gate_must_remain_off"] is True, "Approval off")


def test_no_repeat_lock_no_phase39c_send_or_external() -> None:
    report = build_phase39c_no_repeat_send_lock()
    for key in ("discord_api_send_called_in_phase39c", "discord_message_sent_in_phase39c", "new_llm_api_call_attempted", "new_llm_api_called", "llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "public_channel_send_allowed", "team_channel_send_allowed", "public_channel_reply_allowed", "team_channel_reply_allowed"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count_in_phase39c"] == 0, "No Phase39C message")


def test_no_repeat_lock_no_sensitive_values_and_markdown() -> None:
    report = build_phase39c_no_repeat_send_lock()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Phase 39C No-repeat Send Lock" in render_phase39c_no_repeat_send_lock_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_no_repeat_lock_counts,
        test_no_repeat_lock_blocks_repeat_retry_unattended,
        test_no_repeat_lock_no_phase39c_send_or_external,
        test_no_repeat_lock_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39C no-repeat send lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
