"""Phase 33D live readiness review without live execution."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from rag_context_safety import build_rag_context_safety_report
from rag_llm_private_test_reply import build_rag_llm_private_test_reply_preflight
from rag_llm_private_test_reply_replay import build_rag_llm_private_test_reply_replay_report
from rag_llm_prompt_envelope import build_rag_llm_prompt_envelope
from rag_llm_would_send_preview import build_rag_llm_would_send_preview
from rag_local_retrieval import run_rag_local_retrieval
from rag_preflight import build_rag_preflight_report
from rag_response_packet import build_rag_response_packet


VERSION = "phase33d_review_no_live_execution"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")

MANUAL_ENABLE_CHECKLIST = [
    "Confirm Phase 33D is manually approved.",
    "Confirm only private test channel is allowed.",
    "Confirm private test channel ID is configured.",
    "Confirm source is canonical: operation, not operations.",
    "Confirm local read-only retrieval only.",
    "Confirm max documents and max context chars are enforced.",
    "Confirm RAG response packet is required.",
    "Confirm LLM output safety is required.",
    "Confirm cooldown, max replies, duplicate guard, and circuit breaker are active.",
    "Confirm public/team channel reply is blocked before retrieval.",
    "Confirm self/bot message is blocked before retrieval.",
    "Confirm Discord send gates are false by default.",
    "Confirm rollback commands are available.",
]

ROLLBACK_CHECKLIST = [
    '$env:HERMES_DISCORD_SEND_MESSAGES="false"',
    '$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"',
    '$env:HERMES_LLM_DISCORD_SEND_ENABLED="false"',
    '$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"',
    '$env:HERMES_DISCORD_RAG_ENABLED="false"',
    '$env:HERMES_LLM_RAG_ENABLED="false"',
    '$env:HERMES_RAG_LLM_REPLY_ENABLED="false"',
    "Stop any live runtime with Ctrl+C.",
    "Open the circuit breaker after rate-limit or send exceptions.",
    "Do not inspect token/API key values in logs.",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_rag_llm_live_readiness_review(root: str | None = None) -> dict[str, Any]:
    rag_preflight = build_rag_preflight_report()
    retrieval = run_rag_local_retrieval(root=root, source="operation", query="STOXL brand tone")
    packet = build_rag_response_packet(retrieval)
    context = build_rag_context_safety_report(retrieval)
    preflight = build_rag_llm_private_test_reply_preflight(root=root)
    envelope = build_rag_llm_prompt_envelope(root=root)
    preview = build_rag_llm_would_send_preview(root=root)
    replay = build_rag_llm_private_test_reply_replay_report(root=root)
    report = {
        "report_type": "rag_llm_live_readiness_review",
        "version": VERSION,
        "created_at": utc_now(),
        "go": False,
        "no_go_reasons": [
            "manual_approval_required",
            "live_runtime_not_enabled_by_review_phase",
        ],
        "ready_components": {
            "rag_preflight": bool(rag_preflight.get("ready_for_phase33b_local_readonly_retrieval")),
            "local_readonly_retrieval": bool(retrieval.get("local_read_only")),
            "rag_response_packet": bool(packet.get("response_available")),
            "rag_context_safety": bool(context),
            "rag_llm_prompt_envelope": bool(envelope),
            "rag_llm_would_send_preview": bool(preview),
            "rag_llm_replay": bool(replay.get("ready_for_phase33d_live_review")),
        },
        "required_live_gates": {
            "private_test_channel_id_required": True,
            "channel_id_match_required": True,
            "source_validation_required": True,
            "rag_context_safety_required": True,
            "rag_response_packet_required": True,
            "llm_output_safety_required": True,
            "cooldown_required": True,
            "budget_required": True,
            "circuit_breaker_required": True,
            "manual_env_enable_required": True,
        },
        "forbidden_live_scope": {
            "public_team_channel_reply": True,
            "source_operations": True,
            "channel_name_only_allow": True,
            "external_execution": True,
            "embedding_api": True,
            "unbounded_context": True,
        },
        "manual_enable_checklist": MANUAL_ENABLE_CHECKLIST,
        "rollback_checklist": ROLLBACK_CHECKLIST,
        "actual_discord_send": False,
        "actual_llm_api_call": False,
        "embedding_api_called": False,
        "external_execution": False,
        "ready_for_manual_phase33d_implementation_request": True,
        "safety_assertions": {
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
    }
    assert_live_readiness_report_safe(report)
    return report


def render_rag_llm_live_readiness_markdown(report: dict[str, Any]) -> str:
    components = report.get("ready_components", {})
    gates = report.get("required_live_gates", {})
    forbidden = report.get("forbidden_live_scope", {})
    lines = [
        "# STOXL RAG+LLM Live Readiness Review",
        "",
        f"- Go: {str(report.get('go')).lower()}",
        f"- Ready for manual implementation request: {str(report.get('ready_for_manual_phase33d_implementation_request')).lower()}",
        f"- No-go reasons: {', '.join(report.get('no_go_reasons', []))}",
        "- Actual Discord send: false",
        "- Actual LLM API call: false",
        "- Embedding API called: false",
        "- External execution: false",
        "",
        "## Ready Components",
    ]
    lines.extend(f"- {key}: {str(value).lower()}" for key, value in components.items())
    lines.extend(["", "## Required Live Gates"])
    lines.extend(f"- {key}: {str(value).lower()}" for key, value in gates.items())
    lines.extend(["", "## Forbidden Live Scope"])
    lines.extend(f"- {key}: {str(value).lower()}" for key, value in forbidden.items())
    lines.extend(["", "## Manual Enable Checklist"])
    lines.extend(f"{index}. {item}" for index, item in enumerate(report.get("manual_enable_checklist", []), start=1))
    lines.extend(["", "## Rollback Checklist"])
    lines.extend(f"- `{item}`" if item.startswith("$env:") else f"- {item}" for item in report.get("rollback_checklist", []))
    return "\n".join(lines) + "\n"


def assert_live_readiness_report_safe(report: Any) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("Live readiness report contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("Live readiness report contains raw Discord-like IDs.")
    if isinstance(report, dict):
        for key in ("go", "actual_discord_send", "actual_llm_api_call", "embedding_api_called", "external_execution"):
            if report.get(key):
                raise ValueError(f"Live readiness unsafe flag is true: {key}")
        safety = report.get("safety_assertions", {})
        for key in ("embedding_called", "llm_called", "discord_message_sent", "external_execution"):
            if safety.get(key):
                raise ValueError(f"Live readiness unsafe assertion is true: {key}")
