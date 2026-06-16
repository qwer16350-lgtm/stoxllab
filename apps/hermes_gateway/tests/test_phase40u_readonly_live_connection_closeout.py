from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40u_readonly_live_connection_closeout import build_phase40u_readonly_live_connection_closeout


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_readonly_timeout_closeout_success() -> None:
    report = build_phase40u_readonly_live_connection_closeout()
    assert_true(report["phase40t_live_connection_verified"] is True, "Connection verified")
    assert_true(report["gateway_login_verified"] is True, "Login verified")
    assert_true(report["gateway_connect_verified"] is True, "Gateway verified")
    assert_true(report["read_only_timeout_success"] is True, "Timeout success")
    assert_true(report["captured_event_count"] == 0, "No events")
    assert_true(report["capture_file_written"] is True, "Capture file written")
    assert_true(report["ready_for_phase41_dry_run_preparation"] is True, "Ready for dry-run")


def test_no_send_or_llm_rag_external() -> None:
    report = build_phase40u_readonly_live_connection_closeout()
    for key in ("discord_api_send_called", "discord_message_sent", "llm_called", "llm_api_call_attempted", "rag_called", "embedding_api_called", "external_execution", "ready_for_phase41_actual_reply_send"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No messages")


def test_no_sensitive_values() -> None:
    text = json.dumps(build_phase40u_readonly_live_connection_closeout(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true(not LONG_ID_RE.search(text), "No raw IDs")


def main() -> int:
    for test in (test_readonly_timeout_closeout_success, test_no_send_or_llm_rag_external, test_no_sensitive_values):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40U closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
