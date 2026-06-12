"""Hard stop guards for live Discord-facing actions.

Phase 29 permits a read-only Gateway runtime path, but every outbound action
remains blocked by default.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


OUTGOING_ACTION_TYPES = [
    "message_create",
    "message_update",
    "reaction_create",
    "channel_create",
    "channel_update",
    "role_create",
    "role_update",
    "webhook_create",
    "external_post",
    "external_submit",
    "external_email",
    "contract_response",
    "llm_call",
    "rag_read",
]


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def assert_send_disabled(config: dict[str, Any]) -> None:
    """Raise if any live-send or external-execution flag is enabled."""

    unsafe = []
    if _flag(config.get("send_messages")):
        unsafe.append("send_messages")
    if _flag(config.get("external_execution")):
        unsafe.append("external_execution")
    if _flag(config.get("llm_enabled")):
        unsafe.append("llm_enabled")
    if _flag(config.get("rag_enabled")):
        unsafe.append("rag_enabled")
    if unsafe:
        raise ValueError("Unsafe Phase 29 runtime flags enabled: " + ", ".join(unsafe))


def block_outgoing_action(action_type: str, reason: str | None = None) -> dict[str, Any]:
    """Return a denial record without executing the requested action."""

    return {
        "action_type": action_type,
        "allowed": False,
        "blocked": True,
        "reason": reason or "Phase 29 is read-only. Outbound Discord, external, LLM, and RAG actions are blocked.",
        "message_sent": False,
        "discord_write_api_called": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def is_outgoing_action_allowed(action_type: str, config: dict[str, Any] | None = None) -> bool:
    """Phase 29 never allows outbound actions."""

    if config:
        assert_send_disabled(config)
    return False


def build_send_block_report() -> dict[str, Any]:
    return {
        "report_type": "discord_send_blocking_guard",
        "version": "phase29_readonly",
        "outgoing_actions_checked": OUTGOING_ACTION_TYPES,
        "default_allowed": False,
        "blocked_actions": [block_outgoing_action(action) for action in OUTGOING_ACTION_TYPES],
        "safety_assertions": {
            "can_send_messages": False,
            "can_manage_channels": False,
            "can_manage_roles": False,
            "can_execute_external_actions": False,
            "llm_enabled": False,
            "rag_enabled": False,
            "human_only_execution_preserved": True,
        },
    }
