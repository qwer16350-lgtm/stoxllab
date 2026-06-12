"""Build local approval review packets from replay results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from persistence import make_timestamped_filename, redact_sensitive_values, write_json
from replay import run_replay


HIGH_RISK_ACTIONS = {
    "grant_submit",
    "competition_submit",
    "external_email_send",
    "contract_confirm",
    "price_confirm",
    "delivery_schedule_confirm",
    "official_brand_direction_confirm",
    "external_collaboration_condition_confirm",
}
MEDIUM_RISK_ACTIONS = {"sns_publish", "homepage_upload"}
LOW_RISK_TYPES = {"sns_post_draft", "competition_search", "schedule_deadline_followup", "strategy_product_idea"}
REVIEWABLE_BLOCK_MARKERS = ("Sensitive data exposure", "secret", "API key", "password")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _packet_id(source_replay_id: str) -> str:
    seed = f"{source_replay_id}|{utc_now()}"
    return "review_packet_" + sha256(seed.encode("utf-8")).hexdigest()[:12]


def _event_by_id(replay_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {event.get("event_id"): event for event in replay_result.get("events", [])}


def _audit_refs(replay_result: dict[str, Any], event_id: str | None) -> list[str]:
    if not event_id:
        return []
    refs = []
    for audit in replay_result.get("audit_trail", []):
        if audit.get("event_id") == event_id and audit.get("audit_id"):
            refs.append(audit["audit_id"])
    return refs


def _request_summary(event: dict[str, Any]) -> str:
    text = event.get("normalized_request", {}).get("text") or ""
    return text[:160] if text else "(no request text)"


def _has_sensitive_request(event: dict[str, Any]) -> bool:
    text = (_request_summary(event) + " " + " ".join(event.get("block_reasons", []))).lower()
    return any(marker.lower() in text for marker in REVIEWABLE_BLOCK_MARKERS)


def classify_risk(action: str | None, event: dict[str, Any]) -> tuple[str, list[str]]:
    if action in HIGH_RISK_ACTIONS:
        return "high", [f"Approval-gated external or contractual action: {action}"]
    if _has_sensitive_request(event):
        return "high", ["Sensitive information request is blocked and requires rejection."]
    if action in MEDIUM_RISK_ACTIONS:
        return "medium", [f"Public-facing publish/upload action: {action}"]
    request_type = event.get("classification", {}).get("request_type")
    if request_type in LOW_RISK_TYPES:
        return "low", [f"Internal draft/review flow: {request_type}"]
    return "medium", ["Approval-related item requires manual review."]


def recommended_decision(action: str | None, event: dict[str, Any]) -> str:
    if _has_sensitive_request(event):
        return "reject"
    if action in HIGH_RISK_ACTIONS or action in MEDIUM_RISK_ACTIONS:
        return "manual_review_required"
    return "manual_review_required"


def _decision_template(item: dict[str, Any]) -> str:
    return (
        "Decision Maker note: approve/reject after checking risk reasons. "
        "Approval does not trigger external execution; a human must perform any approved external action separately."
    )


def _queue_items_for_packet(replay_result: dict[str, Any]) -> list[dict[str, Any]]:
    events = _event_by_id(replay_result)
    items: list[dict[str, Any]] = []
    for queue_item in replay_result.get("approval_queue", []):
        action = queue_item.get("requested_action")
        if not action:
            continue
        event = events.get(queue_item.get("source_event_id"), {})
        risk_level, risk_reasons = classify_risk(action, event)
        item = {
            "approval_id": queue_item.get("approval_id"),
            "source_event_id": queue_item.get("source_event_id"),
            "requested_action": action,
            "request_summary": _request_summary(event),
            "primary_agent": queue_item.get("primary_agent"),
            "reviewer_agent": queue_item.get("reviewer_agent"),
            "final_report_channel": queue_item.get("final_report_channel"),
            "status": queue_item.get("status"),
            "risk_level": risk_level,
            "risk_reasons": risk_reasons,
            "human_only_execution": True,
            "external_execution_allowed": False,
            "decision_options": ["approve", "reject"],
            "recommended_decision": recommended_decision(action, event),
            "decision_note_template": "",
            "block_reasons": list(queue_item.get("block_reasons", [])),
            "audit_refs": _audit_refs(replay_result, queue_item.get("source_event_id")),
        }
        item["decision_note_template"] = _decision_template(item)
        items.append(item)
    return items


def _blocked_sensitive_items(replay_result: dict[str, Any], existing_event_ids: set[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for event in replay_result.get("events", []):
        event_id = event.get("event_id")
        if event_id in existing_event_ids or not event.get("blocked") or not _has_sensitive_request(event):
            continue
        risk_level, risk_reasons = classify_risk(None, event)
        item = {
            "approval_id": "blocked_" + sha256(str(event_id).encode("utf-8")).hexdigest()[:12],
            "source_event_id": event_id,
            "requested_action": "sensitive_info_request",
            "request_summary": _request_summary(event),
            "primary_agent": event.get("dispatch_plan", {}).get("dispatch_to_agent"),
            "reviewer_agent": event.get("dispatch_plan", {}).get("reviewer_agent"),
            "final_report_channel": event.get("dispatch_plan", {}).get("final_report_channel"),
            "status": "blocked",
            "risk_level": risk_level,
            "risk_reasons": risk_reasons,
            "human_only_execution": True,
            "external_execution_allowed": False,
            "decision_options": ["reject"],
            "recommended_decision": "reject",
            "decision_note_template": "Reject. Do not expose tokens, API keys, passwords, or secrets.",
            "block_reasons": list(event.get("block_reasons", [])),
            "audit_refs": _audit_refs(replay_result, event_id),
        }
        items.append(item)
    return items


def redact_review_packet(packet: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_sensitive_values(packet)
    redacted["redaction_applied"] = True
    return redacted


def build_review_packet(replay_result: dict[str, Any], packet_id: str | None = None) -> dict[str, Any]:
    summary = replay_result.get("summary", {})
    if summary.get("external_execution_count", 0) != 0:
        raise ValueError("Cannot build review packet when external_execution_count is not 0")
    source_replay_id = replay_result.get("replay_id", "")
    items = _queue_items_for_packet(replay_result)
    items.extend(_blocked_sensitive_items(replay_result, {item.get("source_event_id") for item in items}))
    for item in items:
        if item.get("external_execution_allowed") is not False:
            raise ValueError("Review packet item must keep external_execution_allowed=false")
    packet = {
        "packet_id": packet_id or _packet_id(source_replay_id),
        "packet_type": "approval_review_packet",
        "created_at": utc_now(),
        "source_replay_id": source_replay_id,
        "summary": {
            "total_events": replay_result.get("events_processed", len(replay_result.get("events", []))),
            "blocked_count": summary.get("blocked_count", 0),
            "approval_required_count": summary.get("approval_required_count", 0),
            "pending_count": sum(1 for item in replay_result.get("approval_queue", []) if item.get("status") == "pending"),
            "approved_count": summary.get("approved_count", 0),
            "rejected_count": summary.get("rejected_count", 0),
            "human_only_execution_count": summary.get("human_only_execution_count", 0),
            "external_execution_count": summary.get("external_execution_count", 0),
        },
        "decision_maker_notice": (
            "This packet is for review only. It is not a Discord button/message UI, "
            "and approval does not trigger SNS posting, homepage upload, grant submission, email, or contract execution."
        ),
        "items": items,
        "safety_assertions": list(replay_result.get("safety_assertions", [])),
        "recommended_actions": [
            "Review each high/medium risk item manually.",
            "Reject any sensitive information request.",
            "Keep approved external actions human-only.",
        ],
        "redaction_applied": True,
    }
    return redact_review_packet(packet)


def build_review_packet_from_replay_file(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    return build_review_packet(data)


def _md_list(items: list[Any]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def render_review_packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# STOXL Approval Review Packet",
        "",
        "## Summary",
    ]
    for key, value in packet.get("summary", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Decision Maker Notice",
            "",
            packet.get("decision_maker_notice", ""),
            "",
            "## Pending / Decided Items",
        ]
    )
    for item in packet.get("items", []):
        lines.extend(
            [
                "",
                f"### Item: {item.get('approval_id')}",
                "",
                f"- Requested action: {item.get('requested_action')}",
                f"- Source event: {item.get('source_event_id')}",
                f"- Primary agent: {item.get('primary_agent')}",
                f"- Reviewer: {item.get('reviewer_agent')}",
                f"- Final report channel: {item.get('final_report_channel')}",
                f"- Status: {item.get('status')}",
                f"- Risk level: {item.get('risk_level')}",
                "- Risk reasons:",
                _md_list(item.get("risk_reasons", [])),
                f"- Human-only execution: {item.get('human_only_execution')}",
                f"- External execution allowed: {item.get('external_execution_allowed')}",
                f"- Recommended decision: {item.get('recommended_decision')}",
                f"- Decision note template: {item.get('decision_note_template')}",
            ]
        )
    lines.extend(["", "## Safety Assertions"])
    for assertion in packet.get("safety_assertions", []):
        lines.append(f"- {assertion.get('rule')}: {assertion.get('passed')}")
    lines.extend(
        [
            "",
            "## What This Packet Does Not Do",
            "",
            "- This packet is for review only.",
            "- It is not an approval button or real Discord message.",
            "- Approval does not automatically trigger external execution.",
            "- SNS posting, homepage upload, grant submission, email sending, and contract confirmation must be performed separately by a human.",
        ]
    )
    return "\n".join(lines) + "\n"


def export_review_packet(
    packet: dict[str, Any],
    export_root: str | Path,
    formats: tuple[str, ...] = ("json", "md"),
    dry_run: bool = False,
) -> dict[str, Any]:
    root = Path(export_root)
    root.mkdir(parents=True, exist_ok=True) if not dry_run else None
    base_name = make_timestamped_filename(packet.get("packet_id", "review_packet"), "").rstrip(".")
    json_path = root / f"{base_name}.json"
    md_path = root / f"{base_name}.md"
    summary = {
        "exported": not dry_run,
        "dry_run": dry_run,
        "export_root": str(root),
        "json_path": str(json_path) if "json" in formats else None,
        "markdown_path": str(md_path) if "md" in formats else None,
        "formats": list(formats),
        "redaction_applied": True,
        "external_execution_count": packet.get("summary", {}).get("external_execution_count", 0),
        "human_only_execution_preserved": all(item.get("human_only_execution") is True for item in packet.get("items", [])),
    }
    if summary["external_execution_count"] != 0:
        raise ValueError("Cannot export review packet when external_execution_count is not 0")
    if dry_run:
        return summary
    if "json" in formats:
        write_json(json_path, packet, overwrite=False)
    if "md" in formats:
        md_path.write_text(render_review_packet_markdown(packet), encoding="utf-8")
    return summary


def build_packet_from_replay_paths(events_path: str | Path, actions_path: str | Path | None = None) -> dict[str, Any]:
    return build_review_packet(run_replay(events_path, actions_path))
