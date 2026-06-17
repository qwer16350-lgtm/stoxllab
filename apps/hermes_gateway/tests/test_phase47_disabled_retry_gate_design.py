from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase47_disabled_retry_gate_design import build_phase47_disabled_retry_gate_design


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase47_disabled_retry_gate_design_contract() -> None:
    report = build_phase47_disabled_retry_gate_design()
    assert_true(report["report_type"] == "phase47_disabled_retry_gate_design", "Report type")
    assert_true(report["retry_gate_implemented"] is False, "Retry gate not implemented")
    assert_true(report["retry_execution_available"] is False, "Retry unavailable")
    assert_true(report["automatic_retry_allowed"] is False, "No auto retry")
    assert_true(report["manual_retry_requires_new_phase"] is True, "New phase required")
    assert_true(report["manual_retry_requires_new_approval_phrase"] is True, "New approval phrase")
    assert_true(report["repeat_phase45_call_allowed"] is False, "No Phase45 repeat")
    assert_true(report["discord_send_remains_disabled"] is True, "Discord disabled")


def test_phase47_disabled_retry_gate_design_guards() -> None:
    report = build_phase47_disabled_retry_gate_design()
    assert_true(report["manual_retry_requires_new_manual_gate"] is True, "New manual gate")
    assert_true(report["manual_retry_requires_cost_guard"] is True, "Cost guard")
    assert_true(report["manual_retry_requires_call_count_guard"] is True, "Call-count guard")
    assert_true(report["automatic_send_allowed"] is False, "No auto send")
    assert_true(report["raw_output_included"] is False, "No raw output")
    assert_true(report["full_content_included"] is False, "No full output")
    assert_true(report["ready_for_phase48_retry_manual_gate_design"] is False, "Phase48 B not executed")
    assert_true(report["ready_for_phase48_discord_send_review_gate_design"] is False, "Phase48 C not executed")


def test_phase47_disabled_retry_gate_design_no_execution() -> None:
    report = build_phase47_disabled_retry_gate_design()
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_called"] is False, "No LLM call")
    assert_true(report["additional_llm_api_call"] is False, "No extra LLM")
    assert_true(report["discord_api_send_called"] is False, "No Discord API")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")


def test_phase47_disabled_retry_gate_design_no_sensitive_values() -> None:
    text = json.dumps(build_phase47_disabled_retry_gate_design(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase47_disabled_retry_gate_design_contract,
        test_phase47_disabled_retry_gate_design_guards,
        test_phase47_disabled_retry_gate_design_no_execution,
        test_phase47_disabled_retry_gate_design_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase47 disabled retry gate design tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
