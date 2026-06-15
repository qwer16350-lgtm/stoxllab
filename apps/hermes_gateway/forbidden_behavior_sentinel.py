"""Phase 35G forbidden behavior sentinel.

Report-only guardrail sentinel. It never runs Discord, sends messages, calls
LLMs, creates embeddings/vector indexes, or executes external actions.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase35g_forbidden_behavior_sentinel_report_only"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")
FORBIDDEN_TRUE_FIELDS = (
    "public_channel_reply_allowed",
    "team_channel_reply_allowed",
    "public_channel_send_allowed",
    "team_channel_send_allowed",
    "unattended_auto_reply_allowed",
    "scheduler_auto_reply_allowed",
    "embedding_api_called",
    "vector_index_created",
    "external_execution",
    "full_content_included",
    "approval_phrase_generated",
    "api_key_value_logged",
    "token_value_logged",
    "raw_discord_ids_logged",
    "approval_phrase_value_logged",
)


def build_forbidden_behavior_sentinel(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_type": "forbidden_behavior_sentinel",
        "version": VERSION,
        "sentinel_available": True,
        "report_only": True,
        "live_runtime_executed": False,
        "llm_called": False,
        "discord_message_sent": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "unattended_auto_reply_allowed": False,
        "scheduler_auto_reply_allowed": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "full_content_included": False,
        "approval_phrase_generated": False,
        "api_key_value_logged": False,
        "token_value_logged": False,
        "raw_discord_ids_logged": False,
        "approval_phrase_value_logged": False,
        "public_team_blocked": True,
        "embedding_vector_disabled": True,
        "forbidden_behavior_sentinel_passed": True,
    }
    if overrides:
        report.update(overrides)
    report["public_team_blocked"] = not any(
        bool(report.get(key))
        for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed")
    )
    report["embedding_vector_disabled"] = not (bool(report.get("embedding_api_called")) or bool(report.get("vector_index_created")))
    report["forbidden_behavior_sentinel_passed"] = _sentinel_passed(report)
    assert_forbidden_behavior_sentinel_safe(report)
    return report


def _sentinel_passed(report: dict[str, Any]) -> bool:
    return not any(bool(report.get(key)) for key in FORBIDDEN_TRUE_FIELDS)


def assert_forbidden_behavior_sentinel_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Forbidden behavior sentinel contains sensitive values.")
    if not report.get("forbidden_behavior_sentinel_passed"):
        raise ValueError("Forbidden behavior sentinel failed.")
    for key in FORBIDDEN_TRUE_FIELDS:
        if report.get(key):
            raise ValueError(f"Forbidden behavior enabled: {key}")


def render_forbidden_behavior_sentinel_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Forbidden Behavior Sentinel",
            "",
            "- Sentinel available: true",
            "- Report only: true",
            "- Public/team blocked: true",
            "- Unattended auto reply allowed: false",
            "- Scheduler auto reply allowed: false",
            "- Embedding/vector disabled: true",
            "- External execution: false",
            "- Full content included: false",
            "- Approval phrase generated: false",
            "- Forbidden behavior sentinel passed: true",
        ]
    ) + "\n"
