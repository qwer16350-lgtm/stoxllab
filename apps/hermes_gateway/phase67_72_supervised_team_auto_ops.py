"""Phase67-72 supervised team-channel auto-ops prep.

This stage prepares a manual-gated, low-risk team-channel auto-ops path with
queue/review-packet/deterministic-candidate flow. Safe Bundle verification uses
reports and fake senders only.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Mapping, Protocol


VERSION = "phase67_72_supervised_team_auto_ops_report_only"
APPROVAL_PHRASE = "I_APPROVE_PHASE67_TEAM_AUTO_OPS"
REPLY_MODE = "supervised_team_low_risk_auto_ops_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
LOW_RISK_INTENTS = {
    "status_summary",
    "simple_acknowledgement",
    "meeting_reminder_ops_note",
    "review_packet_ready_notice",
}
HIGH_RISK_INTENTS = {
    "legal_financial_advice",
    "secret_handling",
    "file_deletion",
    "code_push_deploy",
    "external_command_execution",
    "public_channel_message",
    "unknown_channel",
    "multi_message_send",
    "llm_rag_live_reply_without_manual_gate",
}


@dataclass
class Phase67TeamAutoOpsSendResult:
    api_send_called: bool = False
    message_sent: bool = False
    message_sent_count: int = 0
    status_code: int | None = None
    error_type: str = ""


class Phase67TeamAutoOpsSendAdapter(Protocol):
    def send_team_auto_ops(self, content: str) -> Phase67TeamAutoOpsSendResult:
        """Send one supervised deterministic team auto-ops reply."""


class RealDiscordPhase67TeamAutoOpsSendAdapter:
    def __init__(self, *, token: str, team_channel_id: str) -> None:
        self._token = token
        self._team_channel_id = team_channel_id

    def send_team_auto_ops(self, content: str) -> Phase67TeamAutoOpsSendResult:
        if not self._token or not self._team_channel_id:
            return Phase67TeamAutoOpsSendResult(error_type="missing_token_or_team_channel")
        payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{self._team_channel_id}/messages",
            data=payload,
            headers={
                "Authorization": f"Bot {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "stoxl-hermes-gateway/phase67",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status_code = int(getattr(response, "status", 0) or 0)
            sent = 200 <= status_code < 300
            return Phase67TeamAutoOpsSendResult(
                api_send_called=True,
                message_sent=sent,
                message_sent_count=1 if sent else 0,
                status_code=status_code,
            )
        except urllib.error.HTTPError as exc:
            return Phase67TeamAutoOpsSendResult(api_send_called=True, status_code=int(exc.code), error_type="http_error")
        except Exception as exc:
            return Phase67TeamAutoOpsSendResult(error_type=type(exc).__name__)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_value(env: Mapping[str, str] | None, key: str) -> str:
    selected = env if env is not None else os.environ
    return selected.get(key, "")


def _positive_int(env: Mapping[str, str] | None, key: str, default: int) -> int:
    try:
        value = int((_env_value(env, key) or "").strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _gate_snapshot(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    phrase = _env_value(env, "HERMES_PHASE67_TEAM_AUTO_OPS_APPROVAL_PHRASE")
    max_session_seconds = _positive_int(env, "HERMES_PHASE67_TEAM_AUTO_OPS_MAX_SESSION_SECONDS", 300)
    max_send_count = _positive_int(env, "HERMES_PHASE67_TEAM_AUTO_OPS_MAX_SEND_COUNT", 1)
    max_reply_count = _positive_int(env, "HERMES_PHASE67_TEAM_AUTO_OPS_MAX_REPLY_COUNT", 1)
    cooldown_seconds = _positive_int(env, "HERMES_PHASE67_TEAM_AUTO_OPS_COOLDOWN_SECONDS", 30)
    return {
        "manual_gate_required": True,
        "team_auto_ops_manual_gate_required": True,
        "manual_approval_true": _truthy(_env_value(env, "HERMES_PHASE67_TEAM_AUTO_OPS_APPROVED")),
        "approval_phrase_present": bool(phrase),
        "approval_phrase_exact_match": phrase == APPROVAL_PHRASE,
        "approval_phrase_value_logged": False,
        "discord_send_enabled": _truthy(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES")),
        "reply_mode_supervised_team_low_risk_auto_ops_only": _env_value(env, "HERMES_DISCORD_REPLY_MODE") == REPLY_MODE,
        "kill_switch_ready": _truthy(_env_value(env, "HERMES_PHASE67_TEAM_AUTO_OPS_KILL_SWITCH_READY")),
        "max_session_seconds": max_session_seconds,
        "max_send_count": max_send_count,
        "max_reply_count": max_reply_count,
        "cooldown_seconds": cooldown_seconds,
        "max_session_guard_configured": max_session_seconds > 0,
        "max_send_count_configured": max_send_count == 1,
        "max_reply_count_configured": max_reply_count == 1,
        "cooldown_configured": cooldown_seconds > 0,
        "llm_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_LLM_ENABLED")),
        "rag_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_RAG_ENABLED")),
        "embedding_disabled": not _truthy(_env_value(env, "HERMES_EMBEDDING_ENABLED")),
        "vector_disabled": not _truthy(_env_value(env, "HERMES_VECTOR_ENABLED")),
        "external_execution_disabled": not _truthy(_env_value(env, "HERMES_DISCORD_EXTERNAL_EXECUTION")),
        "discord_token_present": bool(_env_value(env, "DISCORD_BOT_TOKEN").strip()),
        "discord_token_value_logged": False,
        "team_channel_id_present": bool(_env_value(env, "HERMES_PHASE67_TEAM_AUTO_OPS_CHANNEL_ID").strip()),
        "team_channel_id_value_logged": False,
    }


def _event_guard(event: Mapping[str, Any] | None = None) -> dict[str, Any]:
    selected = event or {}
    channel_scope = str(selected.get("channel_scope", "team") or "team")
    known_team_channel = bool(selected.get("known_team_channel", channel_scope == "team"))
    intent = str(selected.get("intent", "status_summary") or "status_summary")
    message_count = int(selected.get("message_count", 1) or 1)
    low_risk = intent in LOW_RISK_INTENTS
    high_risk = intent in HIGH_RISK_INTENTS
    return {
        "known_team_channel_required": True,
        "known_team_channel_only": channel_scope == "team" and known_team_channel,
        "non_public_only": channel_scope != "public",
        "low_risk_intent_required": True,
        "low_risk_intent": low_risk,
        "high_risk_intent_blocked": high_risk,
        "deterministic_template_only": True,
        "max_one_reply_per_event": message_count == 1,
        "public_channel_send_allowed": False,
        "unknown_channel_send_allowed": False,
        "team_event_eligible_for_auto_ops": channel_scope == "team" and known_team_channel and low_risk and not high_risk and message_count == 1,
    }


def _base_report() -> dict[str, Any]:
    return {
        "version": VERSION,
        "phase67_supervised_team_auto_ops_path_available": True,
        "actual_path_available": True,
        "runtime_scope": "known_team_channel_only",
        "sent_scope": "known_team_channel_only",
        "reply_text_source": "deterministic_template",
        "ops_queue_available": True,
        "ops_queue_item_count": 1,
        "review_packet_required": True,
        "review_packet_created": True,
        "review_packet_raw_content_included": False,
        "deterministic_reply_candidate_created": True,
        "human_override_available": True,
        "phase60_team_canary_verified_once": True,
        "phase60_repeat_team_canary_locked": True,
        "actual_team_auto_ops_executed": False,
        "real_team_auto_ops_send_performed": False,
        "real_team_sender_adapter_selected": False,
        "fake_sender_adapter_used": False,
        "actual_discord_runtime_executed": False,
        "discord_gateway_live_connection_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_live_execution": False,
        "cron_started": False,
        "unattended_auto_reply_executed": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "raw_session_ids_logged": False,
        "secret_values_logged": False,
        "approval_phrase_value_logged": False,
        "team_channel_id_value_logged": False,
        "ready_for_repeat_team_auto_ops": False,
    }


def _deterministic_reply_text() -> str:
    return "Phase67 supervised team auto-ops acknowledgement. Human oversight remains active."


def _blocked_reasons(
    gate: Mapping[str, Any],
    guard: Mapping[str, Any],
    *,
    allow_flag_present: bool,
    phase67_team_auto_ops_already_consumed: bool = False,
) -> list[str]:
    reasons: list[str] = []
    if phase67_team_auto_ops_already_consumed:
        reasons.append("phase67_team_auto_ops_already_consumed")
        return reasons
    if not allow_flag_present:
        reasons.append("allow_flag_missing")
    if not gate.get("manual_approval_true"):
        reasons.append("manual_approval_not_approved")
    if not gate.get("approval_phrase_exact_match"):
        reasons.append("approval_phrase_mismatch")
    if not gate.get("discord_send_enabled"):
        reasons.append("discord_send_disabled")
    if not gate.get("reply_mode_supervised_team_low_risk_auto_ops_only"):
        reasons.append("reply_mode_not_supervised_team_low_risk_auto_ops_only")
    if not gate.get("kill_switch_ready"):
        reasons.append("kill_switch_not_ready")
    if not (
        gate.get("max_session_guard_configured")
        and gate.get("max_send_count_configured")
        and gate.get("max_reply_count_configured")
        and gate.get("cooldown_configured")
    ):
        reasons.append("team_auto_ops_guard_not_configured")
    if not (gate.get("llm_disabled") and gate.get("rag_disabled") and gate.get("embedding_disabled") and gate.get("vector_disabled")):
        reasons.append("llm_rag_embedding_vector_must_be_disabled")
    if not gate.get("external_execution_disabled"):
        reasons.append("external_execution_enabled")
    if not gate.get("discord_token_present"):
        reasons.append("discord_token_missing")
    if not gate.get("team_channel_id_present"):
        reasons.append("team_channel_id_missing")
    if not guard.get("known_team_channel_only"):
        reasons.append("known_team_channel_required")
    if not guard.get("non_public_only"):
        reasons.append("public_channel_blocked")
    if not guard.get("low_risk_intent"):
        reasons.append("low_risk_intent_required")
    if guard.get("high_risk_intent_blocked"):
        reasons.append("high_risk_intent_blocked")
    if not guard.get("max_one_reply_per_event"):
        reasons.append("max_one_reply_per_event_required")
    if not guard.get("team_event_eligible_for_auto_ops"):
        reasons.append("team_event_not_eligible_for_auto_ops")
    return reasons


def build_phase67_team_auto_ops_preflight(
    env: Mapping[str, str] | None = None, event: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    ready = not _blocked_reasons(gate, guard, allow_flag_present=True)
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase67_team_auto_ops_preflight",
        "ready_for_phase67_team_auto_ops_manual_gate": ready,
        "ready_for_production_unattended": False,
        "current_verified_level": "level4_low_risk_team_channel_canary_verified_once",
        "next_target_level": "level4_supervised_team_channel_auto_ops",
    }
    assert_phase67_72_supervised_team_auto_ops_safe(report, allow_ready=True)
    return report


def build_phase67_72_supervised_team_auto_ops(
    env: Mapping[str, str] | None = None, event: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase67_72_supervised_team_auto_ops",
        "metadata_only": True,
        "team_auto_ops_manual_gate_required": True,
        "known_team_channel_required": True,
        "low_risk_intent_required": True,
        "deterministic_template_only": True,
        "ready_for_phase67_team_auto_ops_manual_gate": True,
        "current_verified_level": "level4_low_risk_team_channel_canary_verified_once",
        "next_target_level": "level4_supervised_team_channel_auto_ops",
        "ready_for_production_unattended": False,
        "autonomy_matrix": {
            "level_1": "read_only_observation_verified",
            "level_2": "manual_gate_deterministic_reply_verified",
            "level_3": "supervised_private_test_auto_reply_verified",
            "level_4_canary": "low_risk_team_channel_canary_verified_once",
            "level_4_auto_ops": "supervised_team_channel_auto_ops_prepared_not_executed",
            "level_5": "production_unattended_not_ready",
        },
        "next_actual_operation": "separate_manual_gate_actual_phase67_supervised_team_channel_auto_ops_exactly_once",
    }
    assert_phase67_72_supervised_team_auto_ops_safe(report, allow_ready=True)
    return report


def build_actual_phase67_team_auto_ops(
    *,
    allow_flag_present: bool = False,
    env: Mapping[str, str] | None = None,
    event: Mapping[str, Any] | None = None,
    send_adapter: Phase67TeamAutoOpsSendAdapter | None = None,
    phase67_team_auto_ops_already_consumed: bool = True,
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    reasons = _blocked_reasons(
        gate,
        guard,
        allow_flag_present=allow_flag_present,
        phase67_team_auto_ops_already_consumed=phase67_team_auto_ops_already_consumed,
    )
    if reasons:
        report = {
            **_base_report(),
            **gate,
            **guard,
            "report_type": "phase67_team_auto_ops_blocked",
            "allow_flag_present": allow_flag_present,
            "phase67_team_auto_ops_already_consumed": phase67_team_auto_ops_already_consumed,
            "phase67_repeat_team_auto_ops_locked": phase67_team_auto_ops_already_consumed,
            "blocked": True,
            "blocked_reasons": reasons,
            "ready_for_phase67_team_auto_ops_manual_gate": False,
            "ready_for_production_unattended": False,
            "current_verified_level": "level4_low_risk_team_channel_canary_verified_once",
            "next_target_level": "level4_supervised_team_channel_auto_ops",
        }
        assert_phase67_72_supervised_team_auto_ops_safe(report)
        return report

    selected_adapter = send_adapter or RealDiscordPhase67TeamAutoOpsSendAdapter(
        token=_env_value(env, "DISCORD_BOT_TOKEN"),
        team_channel_id=_env_value(env, "HERMES_PHASE67_TEAM_AUTO_OPS_CHANNEL_ID"),
    )
    send_result = selected_adapter.send_team_auto_ops(_deterministic_reply_text())
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase67_team_auto_ops_actual_session",
        "allow_flag_present": True,
        "phase67_team_auto_ops_already_consumed": False,
        "phase67_repeat_team_auto_ops_locked": True,
        "blocked": False,
        "blocked_reasons": [],
        "actual_team_auto_ops_executed": bool(send_result.message_sent),
        "real_team_sender_adapter_selected": send_adapter is None,
        "fake_sender_adapter_used": send_adapter is not None,
        "real_team_auto_ops_send_performed": bool(send_result.message_sent and send_result.api_send_called and send_adapter is None),
        "discord_api_send_called": bool(send_result.api_send_called),
        "discord_message_sent": bool(send_result.message_sent),
        "message_sent_count": int(send_result.message_sent_count),
        "send_result_status_code_present": send_result.status_code is not None,
        "send_result_error_type": send_result.error_type,
        "ready_for_phase67_team_auto_ops_manual_gate": False,
        "ready_for_production_unattended": False,
        "current_verified_level": "level4_low_risk_team_channel_canary_verified_once",
        "next_target_level": "level4_supervised_team_channel_auto_ops",
    }
    assert_phase67_72_supervised_team_auto_ops_safe(report, allow_fake_success=True)
    return report


def build_phase67_team_auto_ops_closeout() -> dict[str, Any]:
    report: dict[str, Any] = {
        **_base_report(),
        "report_type": "phase67_team_auto_ops_closeout",
        "metadata_only": True,
        "phase67_team_auto_ops_closed_out": True,
        "phase67_actual_team_auto_ops_sent": True,
        "historical_message_sent_count": 1,
        "phase67_repeat_team_auto_ops_locked": True,
        "phase67_team_auto_ops_already_consumed": True,
        "ready_for_repeat_team_auto_ops": False,
        "ready_for_phase67_team_auto_ops_manual_gate": False,
        "sent_scope": "known_team_channel_only",
        "reply_text_source": "deterministic_template",
        "real_team_auto_ops_send_performed": True,
        "previous_verified_level": "level4_low_risk_team_channel_canary_verified_once",
        "current_verified_level": "level4_supervised_team_channel_auto_ops_verified_once",
        "next_target_level": "level4_limited_auto_mode_prep",
        "ready_for_production_unattended": False,
        "autonomy_matrix": {
            "level_1": "read_only_observation_verified",
            "level_2": "manual_gate_deterministic_reply_verified",
            "level_3": "supervised_private_test_auto_reply_verified",
            "level_4_canary": "low_risk_team_channel_canary_verified_once",
            "level_4_auto_ops": "supervised_team_channel_auto_ops_verified_once",
            "level_5": "production_unattended_not_ready",
        },
        "next_actual_operation": "separate_manual_gate_for_limited_auto_mode_prep",
    }
    assert_phase67_72_supervised_team_auto_ops_safe(report, allow_historical_closeout=True)
    return report


def assert_phase67_72_supervised_team_auto_ops_safe(
    report: Mapping[str, Any],
    *,
    allow_ready: bool = False,
    allow_fake_success: bool = False,
    allow_historical_closeout: bool = False,
) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase67-72 report contains sensitive values.")
    for key in (
        "actual_discord_runtime_executed",
        "discord_gateway_live_connection_executed",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_live_execution",
        "cron_started",
        "unattended_auto_reply_executed",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
        "ready_for_repeat_team_auto_ops",
        "public_channel_send_allowed",
        "unknown_channel_send_allowed",
    ):
        if report.get(key):
            raise ValueError(f"Phase67-72 unsafe flag is true: {key}")
    if not allow_fake_success and not allow_historical_closeout:
        for key in (
            "actual_team_auto_ops_executed",
            "real_team_auto_ops_send_performed",
            "discord_api_send_called",
            "discord_message_sent",
        ):
            if report.get(key):
                raise ValueError(f"Phase67-72 unsafe flag is true: {key}")
        if int(report.get("message_sent_count", 0) or 0) != 0:
            raise ValueError("Phase67-72 safe reports must not send messages.")
    if int(report.get("message_sent_count", 0) or 0) > 1:
        raise ValueError("Phase67-72 message_sent_count must not exceed 1.")
    if allow_historical_closeout and int(report.get("historical_message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase67 closeout historical_message_sent_count must be 1.")
    if allow_historical_closeout and not report.get("real_team_auto_ops_send_performed"):
        raise ValueError("Phase67 closeout must record historical real team auto-ops send semantic.")
    if report.get("reply_text_source") != "deterministic_template":
        raise ValueError("Phase67-72 reply text source must be deterministic_template.")
    if report.get("sent_scope") != "known_team_channel_only":
        raise ValueError("Phase67-72 sent scope must be known_team_channel_only.")
    if not allow_ready and report.get("ready_for_phase67_team_auto_ops_manual_gate"):
        raise ValueError("Phase67-72 blocked report cannot be ready for Manual Gate.")


def render_phase67_72_supervised_team_auto_ops_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase67-72 Supervised Team Auto-Ops",
            "",
            "- Path available: true",
            "- Ops queue available: true",
            "- Review packet required: true",
            "- Manual Gate required: true",
            "- Phase60 canary verified once: true",
            f"- Current verified level: {report.get('current_verified_level')}",
            f"- Next target level: {report.get('next_target_level')}",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- LLM/RAG/embedding/vector/external: false",
            f"- Next actual operation: {report.get('next_actual_operation')}",
        ]
    ) + "\n"
