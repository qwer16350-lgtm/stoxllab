"""Phase 33D-2 RAG+LLM live preflight closeout without live execution."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_llm_private_test_runtime import (
    build_rag_llm_private_reply_preflight,
    build_rag_llm_private_test_runtime_report,
)


VERSION = "phase33d_2_no_live_execution"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
RUNTIME_OPTION = "--run-discord-private-test-rag-llm-reply"

LIVE_READY_FIXTURE_ENV: dict[str, str] = {
    "HERMES_RAG_LLM_REPLY_ENABLED": "true",
    "HERMES_RAG_LLM_REPLY_MODE": "private_test_only",
    "HERMES_RAG_LLM_REQUIRE_RAG_PACKET": "true",
    "HERMES_RAG_LLM_REQUIRE_CONTEXT_SAFETY": "true",
    "HERMES_RAG_LLM_REQUIRE_OUTPUT_SAFETY": "true",
    "HERMES_RAG_LLM_MAX_CONTEXT_CHARS": "3000",
    "HERMES_RAG_LLM_MAX_DOCUMENTS": "5",
    "HERMES_RAG_LLM_MAX_REPLIES_PER_SESSION": "2",
    "HERMES_RAG_LLM_COOLDOWN_SECONDS": "0",
    "HERMES_DISCORD_SEND_MESSAGES": "true",
    "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
    "HERMES_DISCORD_REPLY_MODE": "private_test_only",
    "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_channel",
    "HERMES_RAG_ENABLED": "true",
    "HERMES_RAG_MODE": "local_readonly",
    "HERMES_RAG_PRIVATE_TEST_ONLY": "true",
    "HERMES_RAG_REQUIRE_RESPONSE_PACKET": "true",
    "HERMES_LLM_ENABLED": "true",
    "HERMES_LLM_API_CALL_ENABLED": "true",
    "HERMES_LLM_PROVIDER": "openrouter",
    "HERMES_LLM_MODEL": "openai/gpt-5.4-mini",
    "HERMES_LLM_API_KEY": "present",
    "HERMES_LLM_PRIVATE_TEST_ONLY": "true",
    "HERMES_LLM_DISCORD_SEND_ENABLED": "true",
    "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "true",
    "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
    "HERMES_LLM_EXTERNAL_EXECUTION": "false",
}

BLOCKED_BEFORE_RETRIEVAL = [
    "public_channel",
    "team_mapped_channel",
    "self_message",
    "bot_message",
    "duplicate_message",
    "cooldown",
    "budget_exhausted",
    "invalid_source",
    "operations_source",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_rag_llm_live_preflight_closeout(root: str | None = None) -> dict[str, Any]:
    default_preflight = build_rag_llm_private_reply_preflight({})
    mock_preflight = build_rag_llm_private_reply_preflight(LIVE_READY_FIXTURE_ENV)
    mock_runtime_report = build_rag_llm_private_test_runtime_report(root=root, env=LIVE_READY_FIXTURE_ENV)
    mock_ready = bool(mock_preflight.get("ready")) and bool(mock_runtime_report.get("ready"))
    report = {
        "report_type": "rag_llm_live_preflight_closeout",
        "version": VERSION,
        "created_at": utc_now(),
        "default_preflight_blocked": bool(default_preflight.get("blocked")),
        "default_preflight_blocked_reasons": default_preflight.get("blocked_reasons", []),
        "mock_live_ready_fixture_passed": mock_ready,
        "mock_live_ready_blocked_reasons": mock_preflight.get("blocked_reasons", []),
        "runtime_option_present": bool(mock_runtime_report.get("runtime_option_added")),
        "runtime_option": RUNTIME_OPTION,
        "runtime_executed": False,
        "ready_for_single_live_private_test": mock_ready,
        "live_requirements": {
            "private_test_only": True,
            "private_test_channel_id_required": True,
            "channel_id_match_required": True,
            "source_operation_required": True,
            "source_operations_forbidden": True,
            "local_readonly_rag_required": True,
            "rag_response_packet_required": True,
            "rag_context_safety_required": True,
            "llm_output_safety_required": True,
            "cooldown_required": True,
            "budget_required": True,
            "duplicate_guard_required": True,
            "self_bot_guard_required": True,
            "public_team_channel_block_required": True,
            "separate_manual_approval_required": True,
        },
        "blocked_before_retrieval": BLOCKED_BEFORE_RETRIEVAL,
        "actual_discord_send": False,
        "actual_llm_api_call": False,
        "embedding_api_called": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    assert_rag_llm_live_preflight_closeout_safe(report)
    return report


def render_rag_llm_live_preflight_closeout_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# STOXL RAG+LLM Live Preflight Closeout",
        "",
        f"- Version: {report.get('version')}",
        f"- Default preflight blocked: {str(report.get('default_preflight_blocked')).lower()}",
        f"- Mock live ready fixture passed: {str(report.get('mock_live_ready_fixture_passed')).lower()}",
        f"- Runtime option present: {str(report.get('runtime_option_present')).lower()}",
        f"- Runtime option: `{report.get('runtime_option')}`",
        "- Runtime executed: false",
        f"- Ready for single live private test: {str(report.get('ready_for_single_live_private_test')).lower()}",
        "- Actual Discord send: false",
        "- Actual LLM API call: false",
        "- Embedding API called: false",
        "- External execution: false",
        "",
        "## Live Requirements",
    ]
    lines.extend(f"- {key}: {str(value).lower()}" for key, value in report.get("live_requirements", {}).items())
    lines.extend(["", "## Blocked Before Retrieval"])
    lines.extend(f"- {item}" for item in report.get("blocked_before_retrieval", []))
    lines.extend(
        [
            "",
            "## Safety",
            "- Discord live runtime was not executed.",
            "- No Discord message was sent.",
            "- No OpenRouter or LLM API call was made.",
            "- No embedding API call was made.",
            "- No external execution was performed.",
            "- The next single live private test still requires separate manual approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def assert_rag_llm_live_preflight_closeout_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("RAG+LLM live preflight closeout contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("RAG+LLM live preflight closeout contains raw Discord-like IDs.")
    if not isinstance(report, dict):
        return
    if report.get("runtime_executed"):
        raise ValueError("Closeout report must not execute runtime.")
    for key in ("actual_discord_send", "actual_llm_api_call", "embedding_api_called", "external_execution"):
        if report.get(key):
            raise ValueError(f"Closeout unsafe flag is true: {key}")
    safety = report.get("safety_assertions", {})
    for key in ("api_key_value_logged", "raw_discord_ids_logged", "embedding_called", "llm_called", "discord_message_sent", "external_execution"):
        if safety.get(key):
            raise ValueError(f"Closeout unsafe assertion is true: {key}")
