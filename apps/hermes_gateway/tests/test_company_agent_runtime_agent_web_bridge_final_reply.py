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
    build_company_agent_message_result,
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


class FlakyChannel:
    name = "operation-brief"

    def __init__(self) -> None:
        self.sent: list[str] = []
        self.calls = 0

    async def send(self, content: str) -> None:
        self.calls += 1
        if self.calls == 2:
            raise RuntimeError("discord send failed with hidden detail")
        self.sent.append(content)


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content
        self.channel = FlakyChannel()
        self.author = type("Author", (), {"bot": False})()


def mock_search(agent_id: str, _queries: list[str], _limit: int) -> dict:
    return {
        "search_succeeded": True,
        "failure_reason": "",
        "provider": "mock",
        "results": [
            {
                "title": f"{agent_id} 지원사업 후보",
                "url": "https://www.bizinfo.go.kr/web/reference",
                "snippet": "신청기간 2026.06.01 ~ 2026.06.30 공식 mock",
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


def test_final_reply_send_failure_attempts_short_notice() -> None:
    def run() -> None:
        original = company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout

        async def fake_build(decision: Any, *, timeout_seconds: int) -> dict[str, Any]:
            return build_agent_web_bridge_execution_result_from_decision(decision, env=WEB_ENV, web_search_runner=mock_search)

        company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = fake_build
        try:
            message = FakeMessage("!kasumi 지원사업 후보 찾아줘")
            ack = asyncio.run(_maybe_send_agent_web_bridge_ack(message, client=None))
            completion = asyncio.run(_complete_agent_web_bridge_after_ack(message, ack, client=None, timeout_seconds=10))
        finally:
            company_agent_runtime._build_agent_web_bridge_execution_result_with_timeout = original

        assert_true(ack["ack_sent"] is True, "ACK sent")
        assert_true(completion["agent_web_reference_final_reply_prepared"] is True, "final prepared")
        assert_true(completion["agent_web_reference_final_reply_sent"] is False, "final failed")
        assert_true(completion["fallback_short_notice_attempted"] is True, "short notice attempted")
        assert_true(completion["fallback_short_notice_sent"] is True, "short notice sent")
        assert_true("Discord 전송 중 일부 실패" in message.channel.sent[-1], "short notice content")
        assert_true("hidden detail" not in message.channel.sent[-1], "raw error hidden")

    with_env(WEB_ENV, run)


def test_web_command_and_agent_bridge_share_web_reference_pipeline() -> None:
    web = build_company_agent_message_result(
        "operation-brief",
        "!web 지원사업 후보 찾아줘",
        env=WEB_ENV,
        web_search_runner=mock_search,
    )
    bridge = build_company_agent_message_result(
        "operation-brief",
        "!kasumi 지원사업 후보 찾아줘",
        env=WEB_ENV,
        web_search_runner=mock_search,
    )
    assert_true(web["web_reference_bridge_attempted"] is True, "web attempted")
    assert_true(bridge["web_reference_bridge_attempted"] is True, "bridge attempted")
    assert_true(web["web_reference_succeeded"] is True, "web succeeded")
    assert_true(bridge["web_reference_succeeded"] is True, "bridge succeeded")
    assert_true(web["response"]["reply_text_source"] == "web_reference", "web response source")
    assert_true(bridge["response"]["reply_text_source"] == "web_reference", "bridge response source")
    assert_true(bridge["selected_agent"] == "kasumi", "Kasumi preserved")
    assert_true(bridge["agent_scope"] == "research_discovery", "Kasumi scope")
    assert_true(bridge["response"]["llm_api_called"] is False, "no LLM")
    assert_true(bridge["response"]["rag_called"] is False, "no RAG")
    assert_true(bridge["response"]["external_execution"] is False, "no external")


def main() -> int:
    test_final_reply_send_failure_attempts_short_notice()
    print("PASS test_final_reply_send_failure_attempts_short_notice")
    test_web_command_and_agent_bridge_share_web_reference_pipeline()
    print("PASS test_web_command_and_agent_bridge_share_web_reference_pipeline")
    print("All company agent runtime web bridge final reply tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
