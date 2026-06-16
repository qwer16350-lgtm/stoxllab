"""Phase 44 deterministic fake LLM adapter."""

from __future__ import annotations

from typing import Any, Mapping

from phase44_llm_preflight_contract import build_phase44_prompt_packet, validate_phase44_llm_output_schema


VERSION = "phase44_fake_llm_adapter"
_FAKE_REPLY = "STOXL private-test deterministic fake reply. No provider call was made."


def run_phase44_fake_llm_adapter(prompt_packet: Mapping[str, Any] | None = None) -> dict[str, Any]:
    packet = dict(prompt_packet or build_phase44_prompt_packet())
    output = {
        "schema_version": "phase44_fake_llm_output_v1",
        "reply_text": _FAKE_REPLY,
        "safety": {
            "deterministic": True,
            "provider_called": False,
            "raw_content_included": False,
            "raw_discord_ids_included": False,
            "secret_values_included": False,
        },
    }
    return {
        "report_type": "phase44_fake_llm_reply_dry_run",
        "version": VERSION,
        "fake_adapter_used": True,
        "deterministic_fake_response": True,
        "prompt_packet_schema": packet.get("schema_version"),
        "output": output,
        "output_schema_valid": validate_phase44_llm_output_schema(output),
        "actual_llm_api_call": False,
        "llm_api_call_attempted": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
    }


def render_phase44_fake_llm_reply_dry_run_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 44 Fake LLM Reply Dry-run",
            "",
            "- Fake adapter used: true",
            "- Deterministic fake response: true",
            f"- Output schema valid: {str(report.get('output_schema_valid')).lower()}",
            "- Actual LLM API call: false",
            "- Discord message sent: false",
        ]
    ) + "\n"
