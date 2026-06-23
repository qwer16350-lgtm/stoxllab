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
from company_agent_runtime import (
    AgentWebBridgeDecision,
    _complete_agent_web_bridge_after_ack,
    _maybe_send_agent_web_bridge_ack,
)


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


def test_ack_sent_never_returns_agent_web_bridge_not_reached() -> None:
    def run() -> None:
        original = company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout

        async def empty_build(_decision: Any, *, timeout_seconds: int) -> dict[str, Any]:
            return {"reply_prepared": False, "response": {}}

        company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = empty_build
        try:
            message = FakeMessage("!kasumi 지원사업 후보 찾아줘")
            ack = asyncio.run(_maybe_send_agent_web_bridge_ack(message, client=None))
            completion = asyncio.run(_complete_agent_web_bridge_after_ack(message, ack, client=None, timeout_seconds=10))
        finally:
            company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = original

        assert_true(ack["ack_sent"] is True, "ACK sent")
        assert_true(completion["agent_web_reference_failure_reason"] != "agent_web_bridge_not_reached", "not reached forbidden")
        assert_true(completion["agent_web_reference_failure_reason"] == "agent_web_bridge_state_lost_after_ack", "state lost reason")
        assert_true(completion["agent_web_bridge_state_lost_after_ack"] is True, "state lost trace")
        assert_true("agent_web_bridge_not_reached" not in message.channel.sent[-1], "not reached not sent")
        assert_true("agent_web_bridge_state_lost_after_ack" in message.channel.sent[-1], "state lost sent")

    with_env(WEB_ENV, run)


def test_impossible_state_uses_state_lost_reason() -> None:
    def run() -> None:
        message = FakeMessage("!kasumi 지원사업 후보 찾아줘")
        decision = AgentWebBridgeDecision(
            selected=False,
            selected_agent="kasumi",
            agent_scope="research_discovery",
            source_channel="operation-brief",
            original_message=message.content,
            query="지원사업 후보 찾아줘",
            normalized_command="kasumi",
            web_intent_detected=True,
            web_reference_enabled=True,
            web_reference_mode="manual_command_only",
            reason="test_impossible_state",
        )
        ack = {
            **decision.to_trace(),
            "agent_web_bridge_selected": True,
            "agent_web_bridge_decision": decision,
            "ack_sent": True,
        }
        completion = asyncio.run(_complete_agent_web_bridge_after_ack(message, ack, client=None, timeout_seconds=10))
        assert_true(completion["agent_web_reference_failure_reason"] == "agent_web_bridge_state_lost_after_ack", "state lost")
        assert_true(completion["agent_web_bridge_state_lost_after_ack"] is True, "state lost trace")

    with_env(WEB_ENV, run)


def main() -> int:
    test_ack_sent_never_returns_agent_web_bridge_not_reached()
    print("PASS test_ack_sent_never_returns_agent_web_bridge_not_reached")
    test_impossible_state_uses_state_lost_reason()
    print("PASS test_impossible_state_uses_state_lost_reason")
    print("All company agent runtime web bridge no-not-reached tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
