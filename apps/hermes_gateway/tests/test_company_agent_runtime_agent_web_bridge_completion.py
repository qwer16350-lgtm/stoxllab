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
    build_agent_web_bridge_execution_result_from_decision,
)


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
    "HERMES_COMPANY_AGENT_SENDER_MODE": "bot_fallback",
    "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
    "HERMES_COMPANY_AGENT_LLM_MODE": "off",
    "HERMES_COMPANY_AGENT_REPLY_MODE": "deterministic_fallback",
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


def mock_search(agent_id: str, _queries: list[str], _limit: int) -> dict:
    return {
        "search_succeeded": True,
        "failure_reason": "",
        "provider": "mock",
        "results": [
            {
                "title": f"{agent_id} 중소기업 디자인개발 지원사업",
                "url": "https://www.bizinfo.go.kr/web/reference",
                "snippet": "신청기간 2026.06.01 ~ 2026.06.30 지원대상 중소기업 지원내용 디자인개발",
                "institution": "Mock Official",
            }
        ],
    }


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


def test_agent_web_bridge_completion_sends_final_compact_summary() -> None:
    def run() -> None:
        original = company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout

        async def fake_build(decision: Any, *, timeout_seconds: int) -> dict[str, Any]:
            return build_agent_web_bridge_execution_result_from_decision(decision, env=WEB_ENV, web_search_runner=mock_search)

        company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = fake_build
        try:
            message = FakeMessage("!kasumi 이번 달 한국 중소기업 디자인 개발 지원사업 후보 찾아줘")
            ack = asyncio.run(_maybe_send_agent_web_bridge_ack(message, client=None))
            completion = asyncio.run(_complete_agent_web_bridge_after_ack(message, ack, client=None, timeout_seconds=10))
        finally:
            company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = original

        assert_true(ack["ack_sent"] is True, "ACK sent")
        assert_true(completion["agent_web_reference_execution_started"] is True, "execution started")
        assert_true(completion["agent_web_reference_execution_completed"] is True, "execution completed")
        assert_true(completion["agent_web_reference_final_reply_prepared"] is True, "final prepared")
        assert_true(completion["agent_web_reference_final_reply_sent"] is True, "final sent")
        assert_true(completion["message_sent_count"] >= 1, "final message count")
        assert_true(len(message.channel.sent) >= 2, "ACK plus final")
        assert_true("지원사업 후보 검색 완료" in message.channel.sent[-1], "compact summary sent")
        assert_true("memory/context" in message.channel.sent[-1], "memory notice")
        assert_true("SUPPORT_PROGRAM_VERIFICATION" not in message.channel.sent[-1], "full verification not dumped")
        assert_true(completion["raw_discord_ids_logged"] is False, "no raw IDs")
        assert_true(completion["secret_values_logged"] is False, "no secrets")

    with_env(WEB_ENV, run)


def test_kasumi_ping_completion_path_not_selected() -> None:
    def run() -> None:
        message = FakeMessage("!kasumi ping")
        ack = asyncio.run(_maybe_send_agent_web_bridge_ack(message, client=None))
        completion = asyncio.run(_complete_agent_web_bridge_after_ack(message, ack, client=None, timeout_seconds=10))
        assert_true(ack["ack_attempted"] is False, "ACK not attempted")
        assert_true(completion["agent_web_reference_execution_started"] is False, "execution not started")
        assert_true(completion["agent_web_reference_final_reply_sent"] is False, "final not sent")
        assert_true(len(message.channel.sent) == 0, "nothing sent by bridge")

    with_env(WEB_ENV, run)


def main() -> int:
    test_agent_web_bridge_completion_sends_final_compact_summary()
    print("PASS test_agent_web_bridge_completion_sends_final_compact_summary")
    test_kasumi_ping_completion_path_not_selected()
    print("PASS test_kasumi_ping_completion_path_not_selected")
    print("All company agent runtime web bridge completion tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
