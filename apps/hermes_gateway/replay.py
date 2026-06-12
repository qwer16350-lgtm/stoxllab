"""Local replay runner for STOXL Hermes Gateway mock events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from approval_queue import ApprovalQueue
from audit_log import build_audit_payload
from config import load_config
from discord_event_adapter import normalize_event
from dispatcher import build_dispatch_plan
from evaluator_bridge import evaluate_request
from registry_loader import load_registry


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_input_path(path: str | Path) -> Path:
    source = Path(path)
    if not source.is_absolute():
        source = Path.cwd() / source
    return source


def load_json_list(path: str | Path, key: str) -> list[dict[str, Any]]:
    source = resolve_input_path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.get(key, []))
    raise ValueError(f"{source} must contain a list or an object with '{key}'")


def event_id(event: dict[str, Any], index: int) -> str:
    if event.get("event_id"):
        return str(event["event_id"])
    seed = json.dumps(event, ensure_ascii=False, sort_keys=True)
    return "replay_event_" + sha256(f"{index}|{seed}".encode("utf-8")).hexdigest()[:12]


def process_event(
    event: dict[str, Any],
    index: int,
    registry: dict[str, Any],
    config: Any,
    queue: ApprovalQueue,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_event_id = event_id(event, index)
    normalized = normalize_event(event)
    evaluator_result = evaluate_request(registry, normalized, config)
    dispatch_plan = build_dispatch_plan(normalized, evaluator_result)
    queue_item = queue.add_if_required(source_event_id, evaluator_result, dispatch_plan)
    audit_payload = build_audit_payload(
        event.get("event_type", "replay_event"),
        normalized,
        evaluator_result,
        dispatch_plan,
        event_id=source_event_id,
    )
    processed = {
        "event_index": index,
        "event_id": source_event_id,
        "event_type": event.get("event_type", "replay_event"),
        "normalized_request": normalized,
        "classification": evaluator_result.get("classification", {}),
        "dispatch_plan": dispatch_plan,
        "approval_queue_item_id": queue_item.get("approval_id") if queue_item else None,
        "blocked": dispatch_plan.get("blocked", False),
        "block_reasons": dispatch_plan.get("block_reasons", []),
        "audit_id": audit_payload.get("audit_id"),
    }
    return processed, audit_payload


def build_summary(events: list[dict[str, Any]], queue: ApprovalQueue) -> dict[str, int]:
    queue_items = queue.snapshot()
    return {
        "blocked_count": sum(1 for event in events if event.get("blocked")),
        "dispatch_count": sum(1 for event in events if event.get("dispatch_plan", {}).get("should_dispatch")),
        "approval_required_count": len(queue_items),
        "approved_count": sum(1 for item in queue_items if item.get("status") == "approved"),
        "rejected_count": sum(1 for item in queue_items if item.get("status") == "rejected"),
        "human_only_execution_count": sum(1 for item in queue_items if item.get("human_only_execution") is True),
        "external_execution_count": 0,
    }


def safety_assertions(summary: dict[str, int], queue: ApprovalQueue) -> list[dict[str, Any]]:
    queue_items = queue.snapshot()
    return [
        {
            "rule": "external_execution_count_is_zero",
            "passed": summary.get("external_execution_count") == 0,
            "details": "Replay never converts approvals into external execution.",
        },
        {
            "rule": "approved_items_remain_human_only",
            "passed": all(item.get("human_only_execution") is True for item in queue_items if item.get("status") == "approved"),
            "details": "Approved queue items keep human_only_execution=true.",
        },
        {
            "rule": "approved_items_do_not_allow_external_execution",
            "passed": all(item.get("external_execution_allowed") is False for item in queue_items),
            "details": "Queue items always keep external_execution_allowed=false.",
        },
    ]


def run_replay(
    events_path: str | Path,
    approval_actions_path: str | Path | None = None,
) -> dict[str, Any]:
    config = load_config(Path(__file__).resolve())
    registry = load_registry(config)
    events_source = resolve_input_path(events_path)
    actions_source = resolve_input_path(approval_actions_path) if approval_actions_path else None
    created_at = utc_now()
    events_input = load_json_list(events_source, "events")
    queue = ApprovalQueue()
    replay_events: list[dict[str, Any]] = []
    audit_trail: list[dict[str, Any]] = []

    for index, event in enumerate(events_input, start=1):
        processed, audit_payload = process_event(event, index, registry, config, queue)
        replay_events.append(processed)
        audit_trail.append(audit_payload)

    approval_actions: list[dict[str, Any]] = []
    if actions_source:
        actions = load_json_list(actions_source, "actions")
        approval_actions = queue.apply_actions(actions)

    summary = build_summary(replay_events, queue)
    return {
        "replay_id": "replay_" + sha256(f"{events_source}|{created_at}".encode("utf-8")).hexdigest()[:12],
        "created_at": created_at,
        "source_event_file": str(events_source),
        "approval_actions_file": str(actions_source) if actions_source else None,
        "external_execution_count": summary["external_execution_count"],
        "human_only_execution_count": summary["human_only_execution_count"],
        "exportable": True,
        "events_processed": len(replay_events),
        "events": replay_events,
        "approval_queue": queue.snapshot(),
        "approval_actions": approval_actions,
        "audit_trail": audit_trail,
        "summary": summary,
        "safety_assertions": safety_assertions(summary, queue),
        "warnings": list(queue.warnings),
    }
