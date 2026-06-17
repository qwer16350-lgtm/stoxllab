from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase51_52_readonly_live_runtime_launch_packet import build_phase51_52_readonly_live_runtime_launch_packet
from phase51_52_readonly_live_runtime_preflight import APPROVAL_PHRASE
from test_phase51_52_readonly_live_runtime_preflight import ready_env


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase51_52_launch_packet_closed_state() -> None:
    report = build_phase51_52_readonly_live_runtime_launch_packet(env={})
    assert_true(report["report_type"] == "phase51_52_readonly_live_runtime_launch_packet", "Report type")
    assert_true(report["actual_runtime_command_available"] is True, "Command available")
    assert_true("--run-discord-private-test-readonly" in report["recommended_command"], "Runtime command")
    assert_true(report["send_disabled_required"] is True, "Send disabled")
    assert_true(report["llm_disabled_required"] is True, "LLM disabled")
    assert_true(report["rag_disabled_required"] is True, "RAG disabled")
    assert_true(report["external_execution_disabled_required"] is True, "External disabled")
    assert_true(report["ready_for_manual_gate"] is False, "Gate closed")
    assert_true(report["actual_discord_runtime_executed"] is False, "No runtime")


def test_phase51_52_launch_packet_open_state() -> None:
    report = build_phase51_52_readonly_live_runtime_launch_packet(env=ready_env())
    assert_true(report["ready_for_manual_gate"] is True, "Gate ready")
    assert_true(report["actual_discord_runtime_executed"] is False, "No runtime")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["actual_llm_api_called"] is False, "No LLM")
    assert_true(report["rag_called"] is False, "No RAG")


def test_phase51_52_launch_packet_no_sensitive_values() -> None:
    text = json.dumps(build_phase51_52_readonly_live_runtime_launch_packet(env=ready_env()), ensure_ascii=False)
    assert_true(APPROVAL_PHRASE not in text, "Approval phrase value hidden")
    lowered = text.lower()
    assert_true("sk-" not in lowered and "bearer " not in lowered and "token=" not in lowered, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_phase51_52_launch_packet_closed_state,
        test_phase51_52_launch_packet_open_state,
        test_phase51_52_launch_packet_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase51/52 read-only live runtime launch packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
