"""Deterministic prompt envelope preview for Phase 32A."""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "phase32a_no_api_call"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")
AGENT_TONE_HINTS = {
    "marin": "friendly marketing draft assistant, no final publish",
    "lucy": "concise senior marketing reviewer",
    "kasumi": "cautious operations researcher",
    "meiko": "firm operations reviewer",
    "reze": "soft strategic critique",
    "decision_maker_review": "approval required, no auto-approval",
    "unrouted": "ask for route clarification, no execution",
}


def redact_llm_prompt_content(text: str | None, max_chars: int = 4000) -> str:
    if not text:
        return ""
    redacted = SECRET_RE.sub("[REDACTED_SECRET]", str(text))
    redacted = LONG_ID_RE.sub("[REDACTED_DISCORD_ID]", redacted)
    return redacted[:max(max_chars, 0)]


def _int_value(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_llm_prompt_envelope(
    agent_route_candidate: str,
    user_content_preview: str,
    context: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_context = context or {}
    selected_policy = policy or {}
    max_input_chars = _int_value(selected_policy.get("max_input_chars", selected_context.get("max_input_chars", 4000)), 4000)
    agent = str(agent_route_candidate or "unrouted")
    tone_hint = AGENT_TONE_HINTS.get(agent, AGENT_TONE_HINTS["unrouted"])
    preview = redact_llm_prompt_content(user_content_preview, max_input_chars)
    system_text = (
        "STOXL Hermes Phase 32A prompt preview only. "
        "Do not call tools, do not access RAG, do not execute external actions, "
        "do not claim final approval, and do not send Discord messages. "
        f"Agent tone hint: {tone_hint}."
    )
    envelope = {
        "envelope_type": "llm_prompt_envelope",
        "version": VERSION,
        "agent_route_candidate": agent,
        "channel_scope": "private_test_only",
        "system_safety": {
            "external_execution_allowed": False,
            "rag_allowed": False,
            "discord_send_allowed": False,
            "must_not_claim_approval": True,
            "must_not_execute_external_actions": True,
        },
        "input_limits": {
            "max_input_chars": max_input_chars,
            "raw_content_included": False,
            "content_preview_only": True,
        },
        "messages_preview": [
            {
                "role": "system",
                "content": system_text,
            },
            {
                "role": "user",
                "content": preview,
            },
        ],
        "safety_assertions": {
            "api_key_included": False,
            "raw_discord_id_included": False,
            "llm_api_called": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
        },
    }
    assert_llm_prompt_envelope_safe(envelope)
    return envelope


def assert_llm_prompt_envelope_safe(envelope: dict[str, Any]) -> None:
    text = json.dumps(envelope, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("LLM prompt envelope contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("LLM prompt envelope contains raw Discord-like IDs.")
    assertions = envelope.get("safety_assertions", {})
    for key in ("api_key_included", "raw_discord_id_included", "llm_api_called", "discord_message_sent", "rag_called", "external_execution"):
        if assertions.get(key):
            raise ValueError(f"LLM prompt envelope unsafe assertion is true: {key}")
    safety = envelope.get("system_safety", {})
    for key in ("external_execution_allowed", "rag_allowed", "discord_send_allowed"):
        if safety.get(key):
            raise ValueError(f"LLM prompt envelope unsafe permission is true: {key}")


def render_llm_prompt_envelope_preview(envelope: dict[str, Any]) -> str:
    messages = envelope.get("messages_preview", [])
    user_preview = ""
    if len(messages) > 1:
        user_preview = str(messages[1].get("content", ""))
    return "\n".join(
        [
            "# LLM Prompt Envelope Preview",
            "",
            f"- version: {envelope.get('version', '')}",
            f"- agent_route_candidate: {envelope.get('agent_route_candidate', '')}",
            f"- channel_scope: {envelope.get('channel_scope', '')}",
            f"- max_input_chars: {envelope.get('input_limits', {}).get('max_input_chars')}",
            "- raw_content_included: false",
            "- content_preview_only: true",
            "- external_execution_allowed: false",
            "- rag_allowed: false",
            "- discord_send_allowed: false",
            "",
            "## User Preview",
            user_preview,
        ]
    ) + "\n"
