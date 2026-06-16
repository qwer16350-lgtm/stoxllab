"""Phase 40T-3 sanitized preflight snapshot.

The snapshot preserves only booleans from the read-only runtime preflight so
later execute closeouts can stay consistent without carrying token, channel id,
approval phrase, or other secret values.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase40t_readonly_preflight_snapshot"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def build_phase40t_readonly_preflight_snapshot(preflight: Mapping[str, Any]) -> dict[str, Any]:
    snapshot = {
        "snapshot_type": "phase40t_readonly_preflight_snapshot",
        "version": VERSION,
        "preflight_passed": bool(preflight.get("preflight_passed")),
        "discord_token_present": bool(preflight.get("discord_token_present")),
        "private_test_channel_id_present": bool(preflight.get("private_test_channel_id_present")),
        "approval_actualized": bool(preflight.get("approval_actualized")),
        "approval_phrase_present": bool(preflight.get("approval_phrase_present")),
        "approval_phrase_exact_match": bool(preflight.get("approval_phrase_exact_match")),
        "send_messages_enabled": bool(preflight.get("send_messages_enabled")),
        "private_test_reply_enabled": bool(preflight.get("private_test_reply_enabled")),
        "reply_mode_readonly_private_test_only": bool(preflight.get("reply_mode_readonly_private_test_only")),
        "llm_disabled": not (bool(preflight.get("llm_called")) or bool(preflight.get("llm_api_call_attempted")) or bool(preflight.get("llm_api_called"))),
        "rag_disabled": not bool(preflight.get("rag_called")),
        "embedding_disabled": not (bool(preflight.get("embedding_api_called")) or bool(preflight.get("vector_index_created"))),
        "external_execution": bool(preflight.get("external_execution")),
        "discord_token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "approval_phrase_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "raw_content_logged": False,
        "secret_values_logged": False,
    }
    assert_phase40t_readonly_preflight_snapshot_safe(snapshot)
    return snapshot


def snapshot_has_login_prerequisites(snapshot: Mapping[str, Any] | None) -> bool:
    if not snapshot:
        return False
    return bool(snapshot.get("discord_token_present")) and bool(snapshot.get("private_test_channel_id_present"))


def add_phase40t_snapshot_consistency_fields(report: dict[str, Any], snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    if not snapshot:
        report.update(
            {
                "preflight_snapshot_preserved": False,
                "presence_consistency_verified": False,
                "login_attempt_requires_token_and_channel": True,
            }
        )
        return report
    report.update(
        {
            "preflight_snapshot_preserved": True,
            "presence_consistency_verified": (
                bool(report.get("discord_token_present")) == bool(snapshot.get("discord_token_present"))
                and bool(report.get("private_test_channel_id_present")) == bool(snapshot.get("private_test_channel_id_present"))
            ),
            "login_attempt_requires_token_and_channel": True,
            "preflight_snapshot": dict(snapshot),
        }
    )
    return report


def assert_phase40t_readonly_preflight_snapshot_safe(snapshot: Mapping[str, Any]) -> None:
    text = json.dumps(snapshot, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40T preflight snapshot contains sensitive values.")
    for key in (
        "discord_token_value_logged",
        "private_test_channel_id_value_logged",
        "approval_phrase_value_logged",
        "api_key_value_logged",
        "raw_discord_ids_logged",
        "raw_content_logged",
        "secret_values_logged",
        "external_execution",
    ):
        if snapshot.get(key):
            raise ValueError(f"Phase 40T preflight snapshot unsafe flag is true: {key}")


def render_phase40t_readonly_preflight_snapshot_markdown(snapshot: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40T Read-only Preflight Snapshot",
            "",
            f"- Preflight passed: {str(snapshot.get('preflight_passed')).lower()}",
            f"- Discord token present: {str(snapshot.get('discord_token_present')).lower()}",
            f"- Private-test channel id present: {str(snapshot.get('private_test_channel_id_present')).lower()}",
            f"- Approval exact match: {str(snapshot.get('approval_phrase_exact_match')).lower()}",
            f"- Reply mode readonly_private_test_only: {str(snapshot.get('reply_mode_readonly_private_test_only')).lower()}",
            "- Token/channel/approval values logged: false",
            "- Raw Discord IDs/content logged: false",
        ]
    ) + "\n"
