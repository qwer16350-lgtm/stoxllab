"""Phase 39A actual private-test one-shot send path, default blocked."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Protocol

from actual_private_test_send_blocked_report import build_actual_private_test_send_blocked_report
from actual_private_test_send_safety_gate import build_actual_private_test_send_safety_gate
from final_would_send_payload_freeze import build_final_would_send_payload_freeze


VERSION = "phase39a_actual_private_test_one_shot_send_path_default_blocked_no_execution"
PHASE39B_READY_VERSION = "phase39b_manual_actual_private_test_one_shot_send_ready_gate"
PHASE39B_EXECUTION_GATE_VERSION = "phase39b_actual_private_test_send_execution_gate_mock_no_send"
PHASE39B_REAL_VERSION = "phase39b_manual_actual_private_test_one_shot_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
UNSAFE_RUNTIME_ENV_FLAGS = (
    "HERMES_LLM_DISCORD_SEND_ENABLED",
    "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED",
    "HERMES_DISCORD_RAG_ENABLED",
    "HERMES_LLM_RAG_ENABLED",
    "HERMES_RAG_LLM_REPLY_ENABLED",
    "HERMES_DISCORD_EXTERNAL_EXECUTION",
    "HERMES_DISCORD_LLM_ENABLED",
)


@dataclass
class SendResult:
    api_send_called: bool = False
    message_sent: bool = False
    message_sent_count: int = 0
    status_code: int | None = None
    error_type: str = ""


class DiscordSendAdapter(Protocol):
    def send_message(self, channel_id: str, content: str) -> SendResult:
        """Send a private-test message and return sanitized execution metadata."""


class RealDiscordSendAdapter:
    def __init__(self, token: str) -> None:
        self._token = token

    def send_message(self, channel_id: str, content: str) -> SendResult:
        payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            data=payload,
            headers={
                "Authorization": f"Bot {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "stoxl-hermes-gateway/phase39b",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status_code = int(getattr(response, "status", 0) or 0)
            sent = 200 <= status_code < 300
            return SendResult(api_send_called=True, message_sent=sent, message_sent_count=1 if sent else 0, status_code=status_code)
        except urllib.error.HTTPError as exc:
            return SendResult(api_send_called=True, message_sent=False, message_sent_count=0, status_code=int(exc.code), error_type="http_error")
        except Exception as exc:
            return SendResult(api_send_called=False, message_sent=False, message_sent_count=0, error_type=type(exc).__name__)


class MockDiscordSendAdapter:
    def send_message(self, channel_id: str, content: str) -> SendResult:
        return SendResult()


def _env_flag(env: dict[str, Any], key: str) -> bool:
    return str(env.get(key, "") or "").strip().lower() == "true"


def _env_present(env: dict[str, Any], key: str) -> bool:
    return bool(str(env.get(key, "") or "").strip())


def _unsafe_runtime_flags(env: dict[str, Any]) -> list[str]:
    return [key for key in UNSAFE_RUNTIME_ENV_FLAGS if _env_flag(env, key)]


def _send_content() -> str:
    return str(build_final_would_send_payload_freeze().get("payload_preview", "") or "Review-only private-test payload preview. No external action has been taken.")


def build_actual_private_test_one_shot_send(
    *,
    allow_flag_present: bool = False,
    execute_flag_present: bool = False,
    send_adapter: DiscordSendAdapter | None = None,
    env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_env = env if env is not None else os.environ
    safety_gate = build_actual_private_test_send_safety_gate(allow_flag_present=allow_flag_present, env=source_env)
    blocked_report = build_actual_private_test_send_blocked_report(safety_gate)
    conditions = safety_gate.get("condition_values", {})
    unsafe_flags = _unsafe_runtime_flags(source_env)
    runtime_safety_flags_disabled = not unsafe_flags
    phase39b_ready = bool(allow_flag_present) and bool(safety_gate.get("raw_required_conditions_met")) and runtime_safety_flags_disabled
    phase39b_execution_gate = phase39b_ready and bool(execute_flag_present)
    real_execution_env_enabled = _env_flag(source_env, "HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION")
    real_adapter_selected = phase39b_execution_gate and real_execution_env_enabled
    blocked_reasons = _blocked_reasons(safety_gate)
    if unsafe_flags:
        blocked_reasons.extend(f"unsafe_runtime_flag_enabled:{flag}" for flag in unsafe_flags)
    mode = "phase39a_default_blocked"
    version = VERSION
    adapter = "none"
    send_result = SendResult()
    real_adapter_called = False
    real_adapter_injected_for_test = send_adapter is not None
    if real_adapter_selected:
        mode = "phase39b_actual_send_execution"
        version = PHASE39B_REAL_VERSION
        adapter = "real"
        selected_adapter = send_adapter or RealDiscordSendAdapter(str(source_env.get("DISCORD_BOT_TOKEN", "") or ""))
        real_adapter_called = True
        send_result = selected_adapter.send_message(str(source_env.get("HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "") or ""), _send_content())
    elif phase39b_execution_gate:
        mode = "phase39b_actual_send_execution"
        version = PHASE39B_EXECUTION_GATE_VERSION
        adapter = "mock"
    elif phase39b_ready:
        mode = "phase39b_manual_ready_gate"
        version = PHASE39B_READY_VERSION
    report = {
        "report_type": "actual_private_test_one_shot_send",
        "version": version,
        "actual_send_path_available": True,
        "report_only": not real_adapter_selected,
        "phase39a_implementation_only": not phase39b_ready,
        "phase39b_manual_execution": phase39b_ready,
        "mode": mode,
        "execute_flag_present": bool(execute_flag_present),
        "real_discord_send_execution_env_enabled": real_execution_env_enabled,
        "execution_gate_conditions_met": phase39b_execution_gate,
        "actual_execution_adapter": adapter,
        "phase39b_actual_execution_mode_available": True,
        "real_adapter_selected": real_adapter_selected,
        "real_adapter_called": real_adapter_called,
        "real_adapter_injected_for_test": real_adapter_injected_for_test,
        "actual_private_test_send_executed": bool(send_result.message_sent),
        "actual_send_executed": bool(send_result.message_sent),
        "discord_live_runtime_executed": False,
        "discord_api_send_called": bool(send_result.api_send_called),
        "discord_message_sent": bool(send_result.message_sent),
        "message_sent_count": int(send_result.message_sent_count),
        "send_result_status_code_present": send_result.status_code is not None,
        "send_result_error_type": send_result.error_type,
        "allow_flag_present": bool(allow_flag_present),
        "manual_approval_required": True,
        "manual_approval_actualized": phase39b_ready,
        "approval_phrase_present": _env_present(source_env, "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE"),
        "approval_phrase_exact_match": bool(safety_gate.get("condition_values", {}).get("approval_phrase_exact_match")),
        "approval_phrase_generated": False,
        "approval_phrase_value_logged": False,
        "discord_send_messages_enabled": _env_flag(source_env, "HERMES_DISCORD_SEND_MESSAGES"),
        "private_test_reply_enabled": _env_flag(source_env, "HERMES_DISCORD_PRIVATE_TEST_REPLY"),
        "reply_mode_private_test_only": str(source_env.get("HERMES_DISCORD_REPLY_MODE", "") or "").strip() == "private_test_only",
        "discord_token_present": _env_present(source_env, "DISCORD_BOT_TOKEN"),
        "discord_token_value_logged": False,
        "private_test_channel_id_present": _env_present(source_env, "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"),
        "private_test_channel_id_value_logged": False,
        "source_phase38e_live_send_entry_gate_available": bool(safety_gate.get("condition_values", {}).get("phase38e_gate_available")),
        "payload_frozen": bool(safety_gate.get("condition_values", {}).get("payload_frozen")),
        "rollback_gate_ready": bool(safety_gate.get("condition_values", {}).get("rollback_gate_ready")),
        "operator_checklist_ready": bool(safety_gate.get("condition_values", {}).get("operator_checklist_ready")),
        "send_scope": "private_test_only",
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "unattended_auto_reply_allowed": False,
        "new_llm_api_call_attempted": False,
        "new_llm_api_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "full_content_included": False,
        "ready_for_actual_private_test_send": phase39b_execution_gate,
        "ready_for_discord_send": False,
        "ready_for_phase39b_manual_one_shot_send": phase39b_ready,
        "ready_for_phase39c_send_closeout": bool(send_result.message_sent and int(send_result.message_sent_count) == 1),
        "ready_for_repeat_send": False,
        "ready_for_unattended_auto_reply": False,
        "runtime_safety_flags_disabled": runtime_safety_flags_disabled,
        "unsafe_runtime_flags_enabled": unsafe_flags,
        "blocked": not phase39b_ready,
        "blocked_reasons": [] if phase39b_ready else blocked_reasons,
        "source_safety_gate_available": bool(safety_gate.get("safety_gate_available")),
        "source_blocked_report_available": bool(blocked_report.get("blocked_report_available")),
    }
    assert_actual_private_test_one_shot_send_safe(report)
    return report


def _blocked_reasons(safety_gate: dict[str, Any]) -> list[str]:
    values = safety_gate.get("condition_values", {})
    reasons = []
    if not values.get("allow_flag_present"):
        reasons.append("allow_flag_missing")
    if not values.get("manual_approval_flag_true") or not values.get("approval_phrase_exact_match"):
        reasons.append("manual_approval_not_actualized")
    if not values.get("discord_send_messages_true"):
        reasons.append("discord_send_messages_disabled")
    if not values.get("private_test_reply_true"):
        reasons.append("private_test_reply_disabled")
    if not values.get("reply_mode_private_test_only"):
        reasons.append("reply_mode_not_private_test_only")
    if not values.get("discord_token_present"):
        reasons.append("discord_token_missing")
    if not values.get("private_test_channel_id_present"):
        reasons.append("private_test_channel_id_missing")
    reasons.append("phase39a_no_execution_policy")
    return reasons


def assert_actual_private_test_one_shot_send_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 39A one-shot send report contains sensitive values.")
    readiness_mode = bool(report.get("phase39b_manual_execution"))
    execution_gate_mode = bool(report.get("execution_gate_conditions_met"))
    real_adapter_selected = bool(report.get("real_adapter_selected"))
    injected_real_adapter = bool(report.get("real_adapter_injected_for_test"))
    message_sent = bool(report.get("discord_message_sent"))
    api_send_called = bool(report.get("discord_api_send_called"))
    sent_count = int(report.get("message_sent_count", 0) or 0)
    if not readiness_mode and not report.get("blocked"):
        raise ValueError("Phase 39A one-shot send must be blocked.")
    if readiness_mode and report.get("blocked"):
        raise ValueError("Phase 39B readiness gate must not be blocked.")
    for key in (
        "discord_live_runtime_executed",
        "approval_phrase_generated",
        "approval_phrase_value_logged",
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "public_channel_send_allowed",
        "team_channel_send_allowed",
        "public_channel_reply_allowed",
        "team_channel_reply_allowed",
        "unattended_auto_reply_allowed",
        "new_llm_api_call_attempted",
        "new_llm_api_called",
        "llm_api_call_attempted",
        "llm_api_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "full_content_included",
        "ready_for_discord_send",
        "ready_for_repeat_send",
        "ready_for_unattended_auto_reply",
    ):
        if report.get(key):
            raise ValueError(f"Phase 39A one-shot send unsafe flag is true: {key}")
    if not readiness_mode and report.get("manual_approval_actualized"):
        raise ValueError("Phase 39A default mode must not actualize manual approval.")
    if not readiness_mode and report.get("ready_for_phase39b_manual_one_shot_send"):
        raise ValueError("Phase 39A default mode must not be ready for Phase 39B.")
    if readiness_mode and not report.get("manual_approval_actualized"):
        raise ValueError("Phase 39B readiness mode requires manual approval actualized.")
    if readiness_mode and not report.get("ready_for_phase39b_manual_one_shot_send"):
        raise ValueError("Phase 39B readiness mode must be ready for the manual one-shot send.")
    if not execution_gate_mode and report.get("ready_for_actual_private_test_send"):
        raise ValueError("Actual private-test send readiness requires execution gate mode.")
    if execution_gate_mode and not report.get("ready_for_actual_private_test_send"):
        raise ValueError("Execution gate mode must set ready_for_actual_private_test_send true.")
    if execution_gate_mode and report.get("actual_execution_adapter") not in ("mock", "real"):
        raise ValueError("Execution gate mode must use mock or real adapter.")
    if report.get("actual_execution_adapter") == "real" and not real_adapter_selected:
        raise ValueError("Real adapter label requires real adapter selection.")
    if real_adapter_selected and not report.get("real_discord_send_execution_env_enabled"):
        raise ValueError("Real adapter selection requires the real execution env.")
    if real_adapter_selected and not report.get("real_adapter_called"):
        raise ValueError("Real adapter selection must call the selected adapter.")
    if not real_adapter_selected and report.get("real_adapter_called"):
        raise ValueError("Real adapter must not be called unless selected.")
    if injected_real_adapter and (api_send_called or message_sent or sent_count != 0):
        raise ValueError("Injected test adapter must not report actual Discord send.")
    if not real_adapter_selected and (api_send_called or message_sent or sent_count != 0):
        raise ValueError("Non-real adapter modes must not call Discord or send messages.")
    if not real_adapter_selected and (report.get("actual_private_test_send_executed") or report.get("actual_send_executed")):
        raise ValueError("Non-real adapter modes must not execute actual send.")
    if real_adapter_selected and not injected_real_adapter:
        if message_sent:
            if not api_send_called or sent_count != 1:
                raise ValueError("Real send success must call API and send exactly one message.")
            if not report.get("actual_private_test_send_executed") or not report.get("ready_for_phase39c_send_closeout"):
                raise ValueError("Real send success must prepare Phase 39C closeout.")
        else:
            if sent_count != 0 or report.get("ready_for_phase39c_send_closeout"):
                raise ValueError("Real send failure must not prepare closeout.")
    if not report.get("runtime_safety_flags_disabled") and not report.get("blocked"):
        raise ValueError("Runtime LLM/RAG/external flags must be disabled for unblocked execution.")


def render_actual_private_test_one_shot_send_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Actual Private-test One-shot Send Path",
            "",
            "- Actual send path available: true",
            "- Report only: true",
            "- Phase 39A implementation only: true",
            "- Blocked: true",
            "- Actual private-test send executed: false",
            "- Discord API send called: false",
            "- Discord message sent: false",
            "- Ready for actual private-test send: false",
            "- Ready for Discord send: false",
            "- Ready for Phase 39B manual one-shot send: false",
        ]
    ) + "\n"
