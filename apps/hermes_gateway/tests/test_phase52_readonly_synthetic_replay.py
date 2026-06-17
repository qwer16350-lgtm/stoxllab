from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase52_readonly_synthetic_replay import run_phase52_readonly_synthetic_replay


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase52_synthetic_replay_contract() -> None:
    report = run_phase52_readonly_synthetic_replay()
    assert_true(report["report_type"] == "phase52_readonly_synthetic_replay", "Report type")
    assert_true(report["event_count"] == 7, "Event count")
    assert_true(report["all_events_normalized"] is True, "Normalized")
    assert_true(report["all_events_guarded"] is True, "Guarded")
    assert_true(report["all_events_packetized"] is True, "Packetized")
    assert_true(any(item["message_kind"] == "operator_command" for item in report["results"]), "Command fixture")
    assert_true(any(item["message_kind"] == "duplicate" for item in report["results"]), "Duplicate fixture")


def test_phase52_synthetic_replay_no_external_actions() -> None:
    report = run_phase52_readonly_synthetic_replay()
    for key in ("actual_discord_runtime_executed", "discord_api_send_called", "discord_message_sent", "actual_llm_api_call_attempted", "actual_llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        assert_true(report[key] is False, key)
    for result in report["results"]:
        assert_true(result["discord_send_allowed"] is False, "No send")
        assert_true(result["llm_call_allowed"] is False, "No LLM")
        assert_true(result["rag_call_allowed"] is False, "No RAG")
        assert_true(result["external_execution"] is False, "No external")
        assert_true(result["raw_content_included"] is False, "No raw")


def test_phase52_synthetic_replay_no_sensitive_values() -> None:
    text = json.dumps(run_phase52_readonly_synthetic_replay(), ensure_ascii=False).lower()
    assert_true("please review" not in text, "No raw content")
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase52_synthetic_replay_contract, test_phase52_synthetic_replay_no_external_actions, test_phase52_synthetic_replay_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase52 read-only synthetic replay tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
