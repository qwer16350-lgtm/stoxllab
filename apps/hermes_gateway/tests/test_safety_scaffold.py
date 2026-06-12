"""Phase 23-28 consolidated safety scaffold tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_safety_scaffold.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import cli
from agent_response_interface import build_agent_response_interface_report
from approval_interaction_spec import build_approval_interaction_spec
from live_capture_stub import build_live_capture_stub_report
from readonly_runtime_stub import build_readonly_runtime_stub_report
from reply_planner import build_reply_plan, build_reply_planner_report


ROOT = APP_DIR.parents[1]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_readonly_runtime_stub_safe() -> None:
    report = build_readonly_runtime_stub_report(ROOT)
    assert_true(report["can_connect_gateway"] is False, "Runtime stub must not connect Gateway")
    assert_true(report["can_send_messages"] is False, "Runtime stub must not send messages")
    assert_true(report["token_loaded"] is False, "Runtime stub must not load token")


def test_live_capture_stub_safe() -> None:
    report = build_live_capture_stub_report(ROOT)
    assert_true(report["live_event_received"] is False, "Live capture must not receive live events")
    assert_true(report["message_sent"] is False, "Live capture must not send messages")
    assert_true(report["external_execution_count"] == 0, "Live capture must not execute external actions")


def test_reply_planner_default_disabled() -> None:
    plan = build_reply_plan({"blocked": False})
    assert_true(plan["reply_enabled"] is False, "Reply planner must be disabled")
    assert_true(plan["will_send"] is False, "Reply planner must not send")


def test_approval_interaction_runtime_disabled() -> None:
    spec = build_approval_interaction_spec()
    assert_true(spec["enabled_in_runtime"] is False, "Approval interaction must be disabled at runtime")


def test_approval_after_effect_external_execution_false() -> None:
    spec = build_approval_interaction_spec()
    assert_true(spec["approval_after_effect"]["external_execution_allowed"] is False, "Approval must not allow external execution")


def test_agent_response_llm_disabled() -> None:
    report = build_agent_response_interface_report(ROOT)
    assert_true(report["llm_enabled"] is False, "LLM must be disabled")


def test_agent_response_rag_disabled() -> None:
    report = build_agent_response_interface_report(ROOT)
    assert_true(report["rag_enabled"] is False, "RAG must be disabled")


def test_scaffold_aggregate_has_all_phases() -> None:
    report = cli.build_safety_scaffold_report(ROOT)
    assert_true(len(report["reports"]) == 6, "Aggregate scaffold should include phases 23-28")
    for key in (
        "phase23_connection_preflight",
        "phase24_readonly_runtime_stub",
        "phase25_live_capture_stub",
        "phase26_reply_planner",
        "phase27_approval_interaction_spec",
        "phase28_agent_response_interface",
    ):
        assert_true(key in report["reports"], f"Missing aggregate report: {key}")


def test_no_discord_api_called() -> None:
    assert_true(cli.build_safety_scaffold_report(ROOT)["safety_assertions"]["discord_api_called"] is False, "Discord API must not be called")


def test_no_gateway_connected() -> None:
    assert_true(cli.build_safety_scaffold_report(ROOT)["safety_assertions"]["gateway_connected"] is False, "Gateway must not connect")


def test_no_message_sent() -> None:
    assert_true(cli.build_safety_scaffold_report(ROOT)["safety_assertions"]["message_sent"] is False, "Message must not be sent")


def test_no_llm_called() -> None:
    assert_true(cli.build_safety_scaffold_report(ROOT)["safety_assertions"]["llm_called"] is False, "LLM must not be called")


def test_no_rag_called() -> None:
    assert_true(cli.build_safety_scaffold_report(ROOT)["safety_assertions"]["rag_called"] is False, "RAG must not be called")


def test_no_external_execution() -> None:
    assert_true(cli.build_safety_scaffold_report(ROOT)["safety_assertions"]["external_execution_enabled"] is False, "External execution must not be enabled")


def test_human_only_preserved() -> None:
    assert_true(cli.build_safety_scaffold_report(ROOT)["safety_assertions"]["human_only_execution_preserved"] is True, "Human-only execution must be preserved")


def test_example_reports_are_safe() -> None:
    for path in [
        "readonly_runtime_stub_report.example.json",
        "live_capture_stub_report.example.json",
        "reply_planner_report.example.json",
        "approval_interaction_spec.example.json",
        "agent_response_interface.example.json",
    ]:
        data = json.loads((ROOT / "apps" / "hermes_gateway" / "examples" / path).read_text(encoding="utf-8-sig"))
        text = json.dumps(data, ensure_ascii=False).lower()
        assert_true("xoxb-" not in text and "sk-" not in text and "mfa." not in text, f"Secret-like marker in {path}")


def main() -> int:
    tests = [
        test_readonly_runtime_stub_safe,
        test_live_capture_stub_safe,
        test_reply_planner_default_disabled,
        test_approval_interaction_runtime_disabled,
        test_approval_after_effect_external_execution_false,
        test_agent_response_llm_disabled,
        test_agent_response_rag_disabled,
        test_scaffold_aggregate_has_all_phases,
        test_no_discord_api_called,
        test_no_gateway_connected,
        test_no_message_sent,
        test_no_llm_called,
        test_no_rag_called,
        test_no_external_execution,
        test_human_only_preserved,
        test_example_reports_are_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All safety scaffold tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
