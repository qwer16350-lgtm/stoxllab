"""Reply planner that is disabled by default and never sends messages."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_reply_plan(
    evaluation_result: dict[str, Any],
    would_send_payload: dict[str, Any] | None = None,
    reply_enabled: bool = False,
) -> dict[str, Any]:
    payload = would_send_payload or {}
    plan = {
        "reply_plan_type": "disabled_by_default",
        "reply_enabled": False if not reply_enabled else False,
        "mode": "would_send_only",
        "target_channel": payload.get("target_channel", ""),
        "message_kind": payload.get("message_kind", "blocked_request" if evaluation_result.get("blocked") else "agent_dispatch"),
        "content_preview": str(payload.get("content", ""))[:160],
        "will_send": False,
        "requires_manual_enable": True,
        "safety": {
            "discord_api_called": False,
            "message_sent": False,
            "external_execution": False,
            "human_only_execution": True,
        },
    }
    assert_reply_plan_safe(plan)
    return plan


def assert_reply_plan_safe(reply_plan: dict[str, Any]) -> None:
    if reply_plan.get("will_send") is not False or reply_plan.get("reply_enabled") is not False:
        raise ValueError("Reply planner must remain disabled in this phase.")
    safety = reply_plan.get("safety", {})
    if safety.get("discord_api_called") or safety.get("message_sent") or safety.get("external_execution"):
        raise ValueError("Reply planner safety flags are unsafe.")


def build_reply_planner_report(root: str | Path) -> dict[str, Any]:
    return {
        "report_type": "reply_planner_report",
        "version": "phase26_disabled_by_default",
        "default_reply_enabled": False,
        "allowed_modes": ["disabled", "would_send_only", "private_test_later"],
        "public_channel_reply_allowed": False,
        "safety_assertions": {
            "discord_api_called": False,
            "message_sent": False,
            "external_execution": False,
            "human_only_execution": True,
        },
    }
