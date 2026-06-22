from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_approval_dry_run, build_company_agent_handoff_dry_run
from company_webhook_sender import (
    agent_webhook_names,
    build_company_agent_webhook_persona_dry_run,
    build_company_agent_webhook_persona_report,
    get_or_create_agent_webhook,
    resolve_agent_webhook_name,
    send_as_agent_webhook,
)


class FakeWebhook:
    def __init__(self, name: str) -> None:
        self.name = name
        self.sent = []
        self.id = "123456789012345678"
        self.url = "https://example.invalid/webhook"

    async def send(self, content: str, *, username: str | None = None) -> None:
        self.sent.append({"content": content, "username": username})


class FakeChannel:
    def __init__(self, name: str, hooks: list[FakeWebhook] | None = None, *, fail_create: bool = False) -> None:
        self.name = name
        self.id = "123456789012345678"
        self._hooks = hooks or []
        self.fail_create = fail_create
        self.created = []

    async def webhooks(self) -> list[FakeWebhook]:
        return list(self._hooks)

    async def create_webhook(self, *, name: str) -> FakeWebhook:
        if self.fail_create:
            raise RuntimeError("create failed")
        hook = FakeWebhook(name)
        self._hooks.append(hook)
        self.created.append(name)
        return hook


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_safe(report: dict) -> None:
    text = json.dumps(report, ensure_ascii=False)
    assert_true("123456789012345678" not in text, "raw Discord ID hidden")
    assert_true("https://" not in text and "http://" not in text, "webhook URL hidden")
    assert_true("secret-token" not in text, "secret hidden")
    assert_true(report.get("webhook_url_value_logged") is False, "webhook URL flag")
    assert_true(report.get("raw_discord_ids_logged") is False, "raw IDs flag")
    assert_true(report.get("secret_values_logged") is False, "secret flag")


def test_report_and_mapping() -> None:
    names = agent_webhook_names()
    assert_true(names["marin"] == "MARIN_STOXL", "marin name")
    assert_true(names["lucy"] == "LUCY_STOXL", "lucy name")
    assert_true(names["meiko"] == "MEIKO_STOXL", "meiko name")
    assert_true(names["kasumi"] == "KASUMI_STOXL", "kasumi name")
    assert_true(names["reze"] == "REZE_STOXL", "reze name")
    report = build_company_agent_webhook_persona_report()
    assert_true(report["webhook_persona_mode_available"] is True, "persona available")
    assert_true(report["default_webhook_persona_enabled"] is False, "default disabled")
    assert_true(report["webhook_create_supported"] is True, "create supported")
    assert_true(report["bot_message_fallback_supported"] is True, "fallback supported")
    assert_true(report["external_execution_allowed"] is False, "external false")
    assert_safe(report)


def test_dry_run_no_send_or_create() -> None:
    dry = build_company_agent_webhook_persona_dry_run("marin", "marketing-brief", "MML 인스타 문구")
    assert_true(dry["selected_agent"] == "marin", "dry marin")
    assert_true(dry["webhook_name"] == "MARIN_STOXL", "dry webhook name")
    assert_true(dry["webhook_persona_enabled"] is False, "dry disabled default")
    assert_true(dry["webhook_create_enabled"] is True, "dry create default")
    assert_true(dry["would_use_webhook_persona"] is True, "would use persona")
    assert_true(dry["discord_api_send_called"] is False, "dry no send")
    assert_true(dry["webhook_created"] is False, "dry no create")
    assert_safe(dry)


def test_async_webhook_reuse_create_and_send() -> None:
    async def run() -> None:
        existing = FakeWebhook("MARIN_STOXL")
        reuse_channel = FakeChannel("marketing-brief", [existing])
        reuse = await get_or_create_agent_webhook(reuse_channel, "marin", create_enabled=True)
        assert_true(reuse["webhook_reused"] is True, "reuse")
        assert_true(reuse["webhook_created"] is False, "not created")
        created_channel = FakeChannel("lucy-검토")
        created = await get_or_create_agent_webhook(created_channel, "lucy", create_enabled=True)
        assert_true(created["webhook_created"] is True, "created")
        assert_true(created_channel.created == ["LUCY_STOXL"], "created name")
        sent = await send_as_agent_webhook("lucy", created_channel, "검토 결과", create_enabled=True)
        assert_true(sent["webhook_persona_used"] is True, "persona used")
        assert_true(sent["webhook_name"] == "LUCY_STOXL", "send name")
        assert_true(sent["discord_message_sent"] is True, "sent")
        assert_safe(sent)

    asyncio.run(run())


def test_failure_falls_back_boundary() -> None:
    async def run() -> None:
        disabled = await send_as_agent_webhook("marin", FakeChannel("marketing-brief"), "content", create_enabled=False)
        assert_true(disabled["blocked"] is True, "create disabled blocks")
        assert_true("webhook_missing_create_disabled" in disabled["blocked_reasons"], "disabled reason")
        assert_safe(disabled)
        failed = await send_as_agent_webhook("marin", FakeChannel("marketing-brief", fail_create=True), "content", create_enabled=True)
        assert_true(failed["blocked"] is True, "create failure blocks")
        assert_true("webhook_create_failed" in failed["blocked_reasons"], "failure reason")
        assert_safe(failed)

    asyncio.run(run())


def test_handoff_and_approval_persona_names() -> None:
    handoff = build_company_agent_handoff_dry_run("marketing-brief", "!marin MML 인스타 문구 3개 뽑아줘")
    assert_true(handoff["webhook_name"] == "MARIN_STOXL", "handoff source persona")
    assert_true("[HANDOFF]" in handoff["handoff_message_preview"], "handoff marker")
    approval = build_company_agent_approval_dry_run("lucy-검토", "!approve-draft 이 문구 검토해줘")
    assert_true(approval["webhook_name"] == "LUCY_STOXL", "approval reviewer persona")
    assert_true("[APPROVAL_REQUEST]" in approval["approval_message_preview"], "approval marker")
    assert_true(approval["external_execution_performed"] is False, "external false")
    assert_safe(handoff)
    assert_safe(approval)


def main() -> int:
    tests = [
        test_report_and_mapping,
        test_dry_run_no_send_or_create,
        test_async_webhook_reuse_create_and_send,
        test_failure_falls_back_boundary,
        test_handoff_and_approval_persona_names,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All company agent webhook persona v0.3 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
