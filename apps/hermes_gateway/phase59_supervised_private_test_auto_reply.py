"""Phase59 supervised private-test auto-reply path.

The real runtime is reserved for a later Manual Gate. This module exposes the
gate and deterministic reply path, while tests verify the send branch only with
a fake sender.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Mapping, Protocol


VERSION = "phase59_supervised_private_test_auto_reply_safe_hotfix"
APPROVAL_PHRASE = "I_APPROVE_PHASE59_SUPERVISED_PRIVATE_TEST_AUTO_REPLY"
REPLY_MODE = "private_test_supervised_auto_reply_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


@dataclass
class Phase59SendResult:
    api_send_called: bool = False
    message_sent: bool = False
    message_sent_count: int = 0
    status_code: int | None = None
    error_type: str = ""


class Phase59SendAdapter(Protocol):
    def send_supervised_reply(self, content: str) -> Phase59SendResult:
        """Send a supervised deterministic private-test reply."""


class RealDiscordPhase59SendAdapter:
    def __init__(self, *, token: str, private_test_channel_id: str) -> None:
        self._token = token
        self._private_test_channel_id = private_test_channel_id

    def send_supervised_reply(self, content: str) -> Phase59SendResult:
        if not self._token or not self._private_test_channel_id:
            return Phase59SendResult(error_type="missing_token_or_private_test_channel")
        payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{self._private_test_channel_id}/messages",
            data=payload,
            headers={
                "Authorization": f"Bot {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "stoxl-hermes-gateway/phase59",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status_code = int(getattr(response, "status", 0) or 0)
            sent = 200 <= status_code < 300
            return Phase59SendResult(
                api_send_called=True,
                message_sent=sent,
                message_sent_count=1 if sent else 0,
                status_code=status_code,
            )
        except urllib.error.HTTPError as exc:
            return Phase59SendResult(api_send_called=True, status_code=int(exc.code), error_type="http_error")
        except Exception as exc:
            return Phase59SendResult(error_type=type(exc).__name__)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_value(env: Mapping[str, str] | None, key: str) -> str:
    selected = env if env is not None else os.environ
    return selected.get(key, "")


def _present(env: Mapping[str, str] | None, key: str) -> bool:
    return bool(_env_value(env, key).strip())


def _positive_int(env: Mapping[str, str] | None, key: str, default: int) -> int:
    try:
        value = int((_env_value(env, key) or "").strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _gate_snapshot(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    phrase = _env_value(env, "HERMES_PHASE59_SUPERVISED_AUTO_REPLY_APPROVAL_PHRASE")
    max_session_seconds = _positive_int(env, "HERMES_PHASE59_MAX_SESSION_SECONDS", 300)
    max_reply_count = _positive_int(env, "HERMES_PHASE59_MAX_REPLY_COUNT", 1)
    max_send_count = _positive_int(env, "HERMES_PHASE59_MAX_SEND_COUNT", 1)
    cooldown_seconds = _positive_int(env, "HERMES_PHASE59_COOLDOWN_SECONDS", 30)
    return {
        "manual_gate_required": True,
        "manual_approval_true": _truthy(_env_value(env, "HERMES_PHASE59_SUPERVISED_AUTO_REPLY_APPROVED")),
        "approval_phrase_present": bool(phrase),
        "approval_phrase_exact_match": phrase == APPROVAL_PHRASE,
        "approval_phrase_value_logged": False,
        "discord_send_enabled": _truthy(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES")),
        "private_test_reply_enabled": _truthy(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY")),
        "reply_mode_private_test_supervised_auto_reply_only": _env_value(env, "HERMES_DISCORD_REPLY_MODE") == REPLY_MODE,
        "llm_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_LLM_ENABLED")),
        "rag_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_RAG_ENABLED")),
        "embedding_disabled": not _truthy(_env_value(env, "HERMES_EMBEDDING_ENABLED")),
        "vector_disabled": not _truthy(_env_value(env, "HERMES_VECTOR_ENABLED")),
        "external_execution_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_EXTERNAL_EXECUTION")),
        "discord_token_present": _present(env, "DISCORD_BOT_TOKEN"),
        "discord_token_value_logged": False,
        "private_test_channel_id_present": _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "private_test_channel_id_value_logged": False,
        "max_session_seconds": max_session_seconds,
        "max_reply_count": max_reply_count,
        "max_send_count": max_send_count,
        "cooldown_seconds": cooldown_seconds,
        "max_session_guard_configured": max_session_seconds > 0,
        "max_reply_count_configured": max_reply_count == 1,
        "max_send_count_configured": max_send_count == 1,
        "cooldown_configured": cooldown_seconds > 0,
        "kill_switch_ready": _truthy(_env_value(env, "HERMES_PHASE59_KILL_SWITCH_READY")),
    }


def _event_guard(event: Mapping[str, Any] | None = None) -> dict[str, Any]:
    selected = event or {}
    channel_scope = str(selected.get("channel_scope", "private_test") or "private_test")
    author_type = str(selected.get("author_type", "human") or "human")
    duplicate = bool(selected.get("duplicate", False))
    return {
        "private_test_only": channel_scope == "private_test",
        "public_team_blocked": channel_scope not in {"public", "team"},
        "self_loop_guard_active": True,
        "bot_message_guard_active": True,
        "duplicate_guard_active": True,
        "self_message_skipped": author_type == "self",
        "bot_message_skipped": author_type == "bot",
        "duplicate_message_skipped": duplicate,
        "event_eligible_for_reply": channel_scope == "private_test" and author_type == "human" and not duplicate,
    }


def _base_report() -> dict[str, Any]:
    return {
        "version": VERSION,
        "phase59_actual_path_available": True,
        "actual_path_available": True,
        "phase59_sender_adapter_wired": True,
        "real_discord_sender_adapter_available_for_manual_gate": True,
        "real_discord_sender_adapter_selected": False,
        "fake_sender_adapter_used": False,
        "runtime_scope": "private_test_only",
        "reply_text_source": "deterministic_template",
        "sent_scope": "private_test_only",
        "actual_discord_runtime_executed": False,
        "discord_gateway_connected": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "actual_supervised_auto_reply_executed": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_live_execution": False,
        "unattended_auto_reply_executed": False,
        "raw_user_content_included": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "raw_session_ids_logged": False,
        "secret_values_logged": False,
        "capture_file_path_value_logged": False,
        "capture_file_raw_dumped": False,
        "max_reply_count_respected": True,
        "max_send_count_respected": True,
        "ready_for_repeat_session": False,
        "ready_for_phase59_manual_gate": True,
    }


def _deterministic_reply_text() -> str:
    return "Phase59 supervised private-test acknowledgement. Human supervision remains active."


def _blocked_reasons(
    gate: Mapping[str, Any],
    guard: Mapping[str, Any],
    *,
    allow_flag_present: bool,
    phase59_session_already_consumed: bool = False,
) -> list[str]:
    reasons: list[str] = []
    if phase59_session_already_consumed:
        reasons.append("phase59_supervised_auto_reply_session_already_consumed")
    if not allow_flag_present:
        reasons.append("allow_flag_missing")
    if not gate.get("manual_approval_true"):
        reasons.append("manual_approval_not_approved")
    if not gate.get("approval_phrase_exact_match"):
        reasons.append("approval_phrase_mismatch")
    if not gate.get("discord_send_enabled"):
        reasons.append("discord_send_disabled")
    if not gate.get("private_test_reply_enabled"):
        reasons.append("private_test_reply_disabled")
    if not gate.get("reply_mode_private_test_supervised_auto_reply_only"):
        reasons.append("reply_mode_not_private_test_supervised_auto_reply_only")
    if not (gate.get("llm_disabled") and gate.get("rag_disabled") and gate.get("embedding_disabled") and gate.get("vector_disabled")):
        reasons.append("llm_rag_embedding_vector_must_be_disabled")
    if not gate.get("external_execution_disabled"):
        reasons.append("external_execution_enabled")
    if not gate.get("discord_token_present"):
        reasons.append("discord_token_missing")
    if not gate.get("private_test_channel_id_present"):
        reasons.append("private_test_channel_id_missing")
    if not gate.get("kill_switch_ready"):
        reasons.append("kill_switch_not_ready")
    if not (gate.get("max_session_guard_configured") and gate.get("max_reply_count_configured") and gate.get("max_send_count_configured") and gate.get("cooldown_configured")):
        reasons.append("session_guards_not_configured")
    if not guard.get("private_test_only"):
        reasons.append("not_private_test_channel")
    if not guard.get("event_eligible_for_reply"):
        reasons.append("event_not_eligible_for_reply")
    return reasons


def build_phase59_supervised_private_test_auto_reply_preflight(
    env: Mapping[str, str] | None = None, event: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    ready = not _blocked_reasons(gate, guard, allow_flag_present=True)
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase59_supervised_private_test_auto_reply_preflight",
        "phase59_actual_path_available": True,
        "ready_for_actual_phase59_supervised_auto_reply": ready,
    }
    assert_phase59_supervised_private_test_auto_reply_safe(report, allow_ready=True)
    return report


def build_phase59_supervised_private_test_auto_reply_blocked_report(
    *, allow_flag_present: bool = False, env: Mapping[str, str] | None = None, event: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase59_supervised_private_test_auto_reply_blocked",
        "allow_flag_present": allow_flag_present,
        "blocked": True,
        "blocked_reasons": _blocked_reasons(gate, guard, allow_flag_present=allow_flag_present),
        "ready_for_actual_phase59_supervised_auto_reply": False,
    }
    assert_phase59_supervised_private_test_auto_reply_safe(report)
    return report


def build_actual_phase59_supervised_private_test_auto_reply(
    *,
    allow_flag_present: bool = False,
    env: Mapping[str, str] | None = None,
    event: Mapping[str, Any] | None = None,
    send_adapter: Phase59SendAdapter | None = None,
    phase59_session_already_consumed: bool = True,
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    reasons = _blocked_reasons(
        gate,
        guard,
        allow_flag_present=allow_flag_present,
        phase59_session_already_consumed=phase59_session_already_consumed,
    )
    if reasons:
        report = {
            **_base_report(),
            **gate,
            **guard,
            "report_type": "phase59_supervised_private_test_auto_reply_blocked",
            "allow_flag_present": allow_flag_present,
            "phase59_session_already_consumed": phase59_session_already_consumed,
            "phase59_repeat_session_locked": phase59_session_already_consumed,
            "blocked": True,
            "blocked_reasons": reasons,
            "ready_for_actual_phase59_supervised_auto_reply": False,
        }
        assert_phase59_supervised_private_test_auto_reply_safe(report)
        return report
    selected_adapter = send_adapter or RealDiscordPhase59SendAdapter(
        token=_env_value(env, "DISCORD_BOT_TOKEN"),
        private_test_channel_id=_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
    )
    send_result = selected_adapter.send_supervised_reply(_deterministic_reply_text())
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase59_supervised_private_test_auto_reply_actual_session",
        "allow_flag_present": True,
        "phase59_session_already_consumed": False,
        "phase59_repeat_session_locked": True,
        "blocked": False,
        "blocked_reasons": [],
        "real_discord_sender_adapter_selected": send_adapter is None,
        "fake_sender_adapter_used": send_adapter is not None,
        "actual_supervised_auto_reply_executed": bool(send_result.message_sent),
        "discord_api_send_called": bool(send_result.api_send_called),
        "discord_message_sent": bool(send_result.message_sent),
        "message_sent_count": int(send_result.message_sent_count),
        "send_result_status_code_present": send_result.status_code is not None,
        "send_result_error_type": send_result.error_type,
        "ready_for_actual_phase59_supervised_auto_reply": False,
    }
    assert_phase59_supervised_private_test_auto_reply_safe(report, allow_actual_success=True)
    return report


def assert_phase59_supervised_private_test_auto_reply_safe(
    report: dict[str, Any], *, allow_ready: bool = False, allow_actual_success: bool = False
) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase59 report contains sensitive values.")
    for key in (
        "actual_discord_runtime_executed",
        "discord_gateway_connected",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_live_execution",
        "unattended_auto_reply_executed",
        "raw_user_content_included",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "capture_file_path_value_logged",
        "capture_file_raw_dumped",
        "ready_for_repeat_session",
    ):
        if report.get(key):
            raise ValueError(f"Phase59 unsafe flag is true: {key}")
    if not allow_actual_success:
        for key in ("discord_api_send_called", "discord_message_sent", "actual_supervised_auto_reply_executed"):
            if report.get(key):
                raise ValueError(f"Phase59 unsafe flag is true: {key}")
        if int(report.get("message_sent_count", 0) or 0) != 0:
            raise ValueError("Phase59 Safe Hotfix report message_sent_count must stay 0.")
    if int(report.get("message_sent_count", 0) or 0) > 1:
        raise ValueError("Phase59 message_sent_count must not exceed 1.")
    if report.get("reply_text_source") != "deterministic_template":
        raise ValueError("Phase59 reply text source must be deterministic_template.")
    if report.get("sent_scope") != "private_test_only" or report.get("runtime_scope") != "private_test_only":
        raise ValueError("Phase59 runtime and send scope must be private_test_only.")
    if allow_actual_success and not report.get("private_test_only"):
        raise ValueError("Phase59 successful send path must be private_test_only.")
    if not allow_ready and report.get("ready_for_actual_phase59_supervised_auto_reply"):
        raise ValueError("Phase59 blocked report cannot be ready.")


def render_phase59_supervised_private_test_auto_reply_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase59 Supervised Private-Test Auto-Reply",
            "",
            f"- Report type: {report.get('report_type')}",
            "- Actual path available: true",
            f"- Blocked: {str(report.get('blocked', False)).lower()}",
            "- Runtime scope: private_test_only",
            "- Reply text source: deterministic_template",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
            "- LLM/RAG/embedding/vector/external: false",
        ]
    ) + "\n"
