"""Phase 45A actual LLM one-shot call preflight gate."""

from __future__ import annotations

from typing import Any, Mapping


VERSION = "phase45_actual_llm_one_shot_preflight"
_EXPECTED_APPROVAL_PHRASE = "I_APPROVE_PHASE45A_ACTUAL_LLM_ONE_SHOT"


def build_phase45_actual_llm_one_shot_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = env or {}
    manual_approval_true = str(env.get("HERMES_PHASE45A_MANUAL_APPROVAL", "")).lower() == "true"
    approval_phrase_match = str(env.get("HERMES_PHASE45A_APPROVAL_PHRASE", "")) == _EXPECTED_APPROVAL_PHRASE
    cost_guard_present = str(env.get("HERMES_PHASE45A_COST_GUARD", "")).lower() == "true"
    call_count_guard_present = str(env.get("HERMES_PHASE45A_CALL_COUNT_GUARD", "")).lower() == "true"
    discord_send_false = str(env.get("HERMES_DISCORD_SEND_MESSAGES", "")).lower() != "true"
    key_present = bool(str(env.get("OPENROUTER_API_KEY", "") or env.get("HERMES_OPENROUTER_API_KEY", "")).strip())
    checks = {
        "manual_approval_true": manual_approval_true,
        "approval_phrase_match": approval_phrase_match,
        "cost_guard_present": cost_guard_present,
        "call_count_guard_present": call_count_guard_present,
        "discord_send_false": discord_send_false,
        "provider_key_present": key_present,
    }
    return {
        "report_type": "phase45_actual_llm_one_shot_preflight",
        "version": VERSION,
        "default_blocked": True,
        "blocked": True,
        "blocked_reasons": [key for key, value in checks.items() if not value] + ["actual_llm_call_forbidden_in_safe_prep_bundle"],
        "ready_for_actual_llm_one_shot_call": False,
        "gate_checks": checks,
        "openrouter_api_key_present": key_present,
        "api_key_value_logged": False,
        "approval_phrase_value_logged": False,
        "actual_llm_api_call": False,
        "llm_api_call_attempted": False,
        "llm_api_call_count": 0,
        "discord_send_allowed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }


def render_phase45_actual_llm_one_shot_preflight_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 45A Actual LLM One-shot Preflight",
            "",
            "- Default blocked: true",
            "- Actual LLM API call: false",
            "- LLM API attempt: false",
            "- Discord send allowed: false",
            f"- Ready for actual LLM one-shot call: {str(report.get('ready_for_actual_llm_one_shot_call')).lower()}",
        ]
    ) + "\n"
