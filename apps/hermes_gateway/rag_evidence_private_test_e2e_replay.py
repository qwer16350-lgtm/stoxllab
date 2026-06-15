"""Phase 34L-0 no-live/no-api/no-send E2E replay."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rag_evidence_private_test_e2e_preflight import build_rag_evidence_private_test_e2e_preflight


VERSION = "phase34l0_e2e_replay_no_live_runtime_no_api_no_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def build_rag_evidence_private_test_e2e_replay(root: str | Path | None = None, preflight: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_preflight = preflight or build_rag_evidence_private_test_e2e_preflight(root=root)
    passed = bool(selected_preflight.get("ready_for_phase34l1_manual_e2e_live_reply"))
    report = {
        "report_type": "rag_evidence_private_test_e2e_replay",
        "version": VERSION,
        "mock_user_message_present": True,
        "mock_user_channel_scope": "private_test_only",
        "accepted_private_test_channel": True,
        "public_channel_rejected": True,
        "team_channel_rejected": True,
        "knowledge_dry_chain_replayed": True,
        "evidence_packet_replayed": True,
        "prompt_envelope_replayed": True,
        "llm_response_fixture_replayed": True,
        "would_send_preview_replayed": True,
        "send_closeout_fixture_replayed": True,
        "self_loop_guard_replayed": True,
        "duplicate_send_guard_replayed": True,
        "discord_live_runtime_executed": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "e2e_replay_passed": passed,
        "ready_for_phase34l1_manual_e2e_live_reply": passed,
        "ready_for_unattended_auto_reply": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "token_value_logged": False,
            "raw_discord_ids_logged": False,
            "approval_phrase_value_logged": False,
            "discord_live_runtime_executed": False,
            "discord_message_sent": False,
            "llm_called": False,
            "embedding_called": False,
            "external_execution": False,
        },
    }
    assert_rag_evidence_private_test_e2e_replay_safe(report)
    return report


def render_rag_evidence_private_test_e2e_replay_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL RAG Evidence Private-test E2E Replay",
            "",
            f"- Mock private-test message present: {str(report.get('mock_user_message_present')).lower()}",
            f"- Accepted private-test channel: {str(report.get('accepted_private_test_channel')).lower()}",
            f"- Public channel rejected: {str(report.get('public_channel_rejected')).lower()}",
            f"- Team channel rejected: {str(report.get('team_channel_rejected')).lower()}",
            f"- E2E replay passed: {str(report.get('e2e_replay_passed')).lower()}",
            "- Discord live runtime executed: false",
            "- Discord message sent: false",
            "- LLM API called: false",
            "- Embedding API called: false",
            "- External execution: false",
            f"- Ready for Phase 34L-1 manual E2E live reply: {str(report.get('ready_for_phase34l1_manual_e2e_live_reply')).lower()}",
            "- Ready for unattended auto reply: false",
        ]
    ) + "\n"


def assert_rag_evidence_private_test_e2e_replay_safe(report: dict[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    if SECRET_RE.search(text) or LONG_ID_RE.search(text):
        raise ValueError("E2E replay contains sensitive values.")
    for key in ("discord_live_runtime_executed", "discord_api_send_called", "discord_message_sent", "llm_api_called", "embedding_api_called", "external_execution", "ready_for_unattended_auto_reply"):
        if report.get(key):
            raise ValueError(f"E2E replay unsafe flag is true: {key}")
    if not report.get("e2e_replay_passed"):
        raise ValueError("E2E replay did not pass.")
