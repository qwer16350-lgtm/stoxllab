from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_one_shot_llm_draft_call_closeout import build_success_fixture
from one_shot_llm_no_send_final_lock import build_one_shot_llm_no_send_final_lock, render_one_shot_llm_no_send_final_lock_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(mutator, message: str) -> None:
    fixture = build_success_fixture()
    mutator(fixture)
    try:
        build_one_shot_llm_no_send_final_lock(fixture)
    except ValueError:
        return
    raise AssertionError(message)


def test_final_lock_success_fixture() -> None:
    report = build_one_shot_llm_no_send_final_lock()
    assert_true(report["final_lock_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase36d_actual_llm_draft_call_complete"] is True, "36D complete")
    assert_true(report["phase36e_closeout_passed"] is True, "36E passed")
    assert_true(report["phase36f_no_send_final_lock_passed"] is True, "36F passed")
    assert_true(report["ready_for_phase37_entry_gate"] is True, "Ready for 37 gate")


def test_final_lock_counts_and_safety() -> None:
    report = build_one_shot_llm_no_send_final_lock()
    assert_true(report["new_llm_api_call_attempted"] is False, "No new attempt")
    assert_true(report["new_llm_api_called"] is False, "No new call")
    assert_true(report["llm_call_count_locked"] == 1, "LLM count locked")
    assert_true(report["discord_send_count_locked"] == 0, "Discord send count locked")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["message_sent_count"] == 0, "No message")
    assert_true(report["ready_for_discord_send"] is False, "No send ready")
    assert_true(report["public_channel_send_allowed"] is False, "No public send")
    assert_true(report["team_channel_reply_allowed"] is False, "No team reply")
    assert_true(report["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(report["embedding_vector_disabled"] is True, "Embedding disabled")
    assert_true(report["external_execution"] is False, "No external")


def test_final_lock_fails_bad_counts_and_flags() -> None:
    assert_raises(lambda item: item.update({"llm_api_called_count": 0}), "LLM count 0 fails")
    assert_raises(lambda item: item.update({"llm_api_called_count": 2}), "LLM count 2 fails")
    assert_raises(lambda item: item.update({"message_sent_count": 1}), "Message count 1 fails")
    assert_raises(lambda item: item.update({"discord_message_sent": True}), "Discord sent fails")
    assert_raises(lambda item: item.update({"ready_for_discord_send": True}), "Send ready fails")
    assert_raises(lambda item: item.update({"embedding_api_called": True}), "Embedding fails")
    assert_raises(lambda item: item.update({"external_execution": True}), "External fails")


def test_final_lock_no_sensitive_values_and_markdown() -> None:
    report = build_one_shot_llm_no_send_final_lock()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("No-send Final Lock" in render_one_shot_llm_no_send_final_lock_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_final_lock_success_fixture,
        test_final_lock_counts_and_safety,
        test_final_lock_fails_bad_counts_and_flags,
        test_final_lock_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All one-shot LLM no-send final lock tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
