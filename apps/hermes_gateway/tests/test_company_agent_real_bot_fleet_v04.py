from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_bot_fleet import (
    AGENT_BOT_TOKEN_ENV,
    AgentBotFleet,
    build_agent_bot_specs,
    build_company_agent_real_bot_fleet_report,
    build_company_agent_real_bot_send_dry_run,
    load_agent_bot_token_presence,
    resolve_agent_bot_name,
    sender_order_for_mode,
)
from company_agent_runtime import _send_agent_content, build_company_agent_approval_dry_run, build_company_agent_handoff_dry_run, should_ignore_message


class FakeAuthor:
    def __init__(self, *, bot: bool = False, author_id: int = 1) -> None:
        self.bot = bot
        self.id = author_id


class FakeMessage:
    def __init__(self, *, bot: bool = False, author_id: int = 1) -> None:
        self.content = "!marin test"
        self.author = FakeAuthor(bot=bot, author_id=author_id)
        self.channel = FakeChannel("marketing-brief")


class FakeWebhook:
    def __init__(self, name: str) -> None:
        self.name = name
        self.id = "123456789012345678"
        self.url = "https://example.invalid/hook"
        self.sent = []

    async def send(self, content: str, *, username: str | None = None) -> None:
        self.sent.append({"content": content, "username": username})


class FakeChannel:
    def __init__(self, name: str, *, fail_webhook_create: bool = False) -> None:
        self.name = name
        self.id = "123456789012345678"
        self.fail_webhook_create = fail_webhook_create
        self.sent = []
        self.hooks: list[FakeWebhook] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)

    async def webhooks(self) -> list[FakeWebhook]:
        return list(self.hooks)

    async def create_webhook(self, *, name: str) -> FakeWebhook:
        if self.fail_webhook_create:
            raise RuntimeError("webhook create failed")
        hook = FakeWebhook(name)
        self.hooks.append(hook)
        return hook


class FakeClient:
    def __init__(self, channels: list[FakeChannel] | None = None, fleet: AgentBotFleet | None = None) -> None:
        self.channels = channels or []
        self._agent_bot_fleet = fleet

    def get_all_channels(self) -> list[FakeChannel]:
        return self.channels


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_safe(report: dict) -> None:
    text = json.dumps(report, ensure_ascii=False)
    assert_true("token-secret" not in text, "token value hidden")
    assert_true("123456789012345678" not in text, "raw Discord ID hidden")
    assert_true("https://" not in text and "http://" not in text, "webhook URL hidden")
    assert_true(report.get("raw_discord_ids_logged") is False, "raw IDs flag")
    assert_true(report.get("secret_values_logged") is False, "secret flag")


def test_report_mapping_and_defaults() -> None:
    report = build_company_agent_real_bot_fleet_report({})
    assert_true(report["real_bot_fleet_available"] is True, "fleet available")
    assert_true(report["default_real_bots_enabled"] is False, "default disabled")
    assert_true(report["default_sender_mode"] == "bot_fallback", "default sender")
    assert_true(report["supported_sender_modes"] == ["bot_fallback", "webhook", "real_bot", "auto"], "modes")
    assert_true(report["agent_bot_names"]["marin"] == "MARIN_STOXL", "marin")
    assert_true(report["agent_bot_names"]["lucy"] == "LUCY_STOXL", "lucy")
    assert_true(report["agent_bot_clients_send_only"] is True, "send only")
    assert_true(report["agent_bot_on_message_responds"] is False, "no on_message response")
    assert_safe(report)


def test_token_env_mapping_and_presence_boolean_only() -> None:
    env = {key: "token-secret" for key in AGENT_BOT_TOKEN_ENV.values()}
    presence = load_agent_bot_token_presence(env)
    assert_true(all(presence.values()), "all tokens present")
    specs = build_agent_bot_specs(env)
    assert_true(specs[0].token_value_logged is False, "token value not logged")
    assert_true({spec.agent_id: spec.token_env for spec in specs}["marin"] == "HERMES_DISCORD_MARIN_BOT_TOKEN", "marin env")
    report = build_company_agent_real_bot_fleet_report(env)
    assert_true(report["agent_bot_token_presence"]["marin"] is True, "presence boolean")
    assert_true(report["agent_bot_token_values_logged"] is False, "token values flag")
    assert_safe(report)


def test_dry_run_no_login_send_or_webhook_create() -> None:
    dry = build_company_agent_real_bot_send_dry_run("marin", "marketing-brief", "MML 인스타 문구")
    assert_true(dry["selected_agent"] == "marin", "dry marin")
    assert_true(dry["agent_bot_name"] == "MARIN_STOXL", "dry name")
    assert_true(dry["would_use_real_bot"] is True, "would use real bot")
    assert_true(dry["agent_bot_login_attempted"] is False, "no login")
    assert_true(dry["discord_api_send_called"] is False, "no send")
    assert_true(dry["webhook_created"] is False, "no webhook create")
    assert_true(dry["external_execution_performed"] is False, "external false")
    assert_safe(dry)


def test_sender_order() -> None:
    assert_true(sender_order_for_mode("bot_fallback", real_bots_enabled=True, webhook_enabled=True) == ["bot_fallback"], "bot order")
    assert_true(sender_order_for_mode("webhook", real_bots_enabled=True, webhook_enabled=True) == ["webhook", "bot_fallback"], "webhook order")
    assert_true(sender_order_for_mode("real_bot", real_bots_enabled=True, webhook_enabled=True) == ["real_bot", "webhook", "bot_fallback"], "real order")
    assert_true(sender_order_for_mode("auto", real_bots_enabled=True, webhook_enabled=True) == ["real_bot", "webhook", "bot_fallback"], "auto order")


def test_sender_fallback_paths() -> None:
    async def run() -> None:
        old_env = dict(os.environ)
        try:
            channel = FakeChannel("marketing-brief")
            client = FakeClient([channel])
            os.environ["HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED"] = "true"
            os.environ["HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED"] = "true"
            os.environ["HERMES_COMPANY_AGENT_SENDER_MODE"] = "auto"
            result = await _send_agent_content(client, "marin", channel, "hello")
            assert_true(result["sender_attempt_order"] == ["real_bot", "webhook"], "real fallback to webhook")
            assert_true(result["send_strategy"] == "webhook", "webhook used")
            failing_channel = FakeChannel("marketing-brief", fail_webhook_create=True)
            os.environ["HERMES_COMPANY_AGENT_SENDER_MODE"] = "webhook"
            result2 = await _send_agent_content(FakeClient([failing_channel]), "marin", failing_channel, "hello")
            assert_true(result2["sender_attempt_order"] == ["webhook", "bot_fallback"], "webhook fallback to bot")
            assert_true(result2["send_strategy"] == "bot_fallback", "bot fallback used")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    asyncio.run(run())


def test_hermes_bot_and_agent_bot_loop_guard() -> None:
    ignored_bot = should_ignore_message(FakeMessage(bot=True))
    assert_true(ignored_bot == (True, "bot_message"), "bot ignored")
    ignored_agent = should_ignore_message(FakeMessage(author_id=77), agent_bot_user_ids={77})
    assert_true(ignored_agent == (True, "agent_bot_message"), "agent bot ignored")


def test_handoff_and_approval_real_bot_names() -> None:
    handoff = build_company_agent_handoff_dry_run("marketing-brief", "!marin MML 인스타 문구")
    approval = build_company_agent_approval_dry_run("lucy-검토", "!approve-draft 이 문구 검토해줘")
    assert_true(handoff["agent_bot_name"] == "MARIN_STOXL", "handoff real bot")
    assert_true(approval["agent_bot_name"] == "LUCY_STOXL", "approval real bot")
    assert_true(approval["external_execution_performed"] is False, "external false")
    assert_safe(handoff)
    assert_safe(approval)


def main() -> int:
    tests = [
        test_report_mapping_and_defaults,
        test_token_env_mapping_and_presence_boolean_only,
        test_dry_run_no_login_send_or_webhook_create,
        test_sender_order,
        test_sender_fallback_paths,
        test_hermes_bot_and_agent_bot_loop_guard,
        test_handoff_and_approval_real_bot_names,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All company agent real bot fleet v0.4 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
