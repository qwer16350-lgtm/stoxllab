"""Phase 41B reply adapter boundary.

Adapters keep the actual Discord runtime separated from the one-shot gate and
make tests use fake events only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


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

    def __init__(self, *, token: str, private_test_channel_id: str) -> None:
        self._token = token
        self._private_test_channel_id = private_test_channel_id

    def collect_events(self, *, timeout_seconds: int, max_events: int) -> list[Phase41BReplyEvent]:
        import asyncio
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
            if str(getattr(message.channel, "id", "")) != self._private_test_channel_id:
                return
            author = getattr(message, "author", None)
            if bool(getattr(author, "bot", False)) or author == getattr(client, "user", None):
                events.append(Phase41BReplyEvent(channel_scope="private_test", author_type="bot" if bool(getattr(author, "bot", False)) else "self", source=message))
                return
            events.append(Phase41BReplyEvent(channel_scope="private_test", author_type="human", duplicate=False, source=message))
            if len(events) >= max(1, max_events):
                await client.close()

        client.run(self._token)
        return events

    def send_reply(self, event: Phase41BReplyEvent, content: str) -> Phase41BReplySendResult:
        import asyncio

        message = event.source
        if message is None:
            return Phase41BReplySendResult(error_type="missing_source_message", adapter_type=self.adapter_type)

        async def _reply() -> bool:
            await message.reply(content)
            return True

        try:
            sent = bool(asyncio.run(_reply()))
            return Phase41BReplySendResult(api_send_called=True, message_sent=sent, message_sent_count=1 if sent else 0, sent_scope="private_test_only" if sent else "none", adapter_type=self.adapter_type)
        except Exception as exc:
            return Phase41BReplySendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type=self.adapter_type, error_type=type(exc).__name__)
