"""Phase60-65 low-risk team canary autonomy stage.

This module prepares the team-channel canary path and verifies it with fake
senders only in tests. Real Discord runtime/send remains reserved for a later
Manual Gate.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Mapping, Protocol

from manual_gate_helpers import consumed_lock_blocked_reasons


VERSION = "phase60_65_team_canary_autonomy_stage_report_only"
APPROVAL_PHRASE = "I_APPROVE_PHASE60_TEAM_CANARY"
REPLY_MODE = "known_team_low_risk_canary_only"
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
class Phase60TeamCanarySendResult:
    api_send_called: bool = False
    message_sent: bool = False
    message_sent_count: int = 0
    status_code: int | None = None
    error_type: str = ""


class Phase60TeamCanarySendAdapter(Protocol):
    def send_team_canary(self, content: str) -> Phase60TeamCanarySendResult:
        """Send a deterministic low-risk team canary reply."""


class RealDiscordPhase60TeamCanarySendAdapter:
    def __init__(self, *, token: str, team_channel_id: str) -> None:
        self._token = token
        self._team_channel_id = team_channel_id

    def send_team_canary(self, content: str) -> Phase60TeamCanarySendResult:
        if not self._token or not self._team_channel_id:
            return Phase60TeamCanarySendResult(error_type="missing_token_or_team_channel")
        payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{self._team_channel_id}/messages",
            data=payload,
            headers={
                "Authorization": f"Bot {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "stoxl-hermes-gateway/phase60",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status_code = int(getattr(response, "status", 0) or 0)
            sent = 200 <= status_code < 300
            return Phase60TeamCanarySendResult(
                api_send_called=True,
                message_sent=sent,
                message_sent_count=1 if sent else 0,
                status_code=status_code,
            )
        except urllib.error.HTTPError as exc:
            return Phase60TeamCanarySendResult(api_send_called=True, status_code=int(exc.code), error_type="http_error")
        except Exception as exc:
            return Phase60TeamCanarySendResult(error_type=type(exc).__name__)


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
    phrase = _env_value(env, "HERMES_PHASE60_TEAM_CANARY_APPROVAL_PHRASE")
    max_send_count = _positive_int(env, "HERMES_PHASE60_TEAM_CANARY_MAX_SEND_COUNT", 1)
    max_reply_count = _positive_int(env, "HERMES_PHASE60_TEAM_CANARY_MAX_REPLY_COUNT", 1)
    cooldown_seconds = _positive_int(env, "HERMES_PHASE60_TEAM_CANARY_COOLDOWN_SECONDS", 30)
    return {
        "manual_gate_required": True,
        "team_canary_manual_gate_required": True,
        "manual_approval_true": _truthy(_env_value(env, "HERMES_PHASE60_TEAM_CANARY_APPROVED")),
        "approval_phrase_present": bool(phrase),
        "approval_phrase_exact_match": phrase == APPROVAL_PHRASE,
        "approval_phrase_value_logged": False,
        "discord_send_enabled": _truthy(_env_value(env, "HERMES_DISCORD_SEND_MESSAGES")),
        "reply_mode_known_team_low_risk_canary_only": _env_value(env, "HERMES_DISCORD_REPLY_MODE") == REPLY_MODE,
        "kill_switch_ready": _truthy(_env_value(env, "HERMES_PHASE60_TEAM_CANARY_KILL_SWITCH_READY")),
        "max_send_count": max_send_count,
        "max_reply_count": max_reply_count,
        "cooldown_seconds": cooldown_seconds,
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
        "team_canary_channel_id_present": bool(_env_value(env, "HERMES_PHASE60_TEAM_CANARY_CHANNEL_ID").strip()),
        "team_canary_channel_id_value_logged": False,
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
        "known_team_channel_only": known_team_channel and channel_scope == "team",
        "non_public_only": channel_scope != "public",
        "low_risk_intent_required": True,
        "low_risk_intent": low_risk,
        "high_risk_intent_blocked": high_risk,
        "deterministic_template_only": True,
        "max_one_reply_per_event": message_count == 1,
        "human_override_available": True,
        "public_channel_send_allowed": False,
        "unknown_channel_send_allowed": False,
        "team_channel_event_eligible": channel_scope == "team" and known_team_channel and low_risk and not high_risk and message_count == 1,
    }


def _base_report() -> dict[str, Any]:
    return {
        "version": VERSION,
        "phase60_low_risk_team_canary_path_available": True,
        "actual_path_available": True,
        "runtime_scope": "known_team_channel_only",
        "sent_scope": "known_team_channel_only",
        "reply_text_source": "deterministic_template",
        "team_channel_auto_ops_executed": False,
        "actual_team_canary_executed": False,
        "real_team_discord_send_performed": False,
        "real_team_sender_adapter_selected": False,
        "fake_sender_adapter_used": False,
        "team_channel_discord_send_called": False,
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
        "capture_file_path_value_logged": False,
        "capture_file_raw_dumped": False,
        "ready_for_repeat_team_canary": False,
    }


def _deterministic_reply_text() -> str:
    return "Phase60 team canary acknowledgement. Low-risk team-channel scope remains supervised."


def _blocked_reasons(
    gate: Mapping[str, Any],
    guard: Mapping[str, Any],
    *,
    allow_flag_present: bool,
    phase60_team_canary_already_consumed: bool = False,
) -> list[str]:
    reasons = consumed_lock_blocked_reasons(
        phase60_team_canary_already_consumed,
        "phase60_team_canary_already_consumed",
    )
    if reasons:
        return reasons
    if not allow_flag_present:
        reasons.append("allow_flag_missing")
    if not gate.get("manual_approval_true"):
        reasons.append("manual_approval_not_approved")
    if not gate.get("approval_phrase_exact_match"):
        reasons.append("approval_phrase_mismatch")
    if not gate.get("discord_send_enabled"):
        reasons.append("discord_send_disabled")
    if not gate.get("reply_mode_known_team_low_risk_canary_only"):
        reasons.append("reply_mode_not_known_team_low_risk_canary_only")
    if not gate.get("kill_switch_ready"):
        reasons.append("kill_switch_not_ready")
    if not (gate.get("max_send_count_configured") and gate.get("max_reply_count_configured") and gate.get("cooldown_configured")):
        reasons.append("team_canary_count_or_cooldown_guard_not_configured")
    if not (gate.get("llm_disabled") and gate.get("rag_disabled") and gate.get("embedding_disabled") and gate.get("vector_disabled")):
        reasons.append("llm_rag_embedding_vector_must_be_disabled")
    if not gate.get("external_execution_disabled"):
        reasons.append("external_execution_enabled")
    if not gate.get("discord_token_present"):
        reasons.append("discord_token_missing")
    if not gate.get("team_canary_channel_id_present"):
        reasons.append("team_canary_channel_id_missing")
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
    if not guard.get("team_channel_event_eligible"):
        reasons.append("team_channel_event_not_eligible")
    return reasons


def build_phase60_team_canary_preflight(
    env: Mapping[str, str] | None = None, event: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    ready = not _blocked_reasons(gate, guard, allow_flag_present=True)
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase60_team_canary_preflight",
        "ready_for_phase60_team_canary_manual_gate": ready,
    }
    assert_phase60_65_team_canary_safe(report, allow_ready=True)
    return report


def build_phase60_team_canary_blocked_report(
    *, allow_flag_present: bool = False, env: Mapping[str, str] | None = None, event: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase60_team_canary_blocked",
        "allow_flag_present": allow_flag_present,
        "blocked": True,
        "blocked_reasons": _blocked_reasons(gate, guard, allow_flag_present=allow_flag_present),
        "ready_for_phase60_team_canary_manual_gate": False,
    }
    assert_phase60_65_team_canary_safe(report)
    return report


def build_actual_phase60_team_canary(
    *,
    allow_flag_present: bool = False,
    env: Mapping[str, str] | None = None,
    event: Mapping[str, Any] | None = None,
    send_adapter: Phase60TeamCanarySendAdapter | None = None,
    phase60_team_canary_already_consumed: bool = True,
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    reasons = _blocked_reasons(
        gate,
        guard,
        allow_flag_present=allow_flag_present,
        phase60_team_canary_already_consumed=phase60_team_canary_already_consumed,
    )
    if reasons:
        report = {
            **_base_report(),
            **gate,
            **guard,
            "report_type": "phase60_team_canary_blocked",
            "allow_flag_present": allow_flag_present,
            "phase60_team_canary_already_consumed": phase60_team_canary_already_consumed,
            "phase60_repeat_team_canary_locked": phase60_team_canary_already_consumed,
            "blocked": True,
            "blocked_reasons": reasons,
            "ready_for_phase60_team_canary_manual_gate": False,
        }
        assert_phase60_65_team_canary_safe(report)
        return report

    selected_adapter = send_adapter or RealDiscordPhase60TeamCanarySendAdapter(
        token=_env_value(env, "DISCORD_BOT_TOKEN"),
        team_channel_id=_env_value(env, "HERMES_PHASE60_TEAM_CANARY_CHANNEL_ID"),
    )
    send_result = selected_adapter.send_team_canary(_deterministic_reply_text())
    report = {
        **_base_report(),
        **gate,
        **guard,
        "report_type": "phase60_team_canary_actual_session",
        "allow_flag_present": True,
        "phase60_team_canary_already_consumed": False,
        "phase60_repeat_team_canary_locked": True,
        "blocked": False,
        "blocked_reasons": [],
        "actual_team_canary_executed": bool(send_result.message_sent),
        "real_team_sender_adapter_selected": send_adapter is None,
        "fake_sender_adapter_used": send_adapter is not None,
        "team_channel_auto_ops_executed": bool(send_result.message_sent),
        "real_team_discord_send_performed": bool(send_result.message_sent and send_result.api_send_called and send_adapter is None),
        "team_channel_discord_send_called": bool(send_result.api_send_called),
        "discord_api_send_called": bool(send_result.api_send_called),
        "discord_message_sent": bool(send_result.message_sent),
        "message_sent_count": int(send_result.message_sent_count),
        "send_result_status_code_present": send_result.status_code is not None,
        "send_result_error_type": send_result.error_type,
        "ready_for_phase60_team_canary_manual_gate": False,
    }
    assert_phase60_65_team_canary_safe(report, allow_fake_success=True)
    return report


def build_phase60_team_canary_closeout() -> dict[str, Any]:
    report: dict[str, Any] = {
        **_base_report(),
        "report_type": "phase60_team_canary_closeout",
        "metadata_only": True,
        "phase60_team_canary_closed_out": True,
        "phase60_actual_team_canary_sent": True,
        "historical_message_sent_count": 1,
        "phase60_repeat_team_canary_locked": True,
        "phase60_team_canary_already_consumed": True,
        "ready_for_repeat_team_canary": False,
        "ready_for_phase60_team_canary_manual_gate": False,
        "sent_scope": "known_team_channel_only",
        "reply_text_source": "deterministic_template",
        "real_team_discord_send_performed": True,
        "current_verified_level": "level4_low_risk_team_channel_canary_verified_once",
        "previous_verified_level": "level3_supervised_private_test_auto_reply_verified",
        "next_target_level": "level4_supervised_team_channel_auto_ops",
        "ready_for_production_unattended": False,
        "phase61_scheduler_gate_available": True,
        "scheduler_dry_run_control_available": True,
        "ready_for_scheduler_manual_gate": False,
        "phase62_65_autonomy_matrix_updated": True,
        "autonomy_matrix": {
            "level_1": "read_only_observation_verified",
            "level_2": "manual_gate_deterministic_reply_verified",
            "level_3": "supervised_private_test_auto_reply_verified",
            "level_4": "low_risk_team_channel_canary_verified_once_partial",
            "level_5": "production_unattended_not_ready",
        },
        "next_actual_operation": "separate_manual_gate_for_supervised_team_channel_auto_ops",
    }
    assert_phase60_65_team_canary_safe(report, allow_historical_closeout=True)
    return report


def build_phase60_65_team_canary_autonomy_stage() -> dict[str, Any]:
    report: dict[str, Any] = {
        **_base_report(),
        "report_type": "phase60_65_team_canary_autonomy_stage",
        "metadata_only": True,
        "large_lean_bundle": True,
        "phase60_low_risk_team_canary_path_available": True,
        "team_canary_manual_gate_required": True,
        "known_team_channel_required": True,
        "low_risk_intent_required": True,
        "deterministic_template_only": True,
        "ready_for_phase60_team_canary_manual_gate": True,
        "phase61_scheduler_gate_available": True,
        "scheduler_dry_run_control_available": True,
        "scheduler_preview_tasks_allowed": [
            "daily_summary_preview",
            "read_only_digest_preview",
            "review_packet_queue_summary",
            "manual_gate_reminder_preview",
        ],
        "scheduler_live_tasks_blocked": [
            "auto_send",
            "auto_reply",
            "live_cron_start",
            "external_execution",
            "llm_call_without_manual_gate",
            "rag_call_without_manual_gate",
        ],
        "ready_for_scheduler_manual_gate": False,
        "phase62_65_autonomy_matrix_updated": True,
        "autonomy_matrix": {
            "level_1": "read_only_observation_verified",
            "level_2": "manual_gate_deterministic_reply_verified",
            "level_3": "supervised_private_test_auto_reply_verified",
            "level_4": "low_risk_team_channel_canary_path_ready_not_executed",
            "level_5": "production_unattended_not_ready",
        },
        "release_blockers": [
            "team_canary_not_executed",
            "scheduler_live_not_approved",
            "rag_llm_live_team_reply_not_approved",
            "production_kill_switch_not_live_tested",
            "git_index_lock_unresolved",
            "refactor_compaction_pending",
        ],
        "current_verified_level": "level3_supervised_private_test_auto_reply_verified",
        "next_target_level": "level4_low_risk_team_channel_canary",
        "ready_for_production_unattended": False,
        "next_actual_operation": "separate_manual_gate_actual_phase60_low_risk_team_channel_canary_exactly_once",
    }
    assert_phase60_65_team_canary_safe(report, allow_ready=True)
    return report


def assert_phase60_65_team_canary_safe(
    report: Mapping[str, Any],
    *,
    allow_ready: bool = False,
    allow_fake_success: bool = False,
    allow_historical_closeout: bool = False,
) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase60-65 report contains sensitive values.")
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
        "capture_file_path_value_logged",
        "capture_file_raw_dumped",
        "ready_for_repeat_team_canary",
        "public_channel_send_allowed",
        "unknown_channel_send_allowed",
    ):
        if report.get(key):
            raise ValueError(f"Phase60-65 unsafe flag is true: {key}")
    if not allow_fake_success and not allow_historical_closeout:
        for key in (
            "actual_team_canary_executed",
            "real_team_discord_send_performed",
            "team_channel_auto_ops_executed",
            "team_channel_discord_send_called",
            "discord_api_send_called",
            "discord_message_sent",
        ):
            if report.get(key):
                raise ValueError(f"Phase60-65 unsafe flag is true: {key}")
        if int(report.get("message_sent_count", 0) or 0) != 0:
            raise ValueError("Phase60-65 safe reports must not send messages.")
    if int(report.get("message_sent_count", 0) or 0) > 1:
        raise ValueError("Phase60-65 message_sent_count must not exceed 1.")
    if allow_historical_closeout and int(report.get("historical_message_sent_count", 0) or 0) != 1:
        raise ValueError("Phase60 closeout historical_message_sent_count must be 1.")
    if allow_historical_closeout and not report.get("real_team_discord_send_performed"):
        raise ValueError("Phase60 closeout must record historical real team send semantic.")
    if report.get("reply_text_source") != "deterministic_template":
        raise ValueError("Phase60-65 reply text source must be deterministic_template.")
    if report.get("sent_scope") != "known_team_channel_only":
        raise ValueError("Phase60-65 sent scope must be known_team_channel_only.")
    if not allow_ready and report.get("ready_for_phase60_team_canary_manual_gate"):
        raise ValueError("Phase60-65 blocked report cannot be ready for team canary gate.")


def render_phase60_65_team_canary_autonomy_stage_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase60-65 Team Canary Autonomy Stage",
            "",
            "- Phase60 low-risk team canary path available: true",
            "- Team canary manual gate required: true",
            "- Ready for Phase60 team canary Manual Gate: true",
            "- Phase61 scheduler dry-run control available: true",
            "- Phase62/65 autonomy matrix updated: true",
            f"- Current verified level: {report.get('current_verified_level', 'level3_supervised_private_test_auto_reply_verified')}",
            f"- Next target level: {report.get('next_target_level', 'level4_low_risk_team_channel_canary')}",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- LLM/RAG/embedding/vector/external: false",
            f"- Next actual operation: {report.get('next_actual_operation')}",
        ]
    ) + "\n"
