from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import _maybe_send_agent_web_bridge_ack, build_agent_web_bridge_ack_text


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

    async def send(self, content: str) -> dict[str, Any]:
        self.sent.append(content)
        return {"ok": True}


class FakeAuthor:
    bot = False


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content
        self.channel = FakeChannel()
        self.author = FakeAuthor()


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


def test_agent_web_bridge_ack_sent_once_with_outbound_guard() -> None:
    def run() -> None:
        message = FakeMessage("!kasumi 이번 달 지원사업 후보 찾아줘")
        result = asyncio.run(_maybe_send_agent_web_bridge_ack(message, client=None))
        assert_true(result["agent_web_bridge_selected"] is True, "bridge selected")
        assert_true(result["ack_attempted"] is True, "ack attempted")
        assert_true(result["ack_sent"] is True, "ack sent")
        assert_true(result["outbound_guard_applied"] is True, "guard applied")
        assert_true(len(message.channel.sent) == 1, "sent once")
        assert_true("[KASUMI_STOXL]" in message.channel.sent[0], "Kasumi label")
        assert_true("웹 참조 작업을 시작했습니다." in message.channel.sent[0], "start ack")
        assert_true("공식 출처 우선" in message.channel.sent[0], "official source ack")
        assert_true(len(message.channel.sent[0]) < 1900, "bounded ack")

    with_env(WEB_ENV, run)


def test_agent_web_bridge_ack_not_sent_when_no_web_intent() -> None:
    def run() -> None:
        message = FakeMessage("!kasumi ping")
        result = asyncio.run(_maybe_send_agent_web_bridge_ack(message, client=None))
        assert_true(result["agent_web_bridge_selected"] is False, "bridge not selected")
        assert_true(result["ack_attempted"] is False, "ack not attempted")
        assert_true(result["ack_sent"] is False, "ack not sent")
        assert_true(len(message.channel.sent) == 0, "nothing sent")

    with_env(WEB_ENV, run)


def test_ack_text_format_is_stable() -> None:
    text = build_agent_web_bridge_ack_text("kasumi")
    assert_true(text.startswith("[KASUMI_STOXL]\n"), "label first")
    assert_true("웹 참조 작업을 시작했습니다." in text, "ack text")
    assert_true("공식 출처 우선으로 후보를 확인 중입니다." in text, "official text")


def main() -> int:
    test_agent_web_bridge_ack_sent_once_with_outbound_guard()
    print("PASS test_agent_web_bridge_ack_sent_once_with_outbound_guard")
    test_agent_web_bridge_ack_not_sent_when_no_web_intent()
    print("PASS test_agent_web_bridge_ack_not_sent_when_no_web_intent")
    test_ack_text_format_is_stable()
    print("PASS test_ack_text_format_is_stable")
    print("All company agent runtime web bridge ack tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
