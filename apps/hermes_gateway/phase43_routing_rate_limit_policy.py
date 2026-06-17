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
    sends_sent: int = 0,
    max_sends: int = 1,
    cooldown_active: bool = False,
    one_shot_lock_consumed: bool = False,
    session_lock_active: bool = True,
    phase41b_repeat_locked: bool = True,
    manual_gate_open: bool = False,
) -> dict[str, Any]:
    limit_remaining = replies_sent < max_replies
    send_limit_remaining = sends_sent < max_sends
    allowed_by_policy = limit_remaining and send_limit_remaining and not cooldown_active and not one_shot_lock_consumed and session_lock_active and manual_gate_open and not phase41b_repeat_locked
    return {
        "per_session_max_replies": max_replies,
        "per_session_max_sends": max_sends,
        "replies_sent": replies_sent,
        "sends_sent": sends_sent,
        "limit_remaining": limit_remaining,
        "send_limit_remaining": send_limit_remaining,
        "cooldown_active": cooldown_active,
        "one_shot_lock_consumed": one_shot_lock_consumed,
        "session_lock_active": session_lock_active,
        "phase41b_repeat_locked": phase41b_repeat_locked,
        "manual_gate_open": manual_gate_open,
        "crash_recovery_lock_placeholder": True,
        "rate_limit_allows_reply": allowed_by_policy,
        "send_allowed": False,
    }


def build_phase43_routing_rate_limit_policy(event: Mapping[str, Any] | None = None) -> dict[str, Any]:
    routing = evaluate_phase43_routing_policy(event)
    rate_limit = evaluate_phase43_rate_limit(one_shot_lock_consumed=True, phase41b_repeat_locked=True, manual_gate_open=False)
    return {
        "report_type": "phase43_routing_rate_limit_policy",
        "version": VERSION,
        "routing_policy_available": True,
        "rate_limit_policy_available": True,
        "session_lock_policy_available": True,
        "routing": routing,
        "rate_limit": rate_limit,
        "private_test_eligible": bool(routing["private_test_human_eligible"]),
        "phase41b_repeat_send_locked": True,
        "phase42_actual_supervised_session_succeeded": True,
        "phase42_message_sent_count": 1,
        "phase42_sent_scope": "private_test_only",
        "phase42_repeat_supervised_session_locked": True,
        "phase42_repeat_supervised_session_allowed": False,
        "phase42_manual_gate_required": True,
        "phase42_manual_gate_open": False,
        "phase42_session_lock_active": True,
        "phase42_max_session_messages_enforced": True,
        "phase42_max_send_count_enforced": True,
        "ready_for_phase41b_repeat_send": False,
        "ready_for_phase42_actual_supervised_session": False,
        "ready_for_phase42_repeat_supervised_session": False,
        "public_team_blocked": True,
        "self_bot_duplicate_blocked": True,
        "unattended_auto_reply_allowed": False,
        "public_channel_send_allowed": False,
        "team_channel_send_allowed": False,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "operator_command_separated": bool(routing["operator_command_separated"]),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
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
