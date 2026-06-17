from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase52b_53_readonly_capture_closeout import build_phase52b_53_readonly_capture_closeout


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase52b_53_closeout_contract() -> None:
    report = build_phase52b_53_readonly_capture_closeout()
    assert_true(report["report_type"] == "phase52b_53_readonly_capture_closeout", "Report type")
    assert_true(report["manual_readonly_runtime_successfully_closed_out"] is True, "Runtime closeout")
    assert_true(report["gateway_connection_verified"] is True, "Gateway")
    assert_true(report["empty_capture_handled"] is True, "Empty")
    assert_true(report["capture_to_review_packet_replay_ready"] is True, "Replay")
    assert_true(report["review_packet_pipeline_ready_for_real_capture"] is True, "Pipeline")
    assert_true(report["ready_for_next_readonly_capture_canary_manual_gate"] is True, "Next")


def test_phase52b_53_closeout_no_external_actions() -> None:
    report = build_phase52b_53_readonly_capture_closeout()
    for key in ("ready_for_auto_reply", "ready_for_llm_reply", "ready_for_rag_reply", "ready_for_team_channel_auto_ops", "ready_for_production_unattended", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "scheduler_live_execution", "raw_content_logged", "raw_discord_ids_logged", "secret_values_logged"):
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "No messages")


def test_phase52b_53_closeout_no_sensitive_values() -> None:
    text = json.dumps(build_phase52b_53_readonly_capture_closeout(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase52b_53_closeout_contract, test_phase52b_53_closeout_no_external_actions, test_phase52b_53_closeout_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase52B/53 read-only capture closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
