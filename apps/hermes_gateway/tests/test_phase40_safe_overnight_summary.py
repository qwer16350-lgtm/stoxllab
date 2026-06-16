from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_safe_overnight_summary import build_phase40_safe_overnight_summary, render_phase40_safe_overnight_summary_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40i_summary_completes_reports_without_live_execution() -> None:
    report = build_phase40_safe_overnight_summary()
    assert_true(report["phase40_reports_completed"] is True, "Reports complete")
    assert_true(all(report["phase40_report_status"].values()), "All statuses true")
    assert_true(report["actual_discord_send_count_locked_from_phase39"] == 1, "Phase 39 count locked")
    assert_true(report["additional_discord_send_count"] == 0, "No extra send")
    assert_true(report["live_runtime_started"] is False, "No runtime")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_message_sent"] is False, "No message")


def test_phase40i_no_llm_rag_embedding_external_public_team() -> None:
    report = build_phase40_safe_overnight_summary()
    for key in ("llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "public_channel_send_allowed", "team_channel_send_allowed", "public_channel_reply_allowed", "team_channel_reply_allowed", "unattended_auto_reply_allowed"):
        assert_true(report[key] is False, f"{key} false")


def test_phase40i_no_sensitive_values_and_markdown() -> None:
    report = build_phase40_safe_overnight_summary()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text and "i_approve_" not in text, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true(report["safe_to_review_next_morning"] is True, "Safe review")
    assert_true(report["next_human_confirmation_required"] is True, "Next confirmation")
    assert_true("Phase 40I" in render_phase40_safe_overnight_summary_markdown(report), "Markdown")


def main() -> int:
    for test in (test_phase40i_summary_completes_reports_without_live_execution, test_phase40i_no_llm_rag_embedding_external_public_team, test_phase40i_no_sensitive_values_and_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40I safe overnight summary tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
