from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase52_session_context_store import build_phase52_session_context_store


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase52_session_context_contract() -> None:
    report = build_phase52_session_context_store()
    assert_true(report["report_type"] == "phase52_session_context_store", "Report type")
    assert_true(report["session_id_created"] is True, "Session id")
    assert_true(report["session_scope"] == "private_test", "Session scope")
    assert_true(report["message_count"] == 7, "Synthetic message count")
    assert_true(report["duplicate_count"] == 1, "Duplicate count")
    assert_true(report["operator_command_count"] == 1, "Command count")
    assert_true(report["reply_count"] == 0, "No reply")
    assert_true(report["send_count"] == 0, "No send")
    assert_true(report["llm_call_count"] == 0, "No LLM")
    assert_true(report["rag_call_count"] == 0, "No RAG")
    assert_true(report["external_execution_count"] == 0, "No external")


def test_phase52_session_context_no_runtime() -> None:
    report = build_phase52_session_context_store()
    assert_true(report["actual_discord_runtime_executed"] is False, "No Discord runtime")
    assert_true(report["synthetic_fixture_only"] is True, "Synthetic only")
    assert_true(report["raw_content_logged"] is False, "No raw")
    assert_true(report["raw_discord_ids_logged"] is False, "No raw IDs")


def test_phase52_session_context_no_sensitive_values() -> None:
    text = json.dumps(build_phase52_session_context_store(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase52_session_context_contract, test_phase52_session_context_no_runtime, test_phase52_session_context_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase52 session context store tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
