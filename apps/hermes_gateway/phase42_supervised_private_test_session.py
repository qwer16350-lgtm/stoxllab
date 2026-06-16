"""Phase 42 supervised deterministic private-test session preflight."""

from __future__ import annotations

from typing import Any, Mapping


VERSION = "phase42_supervised_private_test_session_preflight"


def build_phase42_supervised_private_test_session_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = env or {}
    max_reply_count = int(env.get("HERMES_PHASE42_MAX_REPLY_COUNT", "0") or 0)
    timeout_seconds = int(env.get("HERMES_PHASE42_TIMEOUT_SECONDS", "0") or 0)
    cooldown_seconds = int(env.get("HERMES_PHASE42_COOLDOWN_SECONDS", "0") or 0)
    private_test_only = str(env.get("HERMES_DISCORD_REPLY_MODE", "")) == "private_test_only"
    deterministic_reply_only = str(env.get("HERMES_PHASE42_DETERMINISTIC_REPLY_ONLY", "")).lower() == "true"
    llm_disabled = str(env.get("HERMES_DISCORD_LLM_ENABLED", "")).lower() != "true"
    rag_disabled = str(env.get("HERMES_DISCORD_RAG_ENABLED", "")).lower() != "true"
    external_disabled = str(env.get("HERMES_DISCORD_EXTERNAL_EXECUTION", "")).lower() != "true"
    checks = {
        "max_reply_count_required": max_reply_count > 0,
        "timeout_required": timeout_seconds > 0,
        "cooldown_required": cooldown_seconds > 0,
        "private_test_only": private_test_only,
        "deterministic_reply_only": deterministic_reply_only,
        "llm_disabled": llm_disabled,
        "rag_disabled": rag_disabled,
        "external_execution_disabled": external_disabled,
    }
    ready = all(checks.values())
    return {
        "report_type": "phase42_supervised_private_test_session_preflight",
        "version": VERSION,
        "supervised_session_preflight_only": True,
        "default_blocked": not ready,
        "blocked": not ready,
        "blocked_reasons": [key for key, value in checks.items() if not value],
        "max_reply_count": max_reply_count,
        "timeout_seconds": timeout_seconds,
        "cooldown_seconds": cooldown_seconds,
        "private_test_only": private_test_only,
        "deterministic_reply_only": deterministic_reply_only,
        "llm_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "actual_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "ready_for_supervised_session": False,
    }


def render_phase42_supervised_private_test_session_preflight_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 42 Supervised Private-test Session",
            "",
            "- Preflight only: true",
            f"- Default blocked: {str(report.get('default_blocked')).lower()}",
            f"- Max reply count: {report.get('max_reply_count')}",
            f"- Timeout seconds: {report.get('timeout_seconds')}",
            f"- Cooldown seconds: {report.get('cooldown_seconds')}",
            "- Actual runtime executed: false",
        ]
    ) + "\n"
