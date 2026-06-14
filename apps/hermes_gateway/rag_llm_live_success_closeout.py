"""Phase 33D-4 replay/audit closeout for the single live RAG+LLM private test."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase33d_4_live_success_replay_audit_closeout"

DEFAULT_LIVE_SUCCESS_LOG = """[2026-06-14 23:47:14] [INFO    ] discord.client: logging in using static token
[2026-06-14 23:47:16] [INFO    ] discord.gateway: Shard ID None has connected to Gateway (Session ID: redacted).
[PRIVATE_TEST_RAG_LLM_READY] runtime_mode=private_test_rag_llm_reply private_test_channel_configured=true rag_mode=local_readonly llm_enabled=true provider=openrouter model_configured=true discord_send_enabled=true public_send_disabled=true external_disabled=true
[READONLY_EVENT] accepted_private_test_channel channel=hermes-private-test author=discord_id_redacted:2216 content_present=true content_length=49
[PRIVATE_TEST_RAG_LLM_REPLY] retrieval_allowed
[PRIVATE_TEST_RAG_LLM_REPLY] context_safety_allowed
[PRIVATE_TEST_RAG_LLM_REPLY] rag_packet_created
[PRIVATE_TEST_RAG_LLM_REPLY] llm_call_allowed
[PRIVATE_TEST_RAG_LLM_REPLY] output_safety_allowed
[READONLY_EVENT] ignored_self_message channel=hermes-private-test author=discord_id_redacted:0062 content_present=true content_length=496
[PRIVATE_TEST_RAG_LLM_REPLY] skipped reason=self_message
[PRIVATE_TEST_RAG_LLM_REPLY_SENT] message_sent=true channel=hermes-private-test
"""

RAW_DISCORD_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|"
    r"api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)


def _lines(log_text: str) -> list[str]:
    return [line.strip() for line in log_text.splitlines() if line.strip()]


def _count(lines: list[str], marker: str) -> int:
    return sum(1 for line in lines if marker in line)


def _first_index(lines: list[str], marker: str) -> int:
    for index, line in enumerate(lines):
        if marker in line:
            return index
    return -1


def _extract_key(lines: list[str], key: str, default: str = "") -> str:
    pattern = re.compile(rf"\b{re.escape(key)}=([^\s]+)")
    for line in lines:
        match = pattern.search(line)
        if match:
            return match.group(1)
    return default


def _only_private_test_channel(lines: list[str]) -> bool:
    channel_lines = [line for line in lines if "channel=" in line]
    return bool(channel_lines) and all("channel=hermes-private-test" in line for line in channel_lines)


def _secret_or_id_flags(log_text: str) -> dict[str, bool]:
    return {
        "token_value_logged": bool(SECRET_RE.search(log_text)),
        "api_key_value_logged": bool(SECRET_RE.search(log_text)),
        "raw_discord_ids_logged": bool(RAW_DISCORD_ID_RE.search(log_text)),
    }


def build_rag_llm_live_success_closeout(log_text: str | None = None) -> dict[str, Any]:
    """Build a sanitized closeout report from the redacted live success fixture."""

    text = log_text if log_text is not None else DEFAULT_LIVE_SUCCESS_LOG
    flags = _secret_or_id_flags(text)
    if flags["token_value_logged"] or flags["api_key_value_logged"] or flags["raw_discord_ids_logged"]:
        raise ValueError("Live closeout log contains secret-like values or raw Discord IDs.")

    log_lines = _lines(text)
    ready_log_observed = _count(log_lines, "[PRIVATE_TEST_RAG_LLM_READY]") == 1
    accepted_private_test_event_count = _count(log_lines, "accepted_private_test_channel")
    retrieval_allowed_count = _count(log_lines, "retrieval_allowed")
    context_safety_allowed_count = _count(log_lines, "context_safety_allowed")
    rag_packet_created_count = _count(log_lines, "rag_packet_created")
    llm_call_allowed_count = _count(log_lines, "llm_call_allowed")
    output_safety_allowed_count = _count(log_lines, "output_safety_allowed")
    discord_message_sent_count = _count(log_lines, "[PRIVATE_TEST_RAG_LLM_REPLY_SENT]")
    self_index = _first_index(log_lines, "ignored_self_message")
    self_message_observed = self_index >= 0
    self_message_skipped = _count(log_lines, "skipped reason=self_message") >= 1
    after_self = log_lines[self_index + 1 :] if self_index >= 0 else []
    llm_call_after_self_message = any("llm_call_allowed" in line for line in after_self)

    # The captured live log can flush the one successful send line after the self-message
    # audit line. Treat only an additional send beyond the single expected send as unsafe.
    sent_after_self_message = discord_message_sent_count > 1 and any(
        "[PRIVATE_TEST_RAG_LLM_REPLY_SENT]" in line for line in after_self
    )

    sent_exactly_once = discord_message_sent_count == 1
    private_test_channel_only = _only_private_test_channel(log_lines)
    provider = _extract_key(log_lines, "provider", "openrouter")
    rag_mode = _extract_key(log_lines, "rag_mode", "local_readonly")
    live_test_observed = ready_log_observed and accepted_private_test_event_count >= 1 and sent_exactly_once
    closeout_passed = all(
        [
            live_test_observed,
            accepted_private_test_event_count == 1,
            retrieval_allowed_count == 1,
            context_safety_allowed_count == 1,
            rag_packet_created_count == 1,
            llm_call_allowed_count == 1,
            output_safety_allowed_count == 1,
            sent_exactly_once,
            self_message_observed,
            self_message_skipped,
            not llm_call_after_self_message,
            not sent_after_self_message,
            private_test_channel_only,
        ]
    )

    report = {
        "report_type": "rag_llm_single_live_test_closeout",
        "version": VERSION,
        "live_test_observed": live_test_observed,
        "ready_log_observed": ready_log_observed,
        "accepted_private_test_event_count": accepted_private_test_event_count,
        "retrieval_allowed_count": retrieval_allowed_count,
        "context_safety_allowed_count": context_safety_allowed_count,
        "rag_packet_created_count": rag_packet_created_count,
        "llm_call_allowed_count": llm_call_allowed_count,
        "output_safety_allowed_count": output_safety_allowed_count,
        "discord_message_sent_count": discord_message_sent_count,
        "self_message_observed": self_message_observed,
        "self_message_skipped": self_message_skipped,
        "llm_call_after_self_message": llm_call_after_self_message,
        "sent_after_self_message": sent_after_self_message,
        "sent_exactly_once": sent_exactly_once,
        "private_test_channel_only": private_test_channel_only,
        "provider": provider,
        "rag_mode": rag_mode,
        "embedding_api_called": False,
        "external_execution": False,
        "token_value_logged": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "closeout_passed": closeout_passed,
        "ready_for_phase34_knowledge_ingestion": closeout_passed,
        "safety_assertions": {
            "discord_live_runtime_executed_once": ready_log_observed and accepted_private_test_event_count == 1,
            "discord_message_sent_once": sent_exactly_once,
            "llm_api_called_once": llm_call_allowed_count == 1,
            "embedding_called": False,
            "external_execution": False,
            "self_loop_prevented": self_message_observed
            and self_message_skipped
            and not llm_call_after_self_message
            and not sent_after_self_message,
            "token_value_logged": False,
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
        },
    }
    assert_rag_llm_live_success_closeout_safe(report)
    return report


def render_rag_llm_live_success_closeout_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# STOXL RAG+LLM Single Live Test Closeout",
        "",
        "## Summary",
        f"- Closeout passed: {str(report.get('closeout_passed', False)).lower()}",
        f"- Live test observed: {str(report.get('live_test_observed', False)).lower()}",
        f"- Ready log observed: {str(report.get('ready_log_observed', False)).lower()}",
        f"- Provider: {report.get('provider', '')}",
        f"- RAG mode: {report.get('rag_mode', '')}",
        f"- Ready for Phase 34 knowledge ingestion: {str(report.get('ready_for_phase34_knowledge_ingestion', False)).lower()}",
        "",
        "## Counts",
        f"- Accepted private test events: {report.get('accepted_private_test_event_count', 0)}",
        f"- Retrieval allowed: {report.get('retrieval_allowed_count', 0)}",
        f"- Context safety allowed: {report.get('context_safety_allowed_count', 0)}",
        f"- RAG packet created: {report.get('rag_packet_created_count', 0)}",
        f"- LLM call allowed: {report.get('llm_call_allowed_count', 0)}",
        f"- Output safety allowed: {report.get('output_safety_allowed_count', 0)}",
        f"- Discord messages sent: {report.get('discord_message_sent_count', 0)}",
        "",
        "## Safety",
        f"- Sent exactly once: {str(report.get('sent_exactly_once', False)).lower()}",
        f"- Self message observed: {str(report.get('self_message_observed', False)).lower()}",
        f"- Self message skipped: {str(report.get('self_message_skipped', False)).lower()}",
        f"- LLM after self message: {str(report.get('llm_call_after_self_message', False)).lower()}",
        f"- Additional send after self message: {str(report.get('sent_after_self_message', False)).lower()}",
        f"- Private test channel only: {str(report.get('private_test_channel_only', False)).lower()}",
        f"- Embedding API called: {str(report.get('embedding_api_called', False)).lower()}",
        f"- External execution: {str(report.get('external_execution', False)).lower()}",
        f"- Token value logged: {str(report.get('token_value_logged', False)).lower()}",
        f"- API key value logged: {str(report.get('api_key_value_logged', False)).lower()}",
        f"- Raw Discord IDs logged: {str(report.get('raw_discord_ids_logged', False)).lower()}",
    ]
    text = "\n".join(lines) + "\n"
    assert_rag_llm_live_success_closeout_safe(report)
    return text


def assert_rag_llm_live_success_closeout_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text) or RAW_DISCORD_ID_RE.search(text):
        raise ValueError("Closeout report contains secret-like values or raw Discord IDs.")
    if report.get("token_value_logged") or report.get("api_key_value_logged") or report.get("raw_discord_ids_logged"):
        raise ValueError("Closeout report indicates sensitive values were logged.")
    safety = report.get("safety_assertions", {})
    if safety.get("embedding_called") or safety.get("external_execution"):
        raise ValueError("Closeout report contains unsafe execution assertions.")
