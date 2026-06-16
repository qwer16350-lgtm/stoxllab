"""Phase 40T-1 private-test read-only live runner boundary.

Codex tests use injected fake adapters only. The default Discord adapter is
available for a human-run command path and never sends/replies.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Mapping, Protocol

from phase40t_readonly_capture_writer import write_redacted_capture_file
from phase40t_readonly_live_execution_gate import build_phase40t_readonly_live_execution_gate
from phase40t_readonly_runtime_closeout import build_phase40t_readonly_runtime_closeout
from phase40t_discord_login_failure_closeout import (
    build_phase40t_discord_login_failure_closeout_from_exception,
    build_phase40t_missing_env_before_login_closeout,
)
from phase40t_readonly_preflight_snapshot import snapshot_has_login_prerequisites


class ReadOnlyLiveAdapter(Protocol):
    def run(self, *, timeout_seconds: int, max_events: int) -> dict[str, Any]:
        ...


class FakeReadOnlyLiveAdapter:
    def __init__(
        self,
        *,
        gateway_connected: bool = True,
        events: list[dict[str, Any]] | None = None,
        exit_reason: str = "timeout",
    ) -> None:
        self.gateway_connected = gateway_connected
        self.events = events or []
        self.exit_reason = exit_reason
        self.called = False

    def run(self, *, timeout_seconds: int, max_events: int) -> dict[str, Any]:
        self.called = True
        return {
            "started": True,
            "live_runtime_started": True,
            "discord_gateway_connected": bool(self.gateway_connected),
            "exit_reason": self.exit_reason,
            "events": self.events[:max_events] if max_events >= 0 else self.events,
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
        }


class DiscordReadOnlyLiveAdapter:
    def __init__(self, env: Mapping[str, str], preflight_snapshot: Mapping[str, Any] | None = None) -> None:
        self.env = env
        self.preflight_snapshot = preflight_snapshot

    def run(self, *, timeout_seconds: int, max_events: int) -> dict[str, Any]:
        return asyncio.run(self._run_async(timeout_seconds=timeout_seconds, max_events=max_events))

    async def _run_async(self, *, timeout_seconds: int, max_events: int) -> dict[str, Any]:
        try:
            import discord
        except ImportError:
            return {
                "started": False,
                "live_runtime_started": False,
                "discord_gateway_connected": False,
                "exit_reason": "discord_py_missing",
                "events": [],
                "discord_api_send_called": False,
                "discord_message_sent": False,
                "message_sent_count": 0,
            }
        token = str(self.env.get("DISCORD_BOT_TOKEN", "") or "")
        private_channel_id = str(self.env.get("HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "") or "")
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        client = discord.Client(intents=intents)
        events: list[dict[str, Any]] = []
        state = {"connected": False, "exit_reason": "timeout"}

        async def close_client_safely() -> None:
            try:
                await client.close()
            except Exception:
                return

        @client.event
        async def on_ready() -> None:
            state["connected"] = True
            if max_events == 0:
                state["exit_reason"] = "max_events"
                await close_client_safely()

        @client.event
        async def on_message(message: Any) -> None:
            author = getattr(message, "author", None)
            channel = getattr(message, "channel", None)
            channel_id = str(getattr(channel, "id", "") or "")
            is_self = str(getattr(author, "id", "") or "") == str(getattr(getattr(client, "user", None), "id", "") or "")
            is_bot = bool(getattr(author, "bot", False))
            channel_scope = "private_test" if channel_id and channel_id == private_channel_id else "unknown"
            decision = "capture_only"
            author_kind = "human"
            if is_self:
                decision = "skip_self"
                author_kind = "self"
            elif is_bot:
                decision = "skip_bot"
                author_kind = "bot"
            elif channel_scope != "private_test":
                decision = "block_public_team"
                channel_scope = "public_blocked"
                author_kind = "unknown" if not author else "human"
            events.append(
                {
                    "event_id": getattr(message, "id", ""),
                    "message_id": getattr(message, "id", ""),
                    "channel_scope": channel_scope,
                    "author_kind": author_kind,
                    "is_self": is_self,
                    "is_bot": is_bot,
                    "is_duplicate": False,
                    "decision": decision,
                }
            )
            if len(events) >= max_events:
                state["exit_reason"] = "max_events"
                await close_client_safely()

        try:
            await asyncio.wait_for(client.start(token), timeout=max(1, int(timeout_seconds)))
        except asyncio.TimeoutError:
            if state["connected"]:
                state["exit_reason"] = "timeout"
                await close_client_safely()
            else:
                await close_client_safely()
                return build_phase40t_discord_login_failure_closeout_from_exception(
                    self.env,
                    asyncio.TimeoutError(),
                    preflight_snapshot=self.preflight_snapshot,
                )
        except KeyboardInterrupt as exc:
            await close_client_safely()
            return build_phase40t_discord_login_failure_closeout_from_exception(
                self.env,
                exc,
                preflight_snapshot=self.preflight_snapshot,
            )
        except Exception as exc:
            await close_client_safely()
            return build_phase40t_discord_login_failure_closeout_from_exception(
                self.env,
                exc,
                preflight_snapshot=self.preflight_snapshot,
            )
        return {
            "started": True,
            "live_runtime_started": True,
            "discord_gateway_connected": bool(state["connected"]),
            "exit_reason": state["exit_reason"],
            "events": events,
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
        }


def run_phase40t_readonly_live_runtime(
    env: Mapping[str, str] | None = None,
    *,
    execute_flag_present: bool = False,
    timeout_seconds: int = 60,
    max_events: int = 10,
    capture_root: str | Path | None = None,
    root: str | Path | None = None,
    adapter: ReadOnlyLiveAdapter | None = None,
) -> dict[str, Any]:
    env_source = env if env is not None else os.environ
    gate = build_phase40t_readonly_live_execution_gate(
        env=env_source,
        execute_flag_present=execute_flag_present,
        timeout_seconds=timeout_seconds,
        max_events=max_events,
        capture_root=capture_root,
        root=root,
    )
    preflight_snapshot = gate.get("preflight_snapshot")
    if gate.get("blocked"):
        reason = str(gate.get("reason", ""))
        if execute_flag_present and (
            "discord_token_missing" in reason or "private_test_channel_id_missing" in reason
        ):
            return build_phase40t_missing_env_before_login_closeout(
                env=env_source,
                preflight_snapshot=preflight_snapshot if isinstance(preflight_snapshot, dict) else None,
                execute_flag_present=execute_flag_present,
            )
        return gate
    if not snapshot_has_login_prerequisites(preflight_snapshot):
        return build_phase40t_missing_env_before_login_closeout(
            env=env_source,
            preflight_snapshot=preflight_snapshot,
            execute_flag_present=execute_flag_present,
        )
    runner = adapter or DiscordReadOnlyLiveAdapter(env_source, preflight_snapshot=preflight_snapshot)
    try:
        result = runner.run(timeout_seconds=int(timeout_seconds), max_events=int(max_events))
    except (KeyboardInterrupt, Exception) as exc:
        return build_phase40t_discord_login_failure_closeout_from_exception(
            env_source,
            exc,
            preflight_snapshot=preflight_snapshot,
        )
    if result.get("report_type") == "phase40t_discord_login_failure_closeout":
        return result
    capture = write_redacted_capture_file(
        result.get("events", []),
        capture_root=capture_root,
        root=root,
    )
    events = capture.get("payload", {}).get("events", []) if capture.get("capture_file_written") else []
    closeout = build_phase40t_readonly_runtime_closeout(
        started=bool(result.get("started")),
        gateway_connected=bool(result.get("discord_gateway_connected")),
        timeout_seconds=int(timeout_seconds),
        max_events=int(max_events),
        exit_reason=str(result.get("exit_reason", "timeout")),
        captured_event_count=len(events),
        captured_private_test_human_message_count=sum(
            1 for item in events if item.get("channel_scope") == "private_test" and item.get("author_kind") == "human"
        ),
        captured_self_message_count=sum(1 for item in events if item.get("author_kind") == "self" or item.get("is_self")),
        captured_bot_message_count=sum(1 for item in events if item.get("author_kind") == "bot" or item.get("is_bot")),
        captured_duplicate_message_count=sum(1 for item in events if item.get("is_duplicate")),
        captured_public_team_blocked_count=sum(1 for item in events if item.get("channel_scope") in {"public_blocked", "team_blocked"}),
        capture_file_written=bool(capture.get("capture_file_written")),
        capture_file_path_logged=bool(capture.get("capture_file_path_logged")),
        preflight_snapshot=preflight_snapshot if isinstance(preflight_snapshot, dict) else None,
    )
    closeout["execute_flag_present"] = True
    return closeout
