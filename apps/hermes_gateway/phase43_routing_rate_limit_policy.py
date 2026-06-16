"""Phase 43 routing, rate-limit, and session-lock policy scaffold."""

from __future__ import annotations

from typing import Any, Mapping


VERSION = "phase43_routing_rate_limit_session_policy"


def evaluate_phase43_routing_policy(event: Mapping[str, Any] | None = None) -> dict[str, Any]:
    event = event or {}
    channel_scope = str(event.get("channel_scope", "private_test") or "private_test")
    author_type = str(event.get("author_type", "human") or "human")
    duplicate = bool(event.get("duplicate"))
    operator_command = bool(event.get("operator_command"))
    eligible = channel_scope == "private_test" and author_type == "human" and not duplicate and not operator_command
    return {
        "private_test_human_eligible": eligible,
        "self_ignored": author_type == "self",
        "bot_ignored": author_type == "bot",
        "duplicate_ignored": duplicate,
        "public_team_not_eligible_for_send": channel_scope in {"public", "team"},
        "operator_command_separated": operator_command,
        "send_allowed": False,
    }


def evaluate_phase43_rate_limit(
    *,
    replies_sent: int = 0,
    max_replies: int = 1,
    cooldown_active: bool = False,
    one_shot_lock_consumed: bool = False,
    session_lock_active: bool = True,
) -> dict[str, Any]:
    limit_remaining = replies_sent < max_replies
    allowed_by_policy = limit_remaining and not cooldown_active and not one_shot_lock_consumed and session_lock_active
    return {
        "per_session_max_replies": max_replies,
        "replies_sent": replies_sent,
        "limit_remaining": limit_remaining,
        "cooldown_active": cooldown_active,
        "one_shot_lock_consumed": one_shot_lock_consumed,
        "session_lock_active": session_lock_active,
        "crash_recovery_lock_placeholder": True,
        "rate_limit_allows_reply": allowed_by_policy,
        "send_allowed": False,
    }


def build_phase43_routing_rate_limit_policy(event: Mapping[str, Any] | None = None) -> dict[str, Any]:
    routing = evaluate_phase43_routing_policy(event)
    rate_limit = evaluate_phase43_rate_limit()
    return {
        "report_type": "phase43_routing_rate_limit_policy",
        "version": VERSION,
        "routing_policy_available": True,
        "rate_limit_policy_available": True,
        "session_lock_policy_available": True,
        "routing": routing,
        "rate_limit": rate_limit,
        "private_test_eligible": bool(routing["private_test_human_eligible"]),
        "public_team_blocked": True,
        "self_bot_duplicate_blocked": True,
        "operator_command_separated": bool(routing["operator_command_separated"]),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "external_execution": False,
    }


def render_phase43_routing_rate_limit_policy_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 43 Routing and Rate-limit Policy",
            "",
            "- Routing policy available: true",
            "- Rate-limit policy available: true",
            "- Session lock policy available: true",
            "- Discord send allowed: false",
            "- External execution: false",
        ]
    ) + "\n"
