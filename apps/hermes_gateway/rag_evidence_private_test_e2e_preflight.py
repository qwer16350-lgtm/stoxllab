"""Phase 34K private-test E2E preflight without live runtime."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from knowledge_dry_chain import build_knowledge_dry_chain_report
from rag_evidence_llm_dry_call_closeout import build_rag_evidence_llm_dry_call_closeout
from rag_evidence_private_test_send_closeout import build_rag_evidence_private_test_send_closeout
from rag_evidence_private_test_send_preflight import build_rag_evidence_private_test_send_preflight
from rag_evidence_prompt_envelope import build_rag_evidence_prompt_envelope
from rag_evidence_would_send_preview import build_rag_evidence_would_send_preview


VERSION = "phase34k_e2e_preflight_no_live_runtime"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def build_rag_evidence_private_test_e2e_preflight(
    root: str | Path | None = None,
    send_closeout: dict[str, Any] | None = None,
    knowledge_dry_chain: dict[str, Any] | None = None,
    prompt_envelope: dict[str, Any] | None = None,
    llm_dry_call_closeout: dict[str, Any] | None = None,
    would_send_preview: dict[str, Any] | None = None,
    private_test_send_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_send_closeout = send_closeout or build_rag_evidence_private_test_send_closeout()
    selected_knowledge = knowledge_dry_chain or build_knowledge_dry_chain_report(root=root)
    selected_prompt = prompt_envelope or build_rag_evidence_prompt_envelope(root=root)
    selected_llm_closeout = llm_dry_call_closeout or build_rag_evidence_llm_dry_call_closeout()
    selected_preview = would_send_preview or build_rag_evidence_would_send_preview(selected_llm_closeout)
    selected_send_preflight = private_test_send_preflight or build_rag_evidence_private_test_send_preflight(selected_preview)
    ready = bool(
        selected_send_closeout.get("closeout_passed")
        and selected_knowledge.get("ready_for_llm_prompt") is False
        and selected_prompt.get("ready_for_prompt_preview")
        and selected_llm_closeout.get("closeout_passed")
        and selected_preview.get("would_send_preview_created")
        and selected_send_preflight.get("would_send_preview_available")
    )
    report = {
        "report_type": "rag_evidence_private_test_e2e_preflight",
        "version": VERSION,
        "send_closeout_available": bool(selected_send_closeout.get("closeout_passed")),
        "knowledge_dry_chain_available": bool(selected_knowledge),
        "prompt_envelope_available": bool(selected_prompt.get("prompt_envelope_created")),
        "llm_dry_call_closeout_available": bool(selected_llm_closeout.get("closeout_passed")),
        "would_send_preview_available": bool(selected_preview.get("would_send_preview_created")),
        "private_test_send_preflight_available": bool(selected_send_preflight),
        "private_test_channel_only": True,
        "public_channel_reply_allowed": False,
        "team_channel_reply_allowed": False,
        "manual_approval_required_for_llm": True,
        "manual_approval_required_for_send": True,
        "discord_live_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "ready_for_phase34l1_manual_e2e_live_reply": ready,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "public_channel_reply_called": False,
            "team_channel_reply_called": False,
            "discord_live_runtime_executed": False,
            "discord_message_sent": False,
            "llm_called": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_private_test_e2e_preflight_safe(report)
    return report


def render_rag_evidence_private_test_e2e_preflight_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test E2E Preflight",
            "",
            f"- Send closeout available: {str(report.get('send_closeout_available')).lower()}",
            f"- Knowledge dry chain available: {str(report.get('knowledge_dry_chain_available')).lower()}",
            f"- Prompt envelope available: {str(report.get('prompt_envelope_available')).lower()}",
            f"- LLM dry call closeout available: {str(report.get('llm_dry_call_closeout_available')).lower()}",
            f"- Would-send preview available: {str(report.get('would_send_preview_available')).lower()}",
            f"- Private-test send preflight available: {str(report.get('private_test_send_preflight_available')).lower()}",
            "- Discord live runtime executed: false",
            "- Discord message sent: false",
            "- LLM API called: false",
            "- Embedding API called: false",
            "- External execution: false",
            f"- Ready for Phase 34L-1 manual E2E live reply: {str(report.get('ready_for_phase34l1_manual_e2e_live_reply')).lower()}",
            "- Ready for unattended auto reply: false",
        ]
    ) + "\n"


def assert_rag_evidence_private_test_e2e_preflight_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text) or LONG_ID_RE.search(text):
        raise ValueError("E2E preflight contains sensitive values.")
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "discord_live_runtime_executed", "discord_api_send_called", "discord_message_sent", "llm_api_called", "embedding_api_called", "external_execution", "ready_for_unattended_auto_reply"):
        if report.get(key):
            raise ValueError(f"E2E preflight unsafe flag is true: {key}")
    if not report.get("ready_for_phase34l1_manual_e2e_live_reply"):
        raise ValueError("E2E preflight is not ready for manual Phase 34L-1.")
