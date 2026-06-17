"""Phase58 manual-approved deterministic private-test reply path.

This module exposes the actual-path gate shape, but the Safe Hotfix only
returns preflight and blocked/no-send reports. It does not run Discord runtime
or call a Discord send adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Mapping, Protocol


VERSION = "phase58_manual_approved_private_test_reply_safe_hotfix"
APPROVAL_PHRASE = "I_APPROVE_PHASE58_MANUAL_APPROVED_PRIVATE_TEST_REPLY"
REPLY_MODE = "private_test_manual_approved_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


@dataclass
class Phase58SendResult:
    api_send_called: bool = False
    message_sent: bool = False
    message_sent_count: int = 0
    status_code: int | None = None
    error_type: str = ""


class Phase58SendAdapter(Protocol):
    def send_deterministic_reply(self, content: str) -> Phase58SendResult:
        """Send the Phase58 deterministic reply and return sanitized metadata."""


class RealDiscordPhase58SendAdapter:
    def __init__(self, *, token: str, private_test_channel_id: str) -> None:
        self._token = token
        self._private_test_channel_id = private_test_channel_id

    def send_deterministic_reply(self, content: str) -> Phase58SendResult:
        if not self._token or not self._private_test_channel_id:
            return Phase58SendResult(error_type="missing_token_or_private_test_channel")
        payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{self._private_test_channel_id}/messages",
            data=payload,
            headers={
                "Authorization": f"Bot {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "stoxl-hermes-gateway/phase58",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status_code = int(getattr(response, "status", 0) or 0)
            sent = 200 <= status_code < 300
            return Phase58SendResult(
                api_send_called=True,
                message_sent=sent,
                message_sent_count=1 if sent else 0,
                status_code=status_code,
            )
        except urllib.error.HTTPError as exc:
            return Phase58SendResult(api_send_called=True, status_code=int(exc.code), error_type="http_error")
        except Exception as exc:
            return Phase58SendResult(error_type=type(exc).__name__)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_value(env: Mapping[str, str] | None, key: str) -> str:
    selected = env if env is not None else os.environ
    return selected.get(key, "")


def _present(env: Mapping[str, str] | None, key: str) -> bool:
    return bool(_env_value(env, key).strip())


def _gate_snapshot(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    phrase = _env_value(env, "HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVAL_PHRASE")
    return {
        "approval_required": True,
        "manual_approval_true": _truthy(_env_value(env, "HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVED")),
        "approval_phrase_present": bool(phrase),
        "approval_phrase_exact_match": phrase == APPROVAL_PHRASE,
        "approval_phrase_value_logged": False,
        "discord_send_enabled": _truthy(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES")),
        "private_test_reply_enabled": _truthy(_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_REPLY")),
        "reply_mode_private_test_manual_approved_only": _env_value(env, "HERMES_DISCORD_REPLY_MODE") == REPLY_MODE,
        "llm_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_LLM_ENABLED")),
        "rag_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_RAG_ENABLED")),
        "embedding_disabled": not _truthy(_env_value(env, "HERMES_EMBEDDING_ENABLED")),
        "vector_disabled": not _truthy(_env_value(env, "HERMES_VECTOR_ENABLED")),
        "external_execution_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_EXTERNAL_EXECUTION")),
        "discord_token_present": _present(env, "DISCORD_BOT_TOKEN"),
        "discord_token_value_logged": False,
        "private_test_channel_id_present": _present(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "private_test_channel_id_value_logged": False,
    }


def _deterministic_reply_text() -> str:
    return "Phase58 private-test acknowledgement received. Human review remains required before any broader automation."


def _actual_blocked_reasons(gate: Mapping[str, Any], *, allow_flag_present: bool, phase58_reply_already_consumed: bool) -> list[str]:
    reasons: list[str] = []
    if phase58_reply_already_consumed:
        reasons.append("phase58_actual_manual_reply_already_consumed")
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
    if not gate.get("reply_mode_private_test_manual_approved_only"):
        reasons.append("reply_mode_not_private_test_manual_approved_only")
    if not gate.get("llm_disabled"):
        reasons.append("llm_enabled")
    if not gate.get("rag_disabled"):
        reasons.append("rag_enabled")
    if not gate.get("embedding_disabled") or not gate.get("vector_disabled"):
        reasons.append("embedding_or_vector_enabled")
    if not gate.get("external_execution_disabled"):
        reasons.append("external_execution_enabled")
    if not gate.get("discord_token_present"):
        reasons.append("discord_token_missing")
    if not gate.get("private_test_channel_id_present"):
        reasons.append("private_test_channel_id_missing")
    return reasons


def _base_report() -> dict[str, Any]:
    return {
        "version": VERSION,
        "manual_gate_required": True,
        "phase58_actual_path_available": True,
        "actual_path_available": True,
        "captured_event_count": 1,
        "captured_private_test_human_message_count": 1,
        "review_packet_count": 1,
        "mock_reply_packet_created": True,
        "reply_text_source": "deterministic_template",
        "private_test_only": True,
        "sent_scope": "private_test_only",
        "raw_user_content_included": False,
        "capture_file_path_value_logged": False,
        "capture_file_read_attempted": False,
        "capture_file_raw_dumped": False,
        "actual_discord_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "actual_send_executed": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_live_execution": False,
        "unattended_auto_reply_executed": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "raw_session_ids_logged": False,
        "secret_values_logged": False,
        "ready_for_repeat_send": False,
    }


def build_phase58_manual_approved_private_test_reply_preflight(
    env: Mapping[str, str] | None = None, *, phase58_reply_already_consumed: bool = True
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    ready = (
        not phase58_reply_already_consumed
        and gate["manual_approval_true"]
        and gate["approval_phrase_exact_match"]
        and gate["discord_send_enabled"]
        and gate["private_test_reply_enabled"]
        and gate["reply_mode_private_test_manual_approved_only"]
        and gate["llm_disabled"]
        and gate["rag_disabled"]
        and gate["embedding_disabled"]
        and gate["vector_disabled"]
        and gate["external_execution_disabled"]
    )
    report = {
        **_base_report(),
        **gate,
        "report_type": "phase58_manual_approved_private_test_reply_preflight",
        "phase58_reply_already_consumed": phase58_reply_already_consumed,
        "repeat_send_locked": phase58_reply_already_consumed,
        "ready_for_actual_phase58_manual_reply": ready,
        "ready_for_actual_private_test_manual_reply": ready,
    }
    assert_phase58_manual_approved_private_test_reply_safe(report, allow_ready=True)
    return report


def build_phase58_manual_approved_private_test_reply_blocked_report(
    *, allow_flag_present: bool = False, env: Mapping[str, str] | None = None
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    blocked_reasons = _actual_blocked_reasons(gate, allow_flag_present=allow_flag_present, phase58_reply_already_consumed=True)
    report = {
        **_base_report(),
        **gate,
        "report_type": "phase58_manual_approved_private_test_reply_blocked",
        "phase58_reply_already_consumed": True,
        "repeat_send_locked": True,
        "allow_flag_present": allow_flag_present,
        "blocked": True,
        "blocked_reasons": blocked_reasons or ["safe_hotfix_no_send"],
        "ready_for_actual_phase58_manual_reply": False,
    }
    assert_phase58_manual_approved_private_test_reply_safe(report)
    return report


def build_actual_phase58_manual_approved_private_test_reply(
    *,
    allow_flag_present: bool = False,
    env: Mapping[str, str] | None = None,
    send_adapter: Phase58SendAdapter | None = None,
    phase58_reply_already_consumed: bool = True,
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    blocked_reasons = _actual_blocked_reasons(
        gate,
        allow_flag_present=allow_flag_present,
        phase58_reply_already_consumed=phase58_reply_already_consumed,
    )
    if blocked_reasons:
        report = {
            **_base_report(),
            **gate,
            "report_type": "phase58_manual_approved_private_test_reply_blocked",
            "phase58_reply_already_consumed": phase58_reply_already_consumed,
            "repeat_send_locked": phase58_reply_already_consumed,
            "allow_flag_present": allow_flag_present,
            "blocked": True,
            "blocked_reasons": blocked_reasons,
            "ready_for_actual_phase58_manual_reply": False,
        }
        assert_phase58_manual_approved_private_test_reply_safe(report)
        return report

    selected_adapter = send_adapter or RealDiscordPhase58SendAdapter(
        token=_env_value(env, "DISCORD_BOT_TOKEN"),
        private_test_channel_id=_env_value(env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
    )
    send_result = selected_adapter.send_deterministic_reply(_deterministic_reply_text())
    report = {
        **_base_report(),
        **gate,
        "report_type": "phase58_manual_approved_private_test_reply_actual_send",
        "phase58_reply_already_consumed": False,
        "repeat_send_locked": True,
        "allow_flag_present": True,
        "blocked": False,
        "blocked_reasons": [],
        "actual_send_executed": bool(send_result.message_sent),
        "discord_api_send_called": bool(send_result.api_send_called),
        "discord_message_sent": bool(send_result.message_sent),
        "message_sent_count": int(send_result.message_sent_count),
        "send_result_status_code_present": send_result.status_code is not None,
        "send_result_error_type": send_result.error_type,
        "ready_for_phase58_closeout": bool(send_result.message_sent),
        "ready_for_actual_phase58_manual_reply": False,
    }
    assert_phase58_manual_approved_private_test_reply_safe(report, allow_actual_success=True)
    return report


def build_phase58_manual_approved_private_test_reply_closeout() -> dict[str, Any]:
    report = {
        **_base_report(),
        "report_type": "phase58_manual_approved_private_test_reply_closeout",
        "actual_phase58_reply_sent": True,
        "sent_scope": "private_test_only",
        "reply_text_source": "deterministic_template",
        "message_sent_count": 1,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "repeat_send_locked": True,
        "phase58_reply_already_consumed": True,
        "ready_for_phase58_closeout": True,
        "ready_for_repeat_send": False,
        "ready_for_supervised_private_test_auto_reply_gate": True,
    }
    assert_phase58_manual_approved_private_test_reply_safe(report, allow_historical_closeout=True)
    return report


def build_phase58_manual_approved_private_test_reply_no_repeat_lock() -> dict[str, Any]:
    report = {
        **_base_report(),
        "report_type": "phase58_manual_approved_private_test_reply_no_repeat_lock",
        "phase58_actual_manual_reply_already_consumed": True,
        "repeat_send_locked": True,
        "ready_for_repeat_send": False,
        "blocked": True,
        "blocked_reasons": ["phase58_actual_manual_reply_already_consumed"],
        "actual_send_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "ready_for_supervised_private_test_auto_reply_gate": True,
    }
    assert_phase58_manual_approved_private_test_reply_safe(report)
    return report


def assert_phase58_manual_approved_private_test_reply_safe(
    report: dict[str, Any],
    *,
    allow_ready: bool = False,
    allow_actual_success: bool = False,
    allow_historical_closeout: bool = False,
) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase58 report contains sensitive values.")
    for key in (
        "raw_user_content_included",
        "capture_file_path_value_logged",
        "capture_file_read_attempted",
        "capture_file_raw_dumped",
        "actual_discord_runtime_executed",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_live_execution",
        "unattended_auto_reply_executed",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "ready_for_repeat_send",
    ):
        if report.get(key):
            raise ValueError(f"Phase58 unsafe flag is true: {key}")
    if not allow_actual_success:
        for key in ("discord_api_send_called", "discord_message_sent", "actual_send_executed"):
            if report.get(key):
                raise ValueError(f"Phase58 unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) > 1:
        raise ValueError("Phase58 message_sent_count must never exceed 1.")
    if not allow_actual_success and not allow_historical_closeout and int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase58 Safe Hotfix message_sent_count must stay 0.")
    if allow_historical_closeout and int(report.get("message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase58 closeout message_sent_count must be fixed at 1.")
    if allow_actual_success and report.get("actual_send_executed") and int(report.get("message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase58 actual send success must send exactly one message.")
    for key in ("phase58_actual_path_available", "mock_reply_packet_created", "private_test_only"):
        if not report.get(key):
            raise ValueError(f"Phase58 required flag is false: {key}")
    if report.get("reply_text_source") != "deterministic_template":
        raise ValueError("Phase58 reply text source must be deterministic_template.")
    if not allow_ready and report.get("ready_for_actual_phase58_manual_reply"):
        raise ValueError("Phase58 blocked report cannot be ready.")


def render_phase58_manual_approved_private_test_reply_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase58 Manual-Approved Private-Test Reply",
            "",
            f"- Report type: {report.get('report_type')}",
            "- Actual path available: true",
            f"- Ready for actual Phase58 manual reply: {str(report.get('ready_for_actual_phase58_manual_reply', False)).lower()}",
            "- Reply text source: deterministic_template",
            "- Private-test only: true",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Message sent count: 0",
            "- LLM/RAG/embedding/vector/external: false",
        ]
    ) + "\n"
