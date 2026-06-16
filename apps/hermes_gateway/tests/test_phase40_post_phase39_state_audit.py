from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_post_phase39_state_audit import build_phase40_post_phase39_state_audit, render_phase40_post_phase39_state_audit_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40a_locks_phase39_count_and_blocks_live() -> None:
    report = build_phase40_post_phase39_state_audit()
    assert_true(report["actual_discord_send_count_locked"] == 1, "Phase 39 count remains 1")
    assert_true(report["additional_message_sent_count"] == 0, "No Phase 40 send")
    assert_true(report["live_runtime_started"] is False, "No live runtime")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["ready_for_live_runtime_execution"] is False, "Not live ready")


def test_phase40a_no_llm_rag_external_or_public_team() -> None:
    report = build_phase40_post_phase39_state_audit()
    for key in ("llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution", "public_channel_send_allowed", "team_channel_send_allowed", "public_channel_reply_allowed", "team_channel_reply_allowed"):
        assert_true(report[key] is False, f"{key} false")


def test_phase40a_no_sensitive_values_and_markdown() -> None:
    report = build_phase40_post_phase39_state_audit()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text and "i_approve_" not in text, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Phase 40A" in render_phase40_post_phase39_state_audit_markdown(report), "Markdown")


def main() -> int:
    for test in (test_phase40a_locks_phase39_count_and_blocks_live, test_phase40a_no_llm_rag_external_or_public_team, test_phase40a_no_sensitive_values_and_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40A post-Phase39 state audit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
