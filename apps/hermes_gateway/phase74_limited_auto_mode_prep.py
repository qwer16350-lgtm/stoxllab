"""Phase74 limited supervised auto mode prep.

This stage prepares the next Manual Gate for a bounded, deterministic,
low-risk team-channel auto mode. CLI reports never open Discord runtime, send
messages, call LLM/RAG, or start scheduler live execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Mapping, Protocol

from manual_gate_helpers import consumed_lock_blocked_reasons, env_int, env_present, env_true


VERSION = "phase74_limited_auto_mode_prep"
APPROVAL_PHRASE = "I_APPROVE_PHASE74_LIMITED_AUTO_MODE"
REPLY_MODE = "limited_team_low_risk_auto_mode_only"
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
BLOCKED_ACTUAL_REASON = "phase74_limited_auto_mode_requires_separate_manual_gate"
CONSUMED_REASON = "phase74_limited_auto_mode_already_consumed"


@dataclass
class Phase74LimitedAutoSessionResult:
    api_send_called: bool = False
    message_sent: bool = False
    message_sent_count: int = 0
    reply_count: int = 0
    session_seconds: int = 0
    cooldown_respected: bool = False
    error_type: str = ""


class Phase74LimitedAutoSessionAdapter(Protocol):
    def run_limited_auto_session(self, content: str, *, max_session_seconds: int) -> Phase74LimitedAutoSessionResult:
        """Run one bounded deterministic limited auto session."""


class RealDiscordPhase74LimitedAutoSessionAdapter:
    def __init__(self, *, token: str, team_channel_id: str) -> None:
        self._token = token
        self._team_channel_id = team_channel_id

    def run_limited_auto_session(self, content: str, *, max_session_seconds: int) -> Phase74LimitedAutoSessionResult:
        if not self._token or not self._team_channel_id:
            return Phase74LimitedAutoSessionResult(error_type="missing_token_or_team_channel")
        payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{self._team_channel_id}/messages",
            data=payload,
            headers={
                "Authorization": f"Bot {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "stoxl-hermes-gateway/phase74",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=min(max_session_seconds, 15)) as response:
                status_code = int(getattr(response, "status", 0) or 0)
            sent = 200 <= status_code < 300
            return Phase74LimitedAutoSessionResult(
                api_send_called=True,
                message_sent=sent,
                message_sent_count=1 if sent else 0,
                reply_count=1 if sent else 0,
                session_seconds=min(max_session_seconds, 15),
                cooldown_respected=True,
            )
        except urllib.error.HTTPError as exc:
            return Phase74LimitedAutoSessionResult(
                api_send_called=True,
                session_seconds=min(max_session_seconds, 15),
                cooldown_respected=True,
                error_type=f"http_error_{int(exc.code)}",
            )
        except Exception as exc:
            return Phase74LimitedAutoSessionResult(error_type=type(exc).__name__)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_value(env: Mapping[str, str] | None, key: str) -> str:
    selected = env if env is not None else os.environ
    return selected.get(key, "")


def _positive_int(env: Mapping[str, str] | None, key: str, default: int) -> int:
    value = env_int(env, key, default)
    if value is None:
        return default
    return value if value > 0 else default


def _gate_snapshot(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    phrase = _env_value(env, "HERMES_PHASE74_LIMITED_AUTO_APPROVAL_PHRASE")
    max_session_seconds = _positive_int(env, "HERMES_PHASE74_LIMITED_AUTO_MAX_SESSION_SECONDS", 60)
    max_send_count = _positive_int(env, "HERMES_PHASE74_LIMITED_AUTO_MAX_SEND_COUNT", 1)
    max_reply_count = _positive_int(env, "HERMES_PHASE74_LIMITED_AUTO_MAX_REPLY_COUNT", 1)
    cooldown_seconds = _positive_int(env, "HERMES_PHASE74_LIMITED_AUTO_COOLDOWN_SECONDS", 30)
    max_session_configured = 0 < max_session_seconds <= 60
    cooldown_configured = cooldown_seconds >= 5
    return {
        "limited_auto_mode_manual_gate_required": True,
        "manual_gate_required": True,
        "manual_approval_true": env_true(env, "HERMES_PHASE74_LIMITED_AUTO_APPROVED"),
        "approval_phrase_present": bool(phrase),
        "approval_phrase_exact_match": phrase == APPROVAL_PHRASE,
        "approval_phrase_value_logged": False,
        "discord_token_present": env_present(env, "DISCORD_BOT_TOKEN"),
        "discord_token_value_logged": False,
        "team_channel_id_present": env_present(env, "HERMES_PHASE74_LIMITED_AUTO_CHANNEL_ID"),
        "team_channel_id_value_logged": False,
        "kill_switch_ready": env_true(env, "HERMES_PHASE74_LIMITED_AUTO_KILL_SWITCH_READY"),
        "kill_switch_required": True,
        "max_session_seconds": max_session_seconds,
        "max_send_count": max_send_count,
        "max_reply_count": max_reply_count,
        "cooldown_seconds": cooldown_seconds,
        "session_bounds_required": True,
        "session_seconds_bounded": max_session_configured,
        "max_send_count_configured": max_send_count == 1,
        "max_reply_count_configured": max_reply_count == 1,
        "cooldown_required": True,
        "cooldown_configured": cooldown_configured,
        "discord_send_enabled": env_true(env, "HERMES_DISCORD_SEND_MESSAGES"),
        "reply_mode_limited_team_low_risk_auto_mode_only": _env_value(env, "HERMES_DISCORD_REPLY_MODE") == REPLY_MODE,
        "llm_disabled": not env_true(env, "HERMES_DISCORD_LLM_ENABLED"),
        "rag_disabled": not env_true(env, "HERMES_DISCORD_RAG_ENABLED"),
        "embedding_disabled": not env_true(env, "HERMES_EMBEDDING_ENABLED"),
        "vector_disabled": not env_true(env, "HERMES_VECTOR_ENABLED"),
        "external_execution_disabled": not env_true(env, "HERMES_DISCORD_EXTERNAL_EXECUTION"),
        "scheduler_live_disabled": not env_true(env, "HERMES_SCHEDULER_LIVE_ENABLED"),
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
        "low_risk_intent_required": True,
        "low_risk_intent": low_risk,
        "high_risk_intent_blocked": high_risk,
        "deterministic_template_only": True,
        "multi_message_blocked": message_count != 1,
        "max_one_reply_per_event": message_count == 1,
        "public_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "unknown_channel_send_allowed": False,
        "unknown_channel_reply_allowed": False,
        "limited_auto_event_eligible": channel_scope == "team" and known_team_channel and low_risk and not high_risk and message_count == 1,
    }


def _policy_capsule() -> dict[str, Any]:
    return {
        "policy_capsule_available": True,
        "allowed_scope": [
            "known_team_channel_only",
            "low_risk_intent_only",
            "deterministic_template_only",
            "review_packet_exists",
            "ops_queue_item_exists",
            "max_session_seconds",
            "max_send_count",
            "max_reply_count",
            "cooldown_seconds",
            "kill_switch_ready",
            "manual_gate_required",
            "human_override_available",
        ],
        "blocked_scope": [
            "public_channel",
            "unknown_channel",
            "high_risk_intent",
            "secret_token_api_key_handling",
            "legal_financial_advice",
            "code_deploy_push",
            "external_command_execution",
            "file_delete_write_outside_allowed_docs",
            "llm_rag_live_reply",
            "scheduler_live",
            "multi_message",
            "unbounded_session",
            "production_unattended",
        ],
    }


def _base_report() -> dict[str, Any]:
    return {
        "version": VERSION,
        "phase74_limited_auto_mode_path_available": True,
        "sent_scope": "known_team_channel_only",
        "reply_text_source": "deterministic_template",
        "ops_queue_required": True,
        "ops_queue_item_exists": True,
        "review_packet_required": True,
        "review_packet_exists": True,
        "review_packet_raw_content_included": False,
        "human_override_available": True,
        "phase67_team_auto_ops_verified_once": True,
        "phase67_repeat_team_auto_ops_locked": True,
        "current_verified_level": "level4_supervised_team_channel_auto_ops_verified_once",
        "next_target_level": "level4_limited_auto_mode_short_run",
        "ready_for_phase74_limited_auto_manual_gate": True,
        "ready_for_repeat_limited_auto_mode": False,
        "phase74_limited_auto_mode_already_consumed": False,
        "phase74_repeat_limited_auto_locked": False,
        "ready_for_production_unattended": False,
        "actual_limited_auto_mode_executed": False,
        "fake_limited_auto_session_executed": False,
        "session_executed": False,
        "actual_discord_runtime_executed": False,
        "discord_gateway_live_connection_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "reply_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "scheduler_live_execution": False,
        "cron_started": False,
        "unattended_production_auto_reply_executed": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "raw_session_ids_logged": False,
        "secret_values_logged": False,
        "approval_phrase_value_logged": False,
        "team_channel_id_value_logged": False,
        "autonomy_level_matrix": {
            "level_1": "read_only_observation_verified",
            "level_2": "manual_deterministic_reply_verified",
            "level_3": "supervised_private_test_auto_reply_verified",
            "level_4_canary": "low_risk_team_channel_canary_verified_once",
            "level_4_auto_ops": "supervised_team_channel_auto_ops_verified_once",
            "level_4_limited_auto": "limited_auto_mode_prepared_not_executed",
            "level_5": "production_unattended_not_ready",
        },
    }


def _deterministic_reply_text() -> str:
    return "Phase74 limited supervised auto mode acknowledgement. Human oversight remains active."


def _blocked_reasons(
    gate: Mapping[str, Any],
    guard: Mapping[str, Any],
    *,
    allow_flag_present: bool,
    force_separate_manual_gate: bool,
    phase74_limited_auto_mode_already_consumed: bool = False,
) -> list[str]:
    reasons = consumed_lock_blocked_reasons(phase74_limited_auto_mode_already_consumed, CONSUMED_REASON)
    if reasons:
        return reasons
    if force_separate_manual_gate:
        reasons.append("manual_gate_missing")
    if not allow_flag_present:
        reasons.append("allow_flag_missing")
    if not gate.get("manual_approval_true"):
        reasons.append("manual_approval_not_approved")
    if not gate.get("approval_phrase_exact_match"):
        reasons.append("approval_phrase_mismatch")
    if not gate.get("discord_token_present"):
        reasons.append("discord_token_missing")
    if not gate.get("team_channel_id_present"):
        reasons.append("team_channel_id_missing")
    if not gate.get("kill_switch_ready"):
        reasons.append("kill_switch_not_ready")
    if not gate.get("discord_send_enabled"):
        reasons.append("discord_send_disabled")
    if not gate.get("reply_mode_limited_team_low_risk_auto_mode_only"):
        reasons.append("reply_mode_not_limited_team_low_risk_auto_mode_only")
    if not (gate.get("session_seconds_bounded") and gate.get("max_send_count_configured") and gate.get("max_reply_count_configured")):
        reasons.append("session_bounds_not_configured")
    if not gate.get("cooldown_configured"):
        reasons.append("cooldown_not_configured")
    if not (gate.get("llm_disabled") and gate.get("rag_disabled") and gate.get("embedding_disabled") and gate.get("vector_disabled")):
        reasons.append("llm_rag_embedding_vector_must_be_disabled")
    if not gate.get("external_execution_disabled"):
        reasons.append("external_execution_enabled")
    if not gate.get("scheduler_live_disabled"):
        reasons.append("scheduler_live_enabled")
    if not guard.get("known_team_channel_only"):
        reasons.append("known_team_channel_required")
    if not guard.get("low_risk_intent"):
        reasons.append("low_risk_intent_required")
    if guard.get("high_risk_intent_blocked"):
        reasons.append("high_risk_intent_blocked")
    if not guard.get("max_one_reply_per_event"):
        reasons.append("max_one_reply_per_event_required")
    if not guard.get("limited_auto_event_eligible"):
        reasons.append("limited_auto_event_not_eligible")
    return reasons


def build_phase74_limited_auto_mode_prep(env: Mapping[str, str] | None = None, event: Mapping[str, Any] | None = None) -> dict[str, Any]:
    report = {
        **_base_report(),
        **_policy_capsule(),
        **_gate_snapshot(env),
        **_event_guard(event),
        "report_type": "phase74_limited_auto_mode_prep",
        "metadata_only": True,
        "next_actual_operation": "separate_manual_gate_actual_phase74_limited_auto_mode_short_run_exactly_once",
    }
    assert_phase74_limited_auto_mode_safe(report, allow_ready=True)
    return report


def build_phase74_limited_auto_mode_preflight(
    env: Mapping[str, str] | None = None,
    event: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    reasons = _blocked_reasons(gate, guard, allow_flag_present=True, force_separate_manual_gate=False)
    report = {
        **_base_report(),
        **_policy_capsule(),
        **gate,
        **guard,
        "report_type": "phase74_limited_auto_mode_preflight",
        "blocked": bool(reasons),
        "blocked_reasons": reasons,
        "ready_for_phase74_limited_auto_manual_gate": True,
        "preflight_passed": not reasons,
        "next_actual_operation": "separate_manual_gate_actual_phase74_limited_auto_mode_short_run_exactly_once",
    }
    assert_phase74_limited_auto_mode_safe(report, allow_ready=True)
    return report


def build_actual_phase74_limited_auto_mode(
    *,
    allow_flag_present: bool = False,
    env: Mapping[str, str] | None = None,
    event: Mapping[str, Any] | None = None,
    session_adapter: Phase74LimitedAutoSessionAdapter | None = None,
    force_separate_manual_gate: bool = False,
    phase74_limited_auto_mode_already_consumed: bool = True,
) -> dict[str, Any]:
    gate = _gate_snapshot(env)
    guard = _event_guard(event)
    reasons = _blocked_reasons(
        gate,
        guard,
        allow_flag_present=allow_flag_present,
        force_separate_manual_gate=force_separate_manual_gate,
        phase74_limited_auto_mode_already_consumed=phase74_limited_auto_mode_already_consumed,
    )
    if reasons:
        consumed = phase74_limited_auto_mode_already_consumed
        report = {
            **_base_report(),
            **_policy_capsule(),
            **gate,
            **guard,
            "report_type": "phase74_limited_auto_mode_blocked",
            "allow_flag_present": allow_flag_present,
            "phase74_limited_auto_mode_already_consumed": consumed,
            "phase74_repeat_limited_auto_locked": consumed,
            "blocked": True,
            "blocked_reasons": reasons,
            "ready_for_phase74_limited_auto_manual_gate": not consumed,
            "current_verified_level": (
                "level4_limited_auto_mode_short_run_verified_once"
                if consumed
                else "level4_supervised_team_channel_auto_ops_verified_once"
            ),
            "next_target_level": (
                "production_hardening_refactor_compaction"
                if consumed
                else "level4_limited_auto_mode_short_run"
            ),
            "limited_auto_mode_short_run_verified_once": consumed,
            "mvp_supervised_discord_agent_os_complete": consumed,
            "production_unattended_ready": False,
            "autonomy_level_matrix": {
                "level_1": "read_only_observation_verified",
                "level_2": "manual_deterministic_reply_verified",
                "level_3": "supervised_private_test_auto_reply_verified",
                "level_4_canary": "low_risk_team_channel_canary_verified_once",
                "level_4_auto_ops": "supervised_team_channel_auto_ops_verified_once",
                "level_4_limited_auto": (
                    "limited_auto_mode_short_run_verified_once"
                    if consumed
                    else "limited_auto_mode_prepared_not_executed"
                ),
                "level_5": "production_unattended_not_ready",
            },
            "next_actual_operation": (
                "production_hardening_refactor_compaction"
                if consumed
                else "separate_manual_gate_actual_phase74_limited_auto_mode_short_run_exactly_once"
            ),
        }
        assert_phase74_limited_auto_mode_safe(report, allow_ready=True)
        return report

    selected_adapter = session_adapter or RealDiscordPhase74LimitedAutoSessionAdapter(
        token=_env_value(env, "DISCORD_BOT_TOKEN"),
        team_channel_id=_env_value(env, "HERMES_PHASE74_LIMITED_AUTO_CHANNEL_ID"),
    )

    result = selected_adapter.run_limited_auto_session(
        _deterministic_reply_text(),
        max_session_seconds=int(gate.get("max_session_seconds", 60) or 60),
    )
    report = {
        **_base_report(),
        **_policy_capsule(),
        **gate,
        **guard,
        "report_type": "phase74_limited_auto_mode_actual_session",
        "allow_flag_present": allow_flag_present,
        "phase74_limited_auto_mode_already_consumed": False,
        "phase74_repeat_limited_auto_locked": True,
        "blocked": False,
        "blocked_reasons": [],
        "fake_limited_auto_session_executed": session_adapter is not None,
        "real_limited_auto_session_adapter_selected": session_adapter is None,
        "actual_limited_auto_mode_executed": bool(result.message_sent),
        "session_executed": bool(result.message_sent),
        "discord_api_send_called": bool(result.api_send_called),
        "discord_message_sent": bool(result.message_sent),
        "message_sent_count": int(result.message_sent_count),
        "reply_count": int(result.reply_count),
        "session_seconds_bounded": int(result.session_seconds) <= int(gate.get("max_session_seconds", 60) or 60),
        "cooldown_respected": bool(result.cooldown_respected),
        "ready_for_repeat_limited_auto_mode": False,
        "send_result_error_type": result.error_type,
        "next_actual_operation": "separate_manual_gate_actual_phase74_limited_auto_mode_short_run_exactly_once",
    }
    assert_phase74_limited_auto_mode_safe(report, allow_fake_success=True, allow_ready=True)
    return report


def build_phase74_limited_auto_closeout() -> dict[str, Any]:
    report = {
        **_base_report(),
        **_policy_capsule(),
        "report_type": "phase74_limited_auto_mode_closeout",
        "metadata_only": True,
        "phase74_limited_auto_mode_closed_out": True,
        "phase74_actual_limited_auto_sent": True,
        "historical_message_sent_count": 1,
        "historical_reply_count": 1,
        "phase74_limited_auto_mode_already_consumed": True,
        "phase74_repeat_limited_auto_locked": True,
        "ready_for_repeat_limited_auto_mode": False,
        "ready_for_phase74_limited_auto_manual_gate": False,
        "sent_scope": "known_team_channel_only",
        "reply_text_source": "deterministic_template",
        "limited_auto_mode_short_run_verified_once": True,
        "previous_verified_level": "level4_supervised_team_channel_auto_ops_verified_once",
        "current_verified_level": "level4_limited_auto_mode_short_run_verified_once",
        "next_target_level": "production_hardening_refactor_compaction",
        "mvp_supervised_discord_agent_os_complete": True,
        "production_unattended_ready": False,
        "autonomy_level_matrix": {
            "level_1": "read_only_observation_verified",
            "level_2": "manual_deterministic_reply_verified",
            "level_3": "supervised_private_test_auto_reply_verified",
            "level_4_canary": "low_risk_team_channel_canary_verified_once",
            "level_4_auto_ops": "supervised_team_channel_auto_ops_verified_once",
            "level_4_limited_auto": "limited_auto_mode_short_run_verified_once",
            "level_5": "production_unattended_not_ready",
        },
        "next_actual_operation": "production_hardening_refactor_compaction",
    }
    assert_phase74_limited_auto_mode_safe(report, allow_historical_closeout=True)
    return report


def build_hermes_mvp_final_closeout() -> dict[str, Any]:
    report = build_phase74_limited_auto_closeout()
    report["report_type"] = "hermes_mvp_final_closeout"
    assert_phase74_limited_auto_mode_safe(report, allow_historical_closeout=True)
    return report


def assert_phase74_limited_auto_mode_safe(
    report: Mapping[str, Any],
    *,
    allow_ready: bool = False,
    allow_fake_success: bool = False,
    allow_historical_closeout: bool = False,
) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase74 report contains sensitive values.")
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
        "unattended_production_auto_reply_executed",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "raw_session_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
        "discord_token_value_logged",
        "ready_for_repeat_limited_auto_mode",
        "public_channel_send_allowed",
        "public_channel_reply_allowed",
        "unknown_channel_send_allowed",
        "unknown_channel_reply_allowed",
    ):
        if report.get(key):
            raise ValueError(f"Phase74 unsafe flag is true: {key}")
    if not allow_fake_success:
        for key in (
            "actual_limited_auto_mode_executed",
            "fake_limited_auto_session_executed",
            "session_executed",
            "discord_api_send_called",
            "discord_message_sent",
        ):
            if report.get(key):
                raise ValueError(f"Phase74 unsafe flag is true: {key}")
        if int(report.get("message_sent_count", 0) or 0) != 0:
            raise ValueError("Phase74 CLI reports must not send messages.")
    if allow_historical_closeout:
        if int(report.get("historical_message_sent_count", 0) or 0) != 1:
            raise ValueError("Phase74 closeout historical_message_sent_count must be 1.")
        if int(report.get("historical_reply_count", 0) or 0) != 1:
            raise ValueError("Phase74 closeout historical_reply_count must be 1.")
        if not report.get("phase74_repeat_limited_auto_locked"):
            raise ValueError("Phase74 closeout must lock repeat limited auto mode.")
        if not report.get("mvp_supervised_discord_agent_os_complete"):
            raise ValueError("Phase74 closeout must mark supervised MVP complete.")
    if int(report.get("message_sent_count", 0) or 0) > 1:
        raise ValueError("Phase74 message_sent_count must not exceed 1.")
    if int(report.get("reply_count", 0) or 0) > 1:
        raise ValueError("Phase74 reply_count must not exceed 1.")
    if report.get("reply_text_source") != "deterministic_template":
        raise ValueError("Phase74 reply text source must be deterministic_template.")
    if report.get("sent_scope") != "known_team_channel_only":
        raise ValueError("Phase74 sent scope must be known_team_channel_only.")
    if not report.get("phase67_team_auto_ops_verified_once"):
        raise ValueError("Phase67 verified-once lock must be preserved.")
    if not report.get("phase67_repeat_team_auto_ops_locked"):
        raise ValueError("Phase67 repeat team auto-ops lock must be preserved.")
    if report.get("ready_for_production_unattended"):
        raise ValueError("Phase74 must not be production unattended ready.")
    if not allow_ready and report.get("ready_for_phase74_limited_auto_manual_gate"):
        raise ValueError("Phase74 blocked report cannot be ready for Manual Gate.")


def render_phase74_limited_auto_mode_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase74 Limited Auto Mode Prep",
            "",
            "- Path available: true",
            "- Policy capsule available: true",
            "- Manual Gate required: true",
            "- Known team channel only: true",
            "- Low-risk intent only: true",
            "- Deterministic template only: true",
            f"- Current verified level: {report.get('current_verified_level')}",
            f"- Next target level: {report.get('next_target_level')}",
            "- Production unattended ready: false",
            "- Discord runtime/send: false",
            "- LLM/RAG/embedding/vector/external/scheduler: false",
        ]
    ) + "\n"
