"""Phase 44 LLM provider preflight and prompt contract scaffold."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase44_llm_provider_preflight_contract"
_SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|api[_ -]?key\s*[:=]\s*\S+|bearer\s+\S+|token\s*[:=]\s*\S+)")


def build_phase44_prompt_packet(query: str = "redacted private-test query") -> dict[str, Any]:
    return {
        "schema_version": "phase44_prompt_packet_v1",
        "input_summary": query[:80],
        "raw_message_content_included": False,
        "raw_discord_ids_included": False,
        "secret_values_included": False,
        "approval_phrase_included": False,
        "redaction_contract": {
            "token_values": "presence_boolean_only",
            "api_key_values": "presence_boolean_only",
            "discord_ids": "redacted",
            "message_content": "summary_only",
        },
    }


def validate_phase44_llm_output_schema(output: Mapping[str, Any]) -> bool:
    return isinstance(output.get("reply_text"), str) and isinstance(output.get("safety"), Mapping) and output.get("schema_version") == "phase44_fake_llm_output_v1"


def build_phase44_llm_provider_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = env or {}
    key_present = bool(str(env.get("OPENROUTER_API_KEY", "") or env.get("HERMES_OPENROUTER_API_KEY", "")).strip())
    packet = build_phase44_prompt_packet()
    report = {
        "report_type": "phase44_llm_provider_preflight",
        "version": VERSION,
        "default_blocked": True,
        "blocked": True,
        "blocked_reasons": ["actual_llm_api_call_forbidden_in_safe_prep_bundle"],
        "openrouter_api_key_present": key_present,
        "api_key_value_logged": False,
        "provider_preflight_only": True,
        "prompt_packet_schema": packet["schema_version"],
        "prompt_packet": packet,
        "actual_llm_api_call": False,
        "llm_api_call_attempted": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
    }
    assert_phase44_preflight_safe(report)
    return report


def assert_phase44_preflight_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if _SECRET_RE.search(text):
        raise ValueError("Phase 44 preflight contains a secret-like value.")
    for key in ("actual_llm_api_call", "llm_api_call_attempted", "discord_api_send_called", "discord_message_sent", "rag_called", "embedding_api_called", "external_execution"):
        if report.get(key):
            raise ValueError(f"Phase 44 unsafe flag is true: {key}")


def render_phase44_llm_provider_preflight_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 44 LLM Provider Preflight",
            "",
            "- Provider preflight only: true",
            f"- Key present: {str(report.get('openrouter_api_key_present')).lower()}",
            "- API key value logged: false",
            "- Actual LLM API call: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
