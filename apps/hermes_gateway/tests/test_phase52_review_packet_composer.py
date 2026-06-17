from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase52_review_packet_composer import build_phase52_review_packet_composer


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase52_review_packet_contract() -> None:
    report = build_phase52_review_packet_composer()
    assert_true(report["report_type"] == "phase52_review_packet", "Report type")
    assert_true(report["packet_type"] == "readonly_review_packet", "Packet type")
    assert_true(report["external_action_taken"] is False, "No external")
    assert_true(report["discord_send_allowed"] is False, "No send")
    assert_true(report["llm_call_allowed"] is False, "No LLM")
    assert_true(report["rag_call_allowed"] is False, "No RAG")
    assert_true(report["requires_human_review"] is True, "Human review")
    assert_true(report["recommended_next_action"] == "review_only", "Review only")
    assert_true(report["agent_route_candidate"] == "operations", "Route")
    assert_true(report["evidence_shell_created"] is True, "Evidence shell")
    assert_true(report["raw_content_included"] is False, "No raw content")
    assert_true(report["raw_discord_ids_logged"] is False, "No raw IDs")


def test_phase52_review_packet_no_runtime() -> None:
    report = build_phase52_review_packet_composer()
    for key in ("actual_discord_runtime_executed", "actual_llm_api_call_attempted", "actual_llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        assert_true(report[key] is False, key)


def test_phase52_review_packet_no_sensitive_values() -> None:
    text = json.dumps(build_phase52_review_packet_composer(), ensure_ascii=False).lower()
    assert_true("please review" not in text, "No raw content")
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase52_review_packet_contract, test_phase52_review_packet_no_runtime, test_phase52_review_packet_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase52 review packet composer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
