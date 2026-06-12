"""Audit-only live capture skeleton with no live Gateway."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from audit_log import build_audit_payload
from discord_adapter_stub import evaluate_discord_raw_event, build_dispatch_from_evaluation


def build_live_capture_config(root: str | Path) -> dict[str, Any]:
    return {
        "capture_mode": "audit_only_stub",
        "root": str(Path(root).resolve()),
        "live_gateway_enabled": False,
        "persist_without_explicit_export": False,
        "message_send_enabled": False,
    }


def capture_event_audit_only(raw_event: dict[str, Any], root: str | Path | None = None) -> dict[str, Any]:
    evaluation = evaluate_discord_raw_event(raw_event, root=root)
    dispatch_plan = build_dispatch_from_evaluation(evaluation)
    audit_payload = build_audit_payload(
        raw_event.get("event_type", "live_capture_stub_event"),
        evaluation["normalized_request"],
        evaluation["evaluator_result"],
        dispatch_plan,
        event_id=raw_event.get("event_id"),
    )
    return {
        "capture_mode": "audit_only_stub",
        "live_event_received": False,
        "audit_payload_built": True,
        "audit_payload": audit_payload,
        "message_sent": False,
        "external_execution_count": 0,
        "safety_assertions": {
            "discord_api_called": False,
            "gateway_connected": False,
            "message_sent": False,
            "llm_called": False,
            "rag_called": False,
            "external_execution_enabled": False,
        },
    }


def build_live_capture_stub_report(root: str | Path) -> dict[str, Any]:
    return {
        "report_type": "live_capture_audit_only_stub",
        "version": "phase25_no_live_gateway",
        "capture_mode": "audit_only_stub",
        "live_event_received": False,
        "audit_payload_built": False,
        "message_sent": False,
        "external_execution_count": 0,
        "safety_assertions": {
            "discord_api_called": False,
            "gateway_connected": False,
            "message_sent": False,
            "llm_called": False,
            "rag_called": False,
            "external_execution_enabled": False,
        },
    }
