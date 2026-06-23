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
    _complete_agent_web_bridge_after_ack,
    _maybe_send_agent_web_bridge_ack,
    build_agent_web_reference_timeout_response,
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


def test_timeout_response_is_bounded_and_safe() -> None:
    response = build_agent_web_reference_timeout_response("kasumi")
    content = response["content"]
    assert_true(response["reply_text_source"] == "web_reference_timeout", "timeout source")
    assert_true("웹 참조 작업이 시간 초과되었습니다." in content, "timeout message")
    assert_true("web_reference_timeout" == response["web_reference_failure_reason"], "bounded reason")
    assert_true(response["llm_api_called"] is False, "no LLM")
    assert_true(response["rag_called"] is False, "no RAG")
    assert_true(response["external_execution"] is False, "no external")
    assert_true(response["raw_discord_ids_logged"] is False, "no raw IDs")
    assert_true(response["secret_values_logged"] is False, "no secrets")


def test_agent_web_bridge_timeout_sends_final_fallback() -> None:
    def run() -> None:
        original = company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout

        async def timeout_build(_decision: Any, *, timeout_seconds: int) -> dict[str, Any]:
            raise asyncio.TimeoutError()

        company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = timeout_build
        try:
            message = FakeMessage("!kasumi 이번 달 지원사업 후보 찾아줘")
            ack = asyncio.run(_maybe_send_agent_web_bridge_ack(message, client=None))
            completion = asyncio.run(_complete_agent_web_bridge_after_ack(message, ack, client=None, timeout_seconds=1))
        finally:
            company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = original

        assert_true(ack["ack_sent"] is True, "ACK sent")
        assert_true(completion["agent_web_reference_execution_started"] is True, "execution started")
        assert_true(completion["agent_web_reference_execution_completed"] is False, "execution not completed")
        assert_true(completion["agent_web_reference_execution_failed"] is True, "execution failed")
        assert_true(completion["agent_web_reference_failure_reason"] == "web_reference_timeout", "timeout reason")
        assert_true(completion["agent_web_reference_failure_fallback_sent"] is True, "timeout fallback sent")
        assert_true(completion["agent_web_reference_final_reply_sent"] is True, "final fallback sent")
        assert_true("시간 초과" in message.channel.sent[-1], "timeout sent to Discord")
        assert_true(len(message.channel.sent) == 2, "ACK plus one fallback")

    with_env(WEB_ENV, run)


def main() -> int:
    test_timeout_response_is_bounded_and_safe()
    print("PASS test_timeout_response_is_bounded_and_safe")
    test_agent_web_bridge_timeout_sends_final_fallback()
    print("PASS test_agent_web_bridge_timeout_sends_final_fallback")
    print("All company agent runtime web bridge timeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
