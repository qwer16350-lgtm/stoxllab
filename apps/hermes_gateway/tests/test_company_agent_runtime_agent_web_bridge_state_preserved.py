from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import company_agent_runtime
from company_agent_runtime import _complete_agent_web_bridge_after_ack, _maybe_send_agent_web_bridge_ack


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
    "HERMES_COMPANY_AGENT_SENDER_MODE": "bot_fallback",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeChannel:
    name = "operation-brief"

    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content
        self.channel = FakeChannel()
        self.author = type("Author", (), {"bot": False})()


def with_env(values: dict[str, str], func) -> None:
    previous = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            os.environ[key] = value
        func()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_ack_decision_is_preserved_into_completion() -> None:
    def run() -> None:
        captured: dict[str, Any] = {}
        original = company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout

        async def fake_build(decision: Any, *, timeout_seconds: int) -> dict[str, Any]:
            captured["selected_agent"] = decision.selected_agent
            captured["agent_scope"] = decision.agent_scope
            captured["query"] = decision.query
            return company_agent_runtime.build_agent_web_reference_failure_result_from_decision(
                decision,
                "web_reference_provider_exception",
            )

        company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = fake_build
        try:
            message = FakeMessage("!kasumi 이번 달 한국 중소기업 디자인 개발 지원사업 후보 찾아줘")
            ack = asyncio.run(_maybe_send_agent_web_bridge_ack(message, client=None))
            completion = asyncio.run(_complete_agent_web_bridge_after_ack(message, ack, client=None, timeout_seconds=10))
        finally:
            company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = original

        assert_true(ack["agent_web_bridge_selected"] is True, "bridge selected")
        assert_true(ack["ack_sent"] is True, "ACK sent")
        assert_true(completion["agent_web_bridge_decision_preserved_after_ack"] is True, "decision preserved")
        assert_true(captured["selected_agent"] == "kasumi", "selected agent preserved")
        assert_true(captured["agent_scope"] == "research_discovery", "scope preserved")
        assert_true(captured["query"].startswith("이번 달 한국"), "query prefix removed")
        assert_true("!kasumi" not in captured["query"], "command prefix removed")
        assert_true(completion["agent_web_bridge_state_lost_after_ack"] is False, "state not lost")
        assert_true(completion["agent_web_reference_failure_reason"] != "agent_web_bridge_not_reached", "not reached not used")

    with_env(WEB_ENV, run)


def main() -> int:
    test_ack_decision_is_preserved_into_completion()
    print("PASS test_ack_decision_is_preserved_into_completion")
    print("All company agent runtime web bridge state preservation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
