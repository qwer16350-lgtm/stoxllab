"""Deterministic would-send previews that never send."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "phase30_no_send"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _date_stamp(value: str | None = None) -> str:
    return (value or utc_now())[:10].replace("-", "")


def _kind(audit_record: dict[str, Any], routing_report: dict[str, Any]) -> str:
    if audit_record.get("decision", "").startswith("ignored_") or audit_record.get("decision") == "content_unavailable_or_empty":
        return "ignored_event"
    if routing_report.get("approval_relevant"):
        return "needs_decision_maker_approval"
    if routing_report.get("senior_review_required"):
        return "needs_senior_review"
    if routing_report.get("agent_route_candidate") == "unrouted":
        return "acknowledge_received"
    return "route_to_agent"


def build_would_send_preview(
    audit_record: dict[str, Any],
    routing_report: dict[str, Any],
    agent_placeholder_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agent = routing_report.get("agent_route_candidate", "unrouted")
    channel = audit_record.get("channel_name", "")
    kind = _kind(audit_record, routing_report)
    preview = {
        "preview_type": "would_send_preview",
        "version": VERSION,
        "created_at": utc_now(),
        "event_id": audit_record.get("event_id", ""),
        "agent_route_candidate": agent,
        "target_channel_name": channel,
        "would_send_kind": kind,
        "content_preview": f"[NO SEND] Received live event in {channel}. Candidate route: {agent}. Reply generation is disabled.",
        "will_send": False,
        "requires_manual_enable": True,
        "requires_future_reply_phase": True,
        "message_sent": False,
        "llm_called": False,
        "rag_called": False,
        "external_execution": False,
        "agent_placeholder_response": _placeholder_summary(agent_placeholder_response),
        "safety_assertions": {
            "discord_api_write_called": False,
            "message_sent": False,
            "llm_called": False,
            "rag_called": False,
            "external_execution": False,
        },
    }
    assert_would_send_preview_safe(preview)
    return preview


def _placeholder_summary(response: dict[str, Any] | None = None) -> dict[str, Any]:
    if not response:
        return {"available": False, "response_path": "", "title": "", "summary": ""}
    placeholder = response.get("placeholder", {})
    return {
        "available": True,
        "response_path": response.get("response_path", ""),
        "title": placeholder.get("title", ""),
        "summary": placeholder.get("summary", ""),
    }


def assert_would_send_preview_safe(preview: dict[str, Any]) -> None:
    if preview.get("will_send") or preview.get("message_sent") or preview.get("llm_called") or preview.get("rag_called") or preview.get("external_execution"):
        raise ValueError("Would-send preview has unsafe execution flags.")
    text = json.dumps(preview, ensure_ascii=False).lower()
    if "sk-" in text or "xoxb-" in text or "mfa." in text or re.search(r"\b\d{15,25}\b", text):
        raise ValueError("Would-send preview contains unsafe raw values.")


def write_would_send_preview(preview: dict[str, Any], root: str | Path | None = None) -> Path:
    assert_would_send_preview_safe(preview)
    repo_root = Path(root or Path.cwd()).resolve()
    out_dir = repo_root / "exports" / "hermes_gateway" / "would_send_previews" / _date_stamp(preview.get("created_at"))
    out_dir.mkdir(parents=True, exist_ok=True)
    event_id = str(preview.get("event_id") or "event").replace(":", "_")
    path = out_dir / f"{event_id}.json"
    path.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
