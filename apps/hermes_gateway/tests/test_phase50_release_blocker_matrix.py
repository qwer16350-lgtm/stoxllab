from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase50_release_blocker_matrix import MISSING_BEFORE_PRODUCTION, build_phase50_release_blocker_matrix


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase50_release_blocker_contract() -> None:
    report = build_phase50_release_blocker_matrix()
    assert_true(report["report_type"] == "phase50_release_blocker_matrix", "Report type")
    assert_true(report["unattended_auto_reply_blocked"] is True, "Unattended")
    assert_true(report["automatic_retry_blocked"] is True, "Retry")
    assert_true(report["automatic_discord_send_blocked"] is True, "Discord")
    assert_true(report["llm_repeat_call_blocked"] is True, "LLM repeat")
    assert_true(report["raw_output_dump_blocked"] is True, "Raw")
    assert_true(report["scheduler_live_execution_blocked"] is True, "Scheduler")
    assert_true(report["production_unattended_ready"] is False, "Production false")
    assert_true(report["missing_before_production"] == MISSING_BEFORE_PRODUCTION, "Missing list")


def test_phase50_release_blocker_no_execution() -> None:
    report = build_phase50_release_blocker_matrix()
    for key in ("llm_api_call_attempted", "llm_api_called", "discord_api_send_called", "discord_message_sent", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        assert_true(report[key] is False, key)


def test_phase50_release_blocker_no_sensitive_values() -> None:
    text = json.dumps(build_phase50_release_blocker_matrix(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase50_release_blocker_contract, test_phase50_release_blocker_no_execution, test_phase50_release_blocker_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase50 release blocker matrix tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
