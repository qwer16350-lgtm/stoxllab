"""Local review packets for read-only live Discord events."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_response_packet import llm_response_packet_preview


VERSION = "phase30_review_packet"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _date_stamp(value: str | None = None) -> str:
    return (value or utc_now())[:10].replace("-", "")


def build_live_event_review_packet(
    audit_record: dict[str, Any],
    routing_report: dict[str, Any],
    would_send_preview: dict[str, Any],
    agent_placeholder_response: dict[str, Any] | None = None,
    llm_response_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packet = {
        "packet_type": "live_event_review_packet",
        "version": VERSION,
        "created_at": utc_now(),
        "event_id": audit_record.get("event_id", ""),
        "summary": {
            "channel_name": audit_record.get("channel_name", ""),
            "workflow_role": audit_record.get("workflow_role", ""),
            "agent_route_candidate": routing_report.get("agent_route_candidate", ""),
            "decision": audit_record.get("decision", ""),
            "content_present": bool(audit_record.get("content_present")),
            "content_length": int(audit_record.get("content_length") or 0),
        },
        "audit_record": audit_record,
        "routing_report": routing_report,
        "would_send_preview": would_send_preview,
        "agent_placeholder_response": _placeholder_summary(agent_placeholder_response),
        "llm_response_packet": llm_response_packet_preview(llm_response_packet),
        "human_review": {
            "required": True,
            "reason": "Discord replies are disabled in Phase 30.",
            "allowed_actions": ["review_only", "manual_followup_outside_bot"],
            "disallowed_actions": ["auto_reply", "external_execution", "llm_call", "rag_call"],
        },
        "safety_assertions": {
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
        },
    }
    assert_live_event_review_packet_safe(packet)
    return packet


def _placeholder_summary(response: dict[str, Any] | None = None) -> dict[str, Any]:
    if not response:
        return {
            "available": False,
            "agent_route_candidate": "",
            "title": "",
            "summary": "",
            "response_path": "",
        }
    placeholder = response.get("placeholder", {})
    return {
        "available": True,
        "agent_route_candidate": response.get("agent_route_candidate", ""),
        "title": placeholder.get("title", ""),
        "summary": placeholder.get("summary", ""),
        "response_path": response.get("response_path", ""),
    }


def assert_live_event_review_packet_safe(packet: dict[str, Any]) -> None:
    safety = packet.get("safety_assertions", {})
    if safety.get("message_sent") or safety.get("external_execution") or safety.get("llm_called") or safety.get("rag_called"):
        raise ValueError("Live event review packet has unsafe execution flags.")
    text = json.dumps(packet, ensure_ascii=False).lower()
    if "sk-" in text or "xoxb-" in text or "mfa." in text or re.search(r"\b\d{15,25}\b", text):
        raise ValueError("Live event review packet contains unsafe raw values.")


def render_live_event_review_packet_markdown(packet: dict[str, Any]) -> str:
    summary = packet.get("summary", {})
    return "\n".join(
        [
            "# Live Event Review Packet",
            "",
            f"- event_id: {packet.get('event_id', '')}",
            f"- decision: {summary.get('decision', '')}",
            f"- channel_name: {summary.get('channel_name', '')}",
            f"- workflow_role: {summary.get('workflow_role', '')}",
            f"- agent_route_candidate: {summary.get('agent_route_candidate', '')}",
            f"- content_present: {summary.get('content_present')}",
            f"- content_length: {summary.get('content_length')}",
            f"- agent_placeholder_response: {str(packet.get('agent_placeholder_response', {}).get('available', False)).lower()}",
            f"- llm_response_packet: {str(packet.get('llm_response_packet', {}).get('available', False)).lower()}",
            "- message_sent: false",
            "- external_execution: false",
            "- llm_called: false",
            "- rag_called: false",
        ]
    ) + "\n"


def write_live_event_review_packet(packet: dict[str, Any], root: str | Path | None = None) -> dict[str, str]:
    assert_live_event_review_packet_safe(packet)
    repo_root = Path(root or Path.cwd()).resolve()
    out_dir = repo_root / "exports" / "hermes_gateway" / "live_event_packets" / _date_stamp(packet.get("created_at"))
    out_dir.mkdir(parents=True, exist_ok=True)
    event_id = str(packet.get("event_id") or "event").replace(":", "_")
    json_path = out_dir / f"{event_id}.json"
    md_path = out_dir / f"{event_id}.md"
    json_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_live_event_review_packet_markdown(packet), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(md_path)}
