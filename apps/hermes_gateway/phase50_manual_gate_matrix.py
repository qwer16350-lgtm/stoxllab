"""Phase50 manual gate matrix."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase50_manual_gate_matrix_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")

GATE_NAMES = [
    "Read-only live runtime gate",
    "RAG/LLM no-send one-shot gate",
    "Private-test supervised auto reply gate",
    "Team-channel low-risk canary gate",
    "Production unattended limited launch gate",
    "Emergency kill-switch verification gate",
]

BASE_REQUIREMENTS = [
    "approval phrase required",
    "cost/count guard required when LLM involved",
    "channel allowlist required when Discord send involved",
    "rate limit required",
    "cooldown required",
    "no-repeat or bounded-repeat lock required",
    "secret/raw log forbidden",
]


def build_phase50_manual_gate_matrix() -> dict[str, Any]:
    gates = [
        {
            "gate_name": name,
            "approval_phrase_required": True,
            "cost_count_guard_required_when_llm_involved": True,
            "channel_allowlist_required_when_discord_send_involved": True,
            "rate_limit_required": True,
            "cooldown_required": True,
            "no_repeat_or_bounded_repeat_lock_required": True,
            "secret_raw_log_forbidden": True,
            "execution_available_now": False,
        }
        for name in GATE_NAMES
    ]
    report = {
        "report_type": "phase50_manual_gate_matrix",
        "version": VERSION,
        "manual_gate_matrix_available": True,
        "gate_count": len(gates),
        "gates": gates,
        "base_requirements": list(BASE_REQUIREMENTS),
        "manual_gate_execution_available_now": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "scheduler_cron_live_execution": False,
        "external_execution": False,
    }
    assert_phase50_manual_gate_matrix_safe(report)
    return report


def assert_phase50_manual_gate_matrix_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    lowered = text.lower()
    if SECRET_RE.search(lowered) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase50 manual gate matrix contains sensitive values.")
    if report.get("gate_count") != 6:
        raise ValueError("Phase50 manual gate matrix requires six gate types.")
    for gate in report.get("gates", []):
        for key in (
            "approval_phrase_required",
            "cost_count_guard_required_when_llm_involved",
            "channel_allowlist_required_when_discord_send_involved",
            "rate_limit_required",
            "cooldown_required",
            "no_repeat_or_bounded_repeat_lock_required",
            "secret_raw_log_forbidden",
        ):
            if not gate.get(key):
                raise ValueError(f"Phase50 manual gate missing requirement: {key}")
        if gate.get("execution_available_now"):
            raise ValueError("Phase50 manual gate execution is not available now.")
    for key in ("manual_gate_execution_available_now", "llm_api_call_attempted", "llm_api_called", "discord_api_send_called", "discord_message_sent", "scheduler_cron_live_execution", "external_execution"):
        if report.get(key):
            raise ValueError(f"Phase50 manual gate matrix unsafe flag is true: {key}")


def render_phase50_manual_gate_matrix_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase50 Manual Gate Matrix",
            "",
            "- Manual gate count: 6",
            "- Approval phrase required: true",
            "- Rate limit required: true",
            "- Cooldown required: true",
            "- Secret/raw log forbidden: true",
            "- Manual gate execution available now: false",
        ]
    ) + "\n"
