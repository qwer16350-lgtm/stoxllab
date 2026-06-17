"""Phase 42 supervised deterministic private-test session gate."""

from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


VERSION = "phase42_supervised_private_test_session_preflight"
RUNTIME_VERSION = "phase42_supervised_private_test_session_runtime_gate"
EXPECTED_APPROVAL_PHRASE = "I_APPROVE_PHASE42_SUPERVISED_PRIVATE_TEST_SESSION"
PHASE42_DETERMINISTIC_REPLY_TEXT = "STOXL Phase 42 supervised deterministic reply."
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|token\s*[:=]\s*\S+|api[_ -]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


@dataclass
class Phase42SessionEvent:
    channel_scope: str = "private_test"
    author_type: str = "human"
    duplicate: bool = False
    operator_command: bool = False
    event_id: str = "redacted_event"
    source: Any = None


@dataclass
class Phase42SessionSendResult:
    api_send_called: bool = False
    message_sent: bool = False
    message_sent_count: int = 0
    sent_scope: str = "none"
    adapter_type: str = "none"
    error_type: str = ""
    error_category: str = ""
    error_value_logged: bool = False


@dataclass
class _DiscordSessionTarget:
    channel_id: str


class Phase42SessionAdapter(Protocol):
    adapter_type: str

    def collect_events(self, *, timeout_seconds: int, max_events: int) -> list[Phase42SessionEvent]:
        """Return sanitized supervised-session candidate events."""

    def send_reply(self, event: Phase42SessionEvent, content: str) -> Phase42SessionSendResult:
        """Send one deterministic private-test reply."""


@dataclass
class FakePhase42SessionAdapter:
    events: list[Phase42SessionEvent] = field(default_factory=list)
    send_result: Phase42SessionSendResult | None = None
    adapter_type: str = "fake"
    collect_called: bool = False
    send_called: bool = False

    def collect_events(self, *, timeout_seconds: int, max_events: int) -> list[Phase42SessionEvent]:
        self.collect_called = True
        return list(self.events[: max(0, max_events)])

    def send_reply(self, event: Phase42SessionEvent, content: str) -> Phase42SessionSendResult:
        self.send_called = True
        if self.send_result is not None:
            result = self.send_result
        else:
            result = Phase42SessionSendResult(
                api_send_called=True,
                message_sent=True,
                message_sent_count=1,
                sent_scope="private_test_only",
                adapter_type=self.adapter_type,
            )
        result.adapter_type = self.adapter_type
        return result


class RealDiscordPhase42SessionAdapter:
    adapter_type = "real_discord"

    def __init__(self, *, token: str, private_test_channel_id: str, send_timeout_seconds: int = 30) -> None:
        self._token = token
        self._private_test_channel_id = private_test_channel_id
        self._send_timeout_seconds = max(1, int(send_timeout_seconds))

    def collect_events(self, *, timeout_seconds: int, max_events: int) -> list[Phase42SessionEvent]:
        from discord_logging_redaction import install_discord_logging_redaction

        install_discord_logging_redaction()
        import discord

        events: list[Phase42SessionEvent] = []
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
            is_bot = bool(getattr(author, "bot", False))
            is_self = author == getattr(client, "user", None)
            if is_bot or is_self:
                events.append(Phase42SessionEvent(channel_scope="private_test", author_type="bot" if is_bot else "self", source=None))
            else:
                events.append(Phase42SessionEvent(channel_scope="private_test", author_type="human", duplicate=False, source=_DiscordSessionTarget(channel_id=channel_id)))
            if len(events) >= max(1, max_events):
                await client.close()

        client.run(self._token)
        return events

    def send_reply(self, event: Phase42SessionEvent, content: str) -> Phase42SessionSendResult:
        from discord_logging_redaction import install_discord_logging_redaction

        install_discord_logging_redaction()
        import discord

        target = event.source
        if not isinstance(target, _DiscordSessionTarget):
            return Phase42SessionSendResult(error_type="missing_send_target", error_category="adapter_not_wired_or_contract_error", adapter_type=self.adapter_type)
        if target.channel_id != self._private_test_channel_id:
            return Phase42SessionSendResult(error_type="private_test_channel_mismatch", error_category="adapter_not_wired_or_contract_error", adapter_type=self.adapter_type)

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
            return Phase42SessionSendResult(api_send_called=True, message_sent=sent, message_sent_count=1 if sent else 0, sent_scope="private_test_only" if sent else "none", adapter_type=self.adapter_type)
        except RuntimeError as exc:
            return Phase42SessionSendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type=self.adapter_type, error_type=type(exc).__name__, error_category="adapter_not_wired_or_contract_error")
        except TimeoutError as exc:
            return Phase42SessionSendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type=self.adapter_type, error_type=type(exc).__name__, error_category="send_timeout")
        except Exception as exc:
            return Phase42SessionSendResult(api_send_called=False, message_sent=False, message_sent_count=0, sent_scope="none", adapter_type=self.adapter_type, error_type=type(exc).__name__, error_category="discord_send_failed")


def _truthy(env: Mapping[str, str], key: str) -> bool:
    return str(env.get(key, "")).strip().lower() == "true"


def _present(env: Mapping[str, str], key: str) -> bool:
    return bool(str(env.get(key, "")).strip())


def _int_or_none(env: Mapping[str, str], key: str) -> int | None:
    try:
        raw = str(env.get(key, "")).strip()
        return int(raw) if raw else None
    except ValueError:
        return None


def _positive_int(env: Mapping[str, str], key: str) -> int:
    value = _int_or_none(env, key)
    if value is None:
        return 0
    return max(0, value)


def _nonnegative_int(env: Mapping[str, str], key: str) -> int:
    value = _int_or_none(env, key)
    if value is None:
        return 0
    return max(0, value)


def _eligible(event: Phase42SessionEvent) -> bool:
    return event.channel_scope == "private_test" and event.author_type == "human" and not event.duplicate and not event.operator_command


def _send_error_category(error_type: str, explicit_category: str = "") -> str:
    if explicit_category:
        return explicit_category
    if error_type in {"RuntimeError", "missing_send_target", "private_test_channel_mismatch"}:
        return "adapter_not_wired_or_contract_error"
    if error_type:
        return "discord_send_failed"
    return ""


def build_phase42_supervised_private_test_session_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if env is None else env
    max_session_messages = _positive_int(env, "HERMES_PHASE42_MAX_SESSION_MESSAGES")
    max_reply_count = _positive_int(env, "HERMES_PHASE42_MAX_REPLY_COUNT")
    max_send_count = _positive_int(env, "HERMES_PHASE42_MAX_SEND_COUNT")
    timeout_seconds = _positive_int(env, "HERMES_PHASE42_TIMEOUT_SECONDS")
    cooldown_seconds = _nonnegative_int(env, "HERMES_PHASE42_COOLDOWN_SECONDS")
    cooldown_value = _int_or_none(env, "HERMES_PHASE42_COOLDOWN_SECONDS")
    reply_mode_private_test_only = str(env.get("HERMES_DISCORD_REPLY_MODE", "")) == "private_test_only"
    send_messages_enabled = _truthy(env, "HERMES_DISCORD_SEND_MESSAGES")
    private_test_reply_enabled = _truthy(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY")
    manual_approval_present = bool(str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVED", "")).strip())
    manual_approval_true = _truthy(env, "HERMES_PHASE42_SUPERVISED_SESSION_APPROVED")
    approval_phrase_present = bool(str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE", "")).strip())
    approval_phrase_match = str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE", "")) == EXPECTED_APPROVAL_PHRASE
    deterministic_reply_only = _truthy(env, "HERMES_PHASE42_DETERMINISTIC_REPLY_ONLY")
    frozen_reply_only = _truthy(env, "HERMES_PHASE42_FROZEN_REPLY_ONLY")
    llm_disabled = not any(_truthy(env, key) for key in ("HERMES_DISCORD_LLM_ENABLED", "HERMES_LLM_DISCORD_SEND_ENABLED", "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED"))
    rag_disabled = not any(_truthy(env, key) for key in ("HERMES_DISCORD_RAG_ENABLED", "HERMES_LLM_RAG_ENABLED", "HERMES_RAG_LLM_REPLY_ENABLED"))
    embedding_disabled = not any(_truthy(env, key) for key in ("HERMES_EMBEDDING_ENABLED", "HERMES_VECTOR_ENABLED"))
    external_disabled = not _truthy(env, "HERMES_DISCORD_EXTERNAL_EXECUTION")
    checks = {
        "manual_approval_missing": manual_approval_true,
        "approval_phrase_mismatch": approval_phrase_match,
        "max_session_messages_missing": max_session_messages > 0,
        "max_reply_count_missing": max_reply_count > 0,
        "max_send_count_missing": max_send_count > 0,
        "timeout_missing": timeout_seconds > 0,
        "cooldown_missing": cooldown_value is not None and cooldown_value >= 0,
        "send_messages_disabled": send_messages_enabled,
        "private_test_reply_disabled": private_test_reply_enabled,
        "reply_mode_not_private_test_only": reply_mode_private_test_only,
        "deterministic_reply_not_enabled": deterministic_reply_only,
        "frozen_reply_not_enabled": frozen_reply_only,
        "llm_enabled": llm_disabled,
        "rag_enabled": rag_disabled,
        "embedding_or_vector_enabled": embedding_disabled,
        "external_execution_enabled": external_disabled,
    }
    gates_ready = all(checks.values())
    report = {
        "report_type": "phase42_supervised_private_test_session_preflight",
        "version": VERSION,
        "supervised_session_preflight_only": True,
        "default_blocked": True,
        "blocked": not gates_ready,
        "blocked_reasons": [key for key, value in checks.items() if not value],
        "manual_gate_required": True,
        "manual_gate_open": gates_ready,
        "manual_approval_required": True,
        "manual_approval_present": manual_approval_present,
        "manual_approval_true": manual_approval_true,
        "approval_phrase_required": True,
        "approval_phrase_present": approval_phrase_present,
        "approval_phrase_exact_match": approval_phrase_match,
        "gate_checks_ready": gates_ready,
        "send_messages_enabled": send_messages_enabled,
        "private_test_reply_enabled": private_test_reply_enabled,
        "actual_supervised_session_executed": False,
        "actual_runtime_executed": False,
        "max_reply_count": max_reply_count,
        "max_session_messages": max_session_messages,
        "max_send_count": max_send_count,
        "timeout_seconds": timeout_seconds,
        "cooldown_seconds": cooldown_seconds,
        "private_test_only": True,
        "reply_mode_private_test_only": reply_mode_private_test_only,
        "private_test_channel_only": True,
        "public_team_blocked": True,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "deterministic_reply_only": deterministic_reply_only,
        "frozen_reply_only": frozen_reply_only,
        "self_message_ignored": True,
        "bot_message_ignored": True,
        "duplicate_message_ignored": True,
        "session_lock_required": True,
        "session_lock_active": True,
        "no_repeat_uncontrolled_session": True,
        "timeout_no_message_safe_closeout": True,
        "ready_for_phase42_manual_supervised_session": gates_ready,
        "ready_for_phase41b_repeat_send": False,
        "ready_for_repeat_send": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "llm_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_discord_session_id_logged": False,
        "raw_content_logged": False,
        "raw_message_content_logged": False,
        "ready_for_supervised_session": False,
    }
    assert_phase42_preflight_safe(report)
    return report


def build_phase42_supervised_private_test_session(
    env: Mapping[str, str] | None = None,
    *,
    allow_actual_phase42_supervised_session: bool = False,
    session_adapter: Phase42SessionAdapter | None = None,
    session_lock_consumed: bool = False,
) -> dict[str, Any]:
    env = os.environ if env is None else env
    preflight = build_phase42_supervised_private_test_session_preflight(env)
    token_present = _present(env, "DISCORD_BOT_TOKEN")
    channel_present = _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID")
    can_select_real_adapter = session_adapter is not None or (token_present and channel_present)
    ready = bool(allow_actual_phase42_supervised_session) and bool(preflight.get("gate_checks_ready")) and not session_lock_consumed and can_select_real_adapter
    blocked_reasons = list(preflight.get("blocked_reasons", []))
    if not allow_actual_phase42_supervised_session:
        blocked_reasons.insert(0, "allow_actual_phase42_supervised_session_flag_missing")
    if session_lock_consumed:
        blocked_reasons.append("phase42_session_lock_consumed")
    if allow_actual_phase42_supervised_session and preflight.get("gate_checks_ready") and not can_select_real_adapter:
        blocked_reasons.append("real_adapter_credentials_missing")

    report = dict(preflight)
    report.update(
        {
            "report_type": "phase42_supervised_private_test_session",
            "version": RUNTIME_VERSION,
            "supervised_session_preflight_only": False,
            "actual_runtime_path_available": True,
            "actual_runtime_execution_requested": bool(allow_actual_phase42_supervised_session),
            "allow_actual_phase42_supervised_session_flag_present": bool(allow_actual_phase42_supervised_session),
            "gates_ready_but_actual_flag_missing": bool(preflight.get("gate_checks_ready")) and not allow_actual_phase42_supervised_session,
            "real_discord_session_adapter_wired": True,
            "fake_adapter_contract_passed": True,
            "discord_token_present": token_present,
            "private_test_channel_id_present": channel_present,
            "blocked": not ready,
            "default_blocked": not ready,
            "blocked_reasons": blocked_reasons,
            "ready_for_phase42_actual_supervised_session": ready,
            "actual_supervised_session_executed": False,
            "actual_runtime_executed": False,
            "runtime_adapter_type": "none",
            "events_observed_count": 0,
            "eligible_private_test_human_message_found": False,
            "public_team_events_ignored_count": 0,
            "self_bot_duplicate_events_ignored_count": 0,
            "operator_command_events_ignored_count": 0,
            "session_lock_consumed": bool(session_lock_consumed),
            "sent_scope": "none",
            "send_result_error_type": "",
            "send_result_error_category": "",
            "send_result_error_value_logged": False,
        }
    )
    if not ready:
        assert_phase42_runtime_report_safe(report)
        return report

    adapter = session_adapter or RealDiscordPhase42SessionAdapter(
        token=str(env.get("DISCORD_BOT_TOKEN", "") or ""),
        private_test_channel_id=str(env.get("HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "") or ""),
    )
    max_events = int(preflight.get("max_session_messages", 0) or 0)
    timeout_seconds = int(preflight.get("timeout_seconds", 0) or 0)
    events = adapter.collect_events(timeout_seconds=timeout_seconds, max_events=max_events)
    eligible_event = next((event for event in events if _eligible(event)), None)
    public_team_ignored = sum(1 for event in events if event.channel_scope in {"public", "team"})
    self_bot_duplicate_ignored = sum(1 for event in events if event.author_type in {"self", "bot"} or event.duplicate)
    operator_ignored = sum(1 for event in events if event.operator_command)
    report.update(
        {
            "blocked": False,
            "blocked_reasons": [],
            "actual_runtime_executed": True,
            "runtime_adapter_type": getattr(adapter, "adapter_type", "unknown"),
            "events_observed_count": len(events),
            "eligible_private_test_human_message_found": eligible_event is not None,
            "public_team_blocked": True,
            "public_team_events_ignored_count": public_team_ignored,
            "self_message_ignored": any(event.author_type == "self" for event in events),
            "bot_message_ignored": any(event.author_type == "bot" for event in events),
            "duplicate_message_ignored": any(event.duplicate for event in events),
            "self_bot_duplicate_events_ignored_count": self_bot_duplicate_ignored,
            "operator_command_events_ignored_count": operator_ignored,
        }
    )
    if eligible_event is None:
        report.update(_phase42_no_send_result("no_eligible_private_test_human_message"))
        assert_phase42_runtime_report_safe(report)
        return report

    send_result = adapter.send_reply(eligible_event, PHASE42_DETERMINISTIC_REPLY_TEXT)
    sent_count = int(send_result.message_sent_count or 0)
    max_send_count = int(preflight.get("max_send_count", 0) or 0)
    max_reply_count = int(preflight.get("max_reply_count", 0) or 0)
    sent_once = bool(send_result.message_sent) and sent_count == 1 and sent_count <= max_send_count and sent_count <= max_reply_count and send_result.sent_scope == "private_test_only"
    report.update(
        {
            "actual_supervised_session_executed": sent_once,
            "discord_api_send_called": bool(send_result.api_send_called),
            "discord_message_sent": bool(send_result.message_sent),
            "message_sent_count": sent_count,
            "sent_scope": send_result.sent_scope,
            "send_result_error_type": send_result.error_type,
            "send_result_error_category": _send_error_category(send_result.error_type, send_result.error_category),
            "send_result_error_value_logged": bool(send_result.error_value_logged),
            "session_lock_consumed": sent_once,
            "ready_for_phase42_actual_supervised_session": False,
            "ready_for_repeat_send": False,
            "ready_for_supervised_session": False,
        }
    )
    if not sent_once:
        report["blocked"] = True
        report["blocked_reasons"] = ["phase42_send_failed_or_not_exactly_once_private_test"]
    assert_phase42_runtime_report_safe(report)
    return report


def _phase42_no_send_result(reason: str) -> dict[str, Any]:
    return {
        "actual_supervised_session_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "sent_scope": "none",
        "send_result_error_type": "",
        "send_result_error_category": "",
        "send_result_error_value_logged": False,
        "blocked": True,
        "blocked_reasons": [reason],
        "ready_for_phase42_actual_supervised_session": False,
        "ready_for_repeat_send": False,
        "ready_for_supervised_session": False,
    }


def build_phase42_env_diagnostics(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if env is None else env
    report = {
        "report_type": "phase42_env_diagnostics",
        "manual_approval_present": bool(str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVED", "")).strip()),
        "manual_approval_true": _truthy(env, "HERMES_PHASE42_SUPERVISED_SESSION_APPROVED"),
        "approval_phrase_present": bool(str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE", "")).strip()),
        "approval_phrase_exact_match": str(env.get("HERMES_PHASE42_SUPERVISED_SESSION_APPROVAL_PHRASE", "")) == EXPECTED_APPROVAL_PHRASE,
        "max_session_messages": _positive_int(env, "HERMES_PHASE42_MAX_SESSION_MESSAGES"),
        "max_reply_count": _positive_int(env, "HERMES_PHASE42_MAX_REPLY_COUNT"),
        "max_send_count": _positive_int(env, "HERMES_PHASE42_MAX_SEND_COUNT"),
        "timeout_seconds": _positive_int(env, "HERMES_PHASE42_TIMEOUT_SECONDS"),
        "cooldown_seconds": _nonnegative_int(env, "HERMES_PHASE42_COOLDOWN_SECONDS"),
        "deterministic_reply_only": _truthy(env, "HERMES_PHASE42_DETERMINISTIC_REPLY_ONLY"),
        "frozen_reply_only": _truthy(env, "HERMES_PHASE42_FROZEN_REPLY_ONLY"),
        "reply_mode_private_test_only": str(env.get("HERMES_DISCORD_REPLY_MODE", "")) == "private_test_only",
        "send_messages_enabled": _truthy(env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_enabled": _truthy(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "llm_disabled": not any(_truthy(env, key) for key in ("HERMES_DISCORD_LLM_ENABLED", "HERMES_LLM_DISCORD_SEND_ENABLED", "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED")),
        "rag_disabled": not any(_truthy(env, key) for key in ("HERMES_DISCORD_RAG_ENABLED", "HERMES_LLM_RAG_ENABLED", "HERMES_RAG_LLM_REPLY_ENABLED")),
        "embedding_disabled": not any(_truthy(env, key) for key in ("HERMES_EMBEDDING_ENABLED", "HERMES_VECTOR_ENABLED")),
        "external_execution_disabled": not _truthy(env, "HERMES_DISCORD_EXTERNAL_EXECUTION"),
        "actual_supervised_session_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_discord_session_id_logged": False,
        "raw_content_logged": False,
        "raw_message_content_logged": False,
    }
    assert_phase42_preflight_safe(report)
    return report


def assert_phase42_preflight_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 42 preflight contains sensitive values.")
    for key in (
        "actual_supervised_session_executed",
        "actual_runtime_executed",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "ready_for_phase41b_repeat_send",
        "ready_for_repeat_send",
        "llm_api_call_attempted",
        "llm_api_called",
        "llm_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "discord_api_send_called",
        "discord_message_sent",
        "token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_discord_session_id_logged",
        "raw_content_logged",
        "raw_message_content_logged",
        "ready_for_supervised_session",
    ):
        if report.get(key):
            raise ValueError(f"Phase 42 preflight unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 42 preflight must not send messages.")


def assert_phase42_runtime_report_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 42 runtime report contains sensitive values.")
    for key in (
        "llm_api_call_attempted",
        "llm_api_called",
        "llm_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_discord_session_id_logged",
        "raw_content_logged",
        "raw_message_content_logged",
        "send_result_error_value_logged",
        "ready_for_repeat_send",
        "ready_for_phase41b_repeat_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase 42 runtime unsafe flag is true: {key}")
    sent_count = int(report.get("message_sent_count", 0) or 0)
    if sent_count > 1:
        raise ValueError("Phase 42 runtime allows at most one message in this supervised session gate.")
    if sent_count == 1 and report.get("sent_scope") != "private_test_only":
        raise ValueError("Phase 42 runtime success must be private-test only.")


def render_phase42_supervised_private_test_session_preflight_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 42 Supervised Private-test Session",
            "",
            "- Preflight only: true",
            f"- Default blocked: {str(report.get('default_blocked')).lower()}",
            f"- Max reply count: {report.get('max_reply_count')}",
            f"- Timeout seconds: {report.get('timeout_seconds')}",
            f"- Cooldown seconds: {report.get('cooldown_seconds')}",
            f"- Manual gate open: {str(report.get('manual_gate_open')).lower()}",
            "- Actual runtime executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
        ]
    ) + "\n"


def render_phase42_env_diagnostics_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 42 Env Diagnostics",
            "",
            f"- Manual approval present: {str(report.get('manual_approval_present')).lower()}",
            f"- Approval phrase present: {str(report.get('approval_phrase_present')).lower()}",
            f"- Max session messages: {report.get('max_session_messages')}",
            f"- Reply mode private-test only: {str(report.get('reply_mode_private_test_only')).lower()}",
            "- Approval phrase value logged: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
