from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import company_agent_runtime as runtime
from company_discord_outbound_guard import classify_discord_send_failure


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeChannel:
    name = "operation-brief"

    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)


class FakeClient:
    _agent_bot_fleet = object()


async def blocked_real(_fleet, _agent_id: str, _channel_name: str, _content: str) -> dict:
    return {"blocked": True, "blocked_reasons": ["agent_bot_client_missing"], "discord_message_sent": False}


async def blocked_webhook(_agent_id: str, _channel, _content: str, *, create_enabled: bool = True) -> dict:
    return {"blocked": True, "blocked_reasons": ["webhook_send_failed"], "discord_message_sent": False}


def test_failure_reason_mapping_is_bounded() -> None:
    assert_true(classify_discord_send_failure("403 forbidden") == "discord_send_forbidden", "403")
    assert_true(classify_discord_send_failure("429 rate limit") == "discord_send_rate_limited", "429")
    assert_true(classify_discord_send_failure("token missing") == "discord_sender_token_missing", "token")


def test_auto_sender_fallback_uses_guarded_chunks() -> None:
    original_real = runtime.send_as_real_agent_bot
    original_webhook = runtime.send_as_agent_webhook
    old_mode = os.environ.get("HERMES_COMPANY_AGENT_SENDER_MODE")
    old_real = os.environ.get("HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED")
    old_hook = os.environ.get("HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED")
    try:
        runtime.send_as_real_agent_bot = blocked_real
        runtime.send_as_agent_webhook = blocked_webhook
        os.environ["HERMES_COMPANY_AGENT_SENDER_MODE"] = "auto"
        os.environ["HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED"] = "true"
        os.environ["HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED"] = "true"
        channel = FakeChannel()
        result = asyncio.run(runtime._send_agent_content(FakeClient(), "kasumi", channel, "긴 응답\n" * 500))
    finally:
        runtime.send_as_real_agent_bot = original_real
        runtime.send_as_agent_webhook = original_webhook
        if old_mode is None:
            os.environ.pop("HERMES_COMPANY_AGENT_SENDER_MODE", None)
        else:
            os.environ["HERMES_COMPANY_AGENT_SENDER_MODE"] = old_mode
        if old_real is None:
            os.environ.pop("HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED", None)
        else:
            os.environ["HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED"] = old_real
        if old_hook is None:
            os.environ.pop("HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED", None)
        else:
            os.environ["HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED"] = old_hook
    assert_true(result["send_strategy"] == "bot_fallback", "bot fallback")
    assert_true(result["sender_attempt_order"] == ["real_bot", "webhook", "bot_fallback"], "attempt order")
    assert_true(result["outbound_guard_applied"] is True, "guard")
    assert_true(result["outbound_chunking_used"] is True, "chunked")
    assert_true(len(channel.sent) == result["message_sent_count"], "sent count")
    assert_true(all(len(item) <= 1900 for item in channel.sent), "safe chunks")
    assert_true(result["raw_discord_ids_logged"] is False, "no raw IDs")
    assert_true(result["secret_values_logged"] is False, "no secrets")


def main() -> int:
    test_failure_reason_mapping_is_bounded()
    print("PASS test_failure_reason_mapping_is_bounded")
    test_auto_sender_fallback_uses_guarded_chunks()
    print("PASS test_auto_sender_fallback_uses_guarded_chunks")
    print("All company agent sender failure visibility tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
