"""Phase 41B reply adapter boundary.

Adapters keep the actual Discord runtime separated from the one-shot gate and
make tests use fake events only.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol

from discord_logging_redaction import install_discord_logging_redaction


DETERMINISTIC_REPLY_TEXT = "STOXL private-test deterministic reply."


@dataclass
class Phase41BReplyEvent:
    channel_scope: str = "private_test"
    author_type: str = "human"
    duplicate: bool = False
    event_id: str = "redacted_event"
    source: Any = None


@dataclass
class Phase41BReplySendResult:
    api_send_called: bool = False
    message_sent: bool = False
    message_sent_count: int = 0
    sent_scope: str = "none"
    adapter_type: str = "none"
    error_type: str = ""
    error_category: str = ""
    error_value_logged: bool = False


@dataclass
class _DiscordReplyTarget:
    channel_id: str


class Phase41BReplyAdapter(Protocol):
    adapter_type: str

    def collect_events(self, *, timeout_seconds: int, max_events: int) -> list[Phase41BReplyEvent]:
        """Return sanitized candidate events."""

    def send_reply(self, event: Phase41BReplyEvent, content: str) -> Phase41BReplySendResult:
        """Send one deterministic private-test reply."""


@dataclass
class FakePhase41BReplyAdapter:
    events: list[Phase41BReplyEvent] = field(default_factory=list)
    send_result: Phase41BReplySendResult | None = None
    adapter_type: str = "fake"
    collect_called: bool = False
    send_called: bool = False

    def collect_events(self, *, timeout_seconds: int, max_events: int) -> list[Phase41BReplyEvent]:
        self.collect_called = True
        return list(self.events[: max(0, max_events)])

    def send_reply(self, event: Phase41BReplyEvent, content: str) -> Phase41BReplySendResult:
        self.send_called = True
        if self.send_result is not None:
            result = self.send_result
        else:
            result = Phase41BReplySendResult(api_send_called=True, message_sent=True, message_sent_count=1, sent_scope="private_test_only", adapter_type=self.adapter_type)
        result.adapter_type = self.adapter_type
        return result


class RealDiscordPhase41BReplyAdapter:
    adapter_type = "real_discord"

    def __init__(self, *, token: str, private_test_channel_id: str, send_timeout_seconds: int = 30) -> None:
        self._token = token
        self._private_test_channel_id = private_test_channel_id
        self._send_timeout_seconds = max(1, int(send_timeout_seconds))

    def collect_events(self, *, timeout_seconds: int, max_events: int) -> list[Phase41BReplyEvent]:
        install_discord_logging_redaction()
        import discord

        events: list[Phase41BReplyEvent] = []
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        client = discord.Client(intents=intents)

        async def close_after_timeout() -> None:
            await asyncio.sleep(timeout_seconds)
            await client.close()

        @client.event
        async def on_ready() -> None:
            client.loop.create_task(close_after_timeout())

        @client.event
        async def on_message(message: Any) -> None:
            channel = getattr(message, "channel", None)
            channel_id = str(getattr(channel, "id", ""))
            if channel_id != self._private_test_channel_id:
                return
            author = getattr(message, "author", None)
            if bool(getattr(author, "bot", False)) or author == getattr(client, "user", None):
                events.append(Phase41BReplyEvent(channel_scope="private_test", author_type="bot" if bool(getattr(author, "bot", False)) else "self", source=message))
                return
            events.append(Phase41BReplyEvent(channel_scope="private_test", author_type="human", duplicate=False, source=_DiscordReplyTarget(channel_id=channel_id)))
            if len(events) >= max(1, max_events):
                await client.close()

        client.run(self._token)
        return events

    def send_reply(self, event: Phase41BReplyEvent, content: str) -> Phase41BReplySendResult:
        install_discord_logging_redaction()
        import discord

        target = event.source
        if not isinstance(target, _DiscordReplyTarget):
            return Phase41BReplySendResult(error_type="missing_send_target", error_category="adapter_not_wired_or_contract_error", adapter_type=self.adapter_type)
        if target.channel_id != self._private_test_channel_id:
            return Phase41BReplySendResult(error_type="private_test_channel_mismatch", error_category="adapter_not_wired_or_contract_error", adapter_type=self.adapter_type)

        async def _reply() -> bool:
            intents = discord.Intents.default()
            intents.guilds = True
            intents.messages = True
            client = discord.Client(intents=intents)
            sent = False

            @client.event
            async def on_ready() -> None:
                nonlocal sent
                try:
                    channel = client.get_channel(int(self._private_test_channel_id))
                    if channel is None:
                        channel = await client.fetch_channel(int(self._private_test_channel_id))
                    if not hasattr(channel, "send"):
                        raise RuntimeError("discord_channel_send_unavailable")
                    await channel.send(content)
                    sent = True
                finally:
                    await client.close()

            try:
                await asyncio.wait_for(client.start(self._token), timeout=self._send_timeout_seconds)
            finally:
                if not client.is_closed():
                    await client.close()
            return sent

        try:
            sent = bool(asyncio.run(_reply()))
            return Phase41BReplySendResult(api_send_called=True, message_sent=sent, message_sent_count=1 if sent else 0, sent_scope="private_test_only" if sent else "none", adapter_type=self.adapter_type)
        except RuntimeError as exc:
            return Phase41BReplySendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type=self.adapter_type, error_type=type(exc).__name__, error_category="adapter_not_wired_or_contract_error")
        except TimeoutError as exc:
            return Phase41BReplySendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type=self.adapter_type, error_type=type(exc).__name__, error_category="send_timeout")
        except Exception as exc:
            return Phase41BReplySendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type=self.adapter_type, error_type=type(exc).__name__, error_category="discord_send_failed")
