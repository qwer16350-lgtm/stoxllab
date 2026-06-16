from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40t_readonly_runtime_closeout import (
    build_phase40t_readonly_runtime_closeout,
    render_phase40t_readonly_runtime_closeout_markdown,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def snapshot() -> dict[str, object]:
    return {
        "snapshot_type": "phase40t_readonly_preflight_snapshot",
        "version": "phase40t_readonly_preflight_snapshot",
        "preflight_passed": True,
        "discord_token_present": True,
        "private_test_channel_id_present": True,
        "approval_actualized": True,
        "approval_phrase_present": True,
        "approval_phrase_exact_match": True,
        "send_messages_enabled": False,
        "private_test_reply_enabled": False,
        "reply_mode_readonly_private_test_only": True,
        "llm_disabled": True,
        "rag_disabled": True,
        "embedding_disabled": True,
        "external_execution": False,
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_content_logged": False,
        "secret_values_logged": False,
    }


def test_empty_closeout_not_executed() -> None:
    report = build_phase40t_readonly_runtime_closeout()
    assert_true(report["started"] is False, "Not started")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["capture_file_written"] is False, "No file")
    assert_true(report["message_sent_count"] == 0, "No send count")
    assert_true(report["ready_for_phase41_reply_runtime"] is False, "No phase41")


def test_fake_success_closeout_no_send_or_raw_values() -> None:
    report = build_phase40t_readonly_runtime_closeout(
        started=True,
        gateway_connected=True,
        exit_reason="timeout",
        captured_event_count=1,
        captured_private_test_human_message_count=1,
        capture_file_written=True,
        capture_file_path_logged=True,
        preflight_snapshot=snapshot(),
    )
    text = json.dumps(report, ensure_ascii=False)
    assert_true(report["started"] is True, "Started")
    assert_true(report["discord_gateway_connected"] is True, "Gateway")
    assert_true(report["ready_for_capture_closeout"] is True, "Ready closeout")
    assert_true(report["discord_api_send_called"] is False, "No API send")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["preflight_snapshot_preserved"] is True, "Snapshot preserved")
    assert_true(report["presence_consistency_verified"] is True, "Presence consistent")
    assert_true(report["llm_called"] is False and report["rag_called"] is False, "No LLM/RAG")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_closeout_markdown() -> None:
    assert_true("Phase 40T" in render_phase40t_readonly_runtime_closeout_markdown(build_phase40t_readonly_runtime_closeout()), "Markdown")


def main() -> int:
    for test in (test_empty_closeout_not_executed, test_fake_success_closeout_no_send_or_raw_values, test_closeout_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40T runtime closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
