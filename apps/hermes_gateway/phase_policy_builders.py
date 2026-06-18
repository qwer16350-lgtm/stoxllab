"""Shared policy report builders for post-MVP Hermes phase reports.

These helpers return labels, booleans, and counts only. They never include raw
content, token values, channel values, approval phrases, or IDs.
"""

from __future__ import annotations

from typing import Any


def build_allowed_scope(*items: str) -> list[str]:
    return list(items)


def build_blocked_scope(*items: str) -> list[str]:
    return list(items)


def build_policy_capsule_report(allowed_scope: list[str], blocked_scope: list[str]) -> dict[str, Any]:
    return {
        "policy_capsule_available": True,
        "allowed_scope": list(allowed_scope),
        "blocked_scope": list(blocked_scope),
    }


def build_known_team_low_risk_policy_report() -> dict[str, bool]:
    return {
        "known_team_channel_required": True,
        "low_risk_intent_required": True,
        "deterministic_template_only": True,
    }


def build_phase_progression_report(
    current_verified_level: str,
    next_target_level: str,
    production_unattended_ready: bool = False,
) -> dict[str, Any]:
    return {
        "current_verified_level": current_verified_level,
        "next_target_level": next_target_level,
        "ready_for_production_unattended": production_unattended_ready,
    }


def build_queue_review_packet_report(
    queue_required: bool = True,
    packet_required: bool = True,
    raw_content_included: bool = False,
) -> dict[str, Any]:
    return {
        "ops_queue_required": queue_required,
        "ops_queue_item_exists": queue_required,
        "review_packet_required": packet_required,
        "review_packet_exists": packet_required,
        "review_packet_raw_content_included": raw_content_included,
    }


def build_limited_bounds_report(
    max_session_seconds: int,
    max_send_count: int,
    max_reply_count: int,
    cooldown_seconds: int,
) -> dict[str, Any]:
    return {
        "max_session_seconds": max_session_seconds,
        "max_send_count": max_send_count,
        "max_reply_count": max_reply_count,
        "cooldown_seconds": cooldown_seconds,
        "session_bounds_required": True,
        "session_seconds_bounded": 0 < max_session_seconds <= 60,
        "max_send_count_configured": max_send_count == 1,
        "max_reply_count_configured": max_reply_count == 1,
        "cooldown_required": True,
        "cooldown_configured": cooldown_seconds >= 5,
    }
