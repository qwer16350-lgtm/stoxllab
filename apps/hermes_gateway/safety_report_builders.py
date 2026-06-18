"""Shared safety report builders for Hermes post-MVP compaction.

These helpers create report fragments only. They do not run Discord runtime,
send messages, call LLM/RAG, execute external commands, or start scheduler live
execution.
"""

from __future__ import annotations

from typing import Any, Mapping


def base_no_runtime_send_report() -> dict[str, Any]:
    return {
        "actual_discord_runtime_executed": False,
        "discord_gateway_live_connection_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "reply_count": 0,
    }


def base_no_llm_rag_external_report() -> dict[str, Any]:
    return {
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }


def base_scheduler_disabled_report() -> dict[str, Any]:
    return {
        "scheduler_live_execution": False,
        "cron_started": False,
        "unattended_production_auto_reply_executed": False,
    }


def base_secret_redaction_report() -> dict[str, Any]:
    return {
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "raw_session_ids_logged": False,
        "secret_values_logged": False,
        "approval_phrase_value_logged": False,
        "team_channel_id_value_logged": False,
    }


def base_no_external_action_report() -> dict[str, Any]:
    return {
        **base_no_runtime_send_report(),
        **base_no_llm_rag_external_report(),
        **base_scheduler_disabled_report(),
        **base_secret_redaction_report(),
    }


def build_blocked_report(
    report_type: str,
    blocked_reasons: list[str] | tuple[str, ...],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        **base_no_external_action_report(),
        "report_type": report_type,
        "blocked": True,
        "blocked_reasons": list(blocked_reasons),
        **dict(extra or {}),
    }


def build_consumed_lock_report(lock_name: str, blocked_reason: str) -> dict[str, Any]:
    return build_blocked_report(
        f"{lock_name}_blocked",
        [blocked_reason],
        {
            "consumed_lock_name": lock_name,
            f"{lock_name}_already_consumed": True,
            f"{lock_name}_repeat_locked": True,
            "ready_for_repeat": False,
        },
    )
