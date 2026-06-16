from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40j_private_test_readonly_runtime_preflight import build_phase40j_private_test_readonly_runtime_preflight, render_phase40j_private_test_readonly_runtime_preflight_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40j_preflight_report_only_and_no_live() -> None:
    report = build_phase40j_private_test_readonly_runtime_preflight()
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase39_actual_send_count_locked"] == 1, "Phase 39 count locked")
    assert_true(report["phase40_readiness_completed"] is True, "Phase 40 complete")
    assert_true(report["readonly_runtime_preflight_available"] is True, "Preflight available")
    assert_true(report["live_runtime_started"] is False, "No live runtime")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_api_send_called"] is False, "No send API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_phase40j_conditions_and_no_reply_readiness() -> None:
    report = build_phase40j_private_test_readonly_runtime_preflight()
    conditions = set(report["required_future_runtime_conditions"])
    for item in ("DISCORD_BOT_TOKEN present", "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID present", "HERMES_DISCORD_SEND_MESSAGES=false", "HERMES_DISCORD_PRIVATE_TEST_REPLY=false", "HERMES_DISCORD_REPLY_MODE=readonly_private_test_only", "LLM false", "RAG false", "embedding false", "external false"):
        assert_true(item in conditions, f"{item} required")
    assert_true(report["ready_for_manual_readonly_runtime_launch"] is False, "Manual launch false now")
    assert_true(report["ready_for_reply_send"] is False, "Reply send false")


def test_phase40j_no_sensitive_values_and_markdown() -> None:
    report = build_phase40j_private_test_readonly_runtime_preflight()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text and "i_approve_" not in text, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Phase 40J" in render_phase40j_private_test_readonly_runtime_preflight_markdown(report), "Markdown")


def main() -> int:
    for test in (test_phase40j_preflight_report_only_and_no_live, test_phase40j_conditions_and_no_reply_readiness, test_phase40j_no_sensitive_values_and_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40J read-only preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
