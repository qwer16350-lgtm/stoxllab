from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase46_llm_retry_policy import build_phase46_llm_retry_policy


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase46_retry_policy_blocks_automatic_retry() -> None:
    report = build_phase46_llm_retry_policy()
    assert_true(report["report_type"] == "phase46_llm_retry_policy", "Report type")
    assert_true(report["phase45_actual_llm_call_completed"] is True, "Phase45 complete")
    assert_true(report["phase45_llm_call_count"] == 1, "Exactly one")
    assert_true(report["automatic_retry_allowed"] is False, "No auto retry")
    assert_true(report["repeat_phase45_call_allowed"] is False, "No repeat")
    assert_true(report["retry_requires_new_manual_gate"] is True, "Manual gate")
    assert_true(report["retry_requires_new_approval_phrase"] is True, "Approval phrase")
    assert_true(report["retry_requires_cost_guard"] is True, "Cost guard")
    assert_true(report["retry_requires_call_count_guard"] is True, "Call-count guard")
    assert_true(report["discord_send_remains_disabled"] is True, "Discord disabled")


def test_phase46_retry_policy_no_execution() -> None:
    report = build_phase46_llm_retry_policy()
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_called"] is False, "No LLM call")
    assert_true(report["additional_llm_api_call"] is False, "No additional call")
    assert_true(report["discord_api_send_called"] is False, "No Discord API")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["raw_output_included"] is False, "No raw output")
    assert_true(report["full_content_included"] is False, "No full content")


def test_phase46_retry_policy_no_sensitive_values() -> None:
    text = json.dumps(build_phase46_llm_retry_policy(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase46_retry_policy_blocks_automatic_retry,
        test_phase46_retry_policy_no_execution,
        test_phase46_retry_policy_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase46 LLM retry policy tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
