"""Local replay runner for Discord-shaped raw event JSON.

This module extends the Phase 18 adapter stub into a batch replay runner. It
does not connect to Discord, send messages, import Discord SDKs, or convert any
approval into external execution.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from approval_queue import ApprovalQueue
from audit_log import build_audit_payload
from discord_adapter_stub import load_raw_events, run_discord_adapter_stub
from persistence import redact_sensitive_values


KNOWN_CHANNELS = {
    "공지-결정사항",
    "대표-회의실",
    "최종-승인요청",
    "marketing-brief",
    "lucy-검토",
    "marin-초안",
    "sns-콘텐츠",
    "homepage",
    "operation-brief",
    "meiko-검토",
    "kasumi-리서치",
    "공모전-지원사업",
    "일정-마감관리",
    "reze-전략기획",
    "brand-rag",
    "new-business",
    "product-ideas",
    "완료된-안건",
    "보류된-안건",
    "폐기된-안건",
    "marin-珥덉븞",
    "sns-肄섑뀗痢?",
    "lucy-寃??",
    "kasumi-由ъ꽌移?",
    "怨듬え??吏?먯궗??",
    "?쇱젙-留덇컧愿由?",
    "meiko-寃??",
    "reze-?꾨왂湲고쉷",
    "????뚯쓽??",
    "理쒖쥌-?뱀씤?붿껌",
}
SECRET_MARKERS = ("api key", "apikey", "token", "secret", "password", "sk-", "bearer")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_discord_raw_events(path: str | Path) -> list[dict[str, Any]]:
    return load_raw_events(path)


def _event_id(raw_event: dict[str, Any], index: int) -> str:
    if raw_event.get("event_id"):
        return str(raw_event["event_id"])
    seed = json.dumps(raw_event, ensure_ascii=False, sort_keys=True)
    return "discord_event_" + sha256(f"{index}|{seed}".encode("utf-8")).hexdigest()[:12]


def _preview(text: str, limit: int = 80) -> str:
    safe = redact_sensitive_values(text or "")
    if not isinstance(safe, str):
        safe = "[REDACTED]"
    return safe[:limit]


def _contains_secret(payload: Any) -> bool:
    if isinstance(payload, dict):
        return any(_contains_secret(value) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_secret(item) for item in payload)
    if isinstance(payload, str):
        lower = payload.lower()
        return any(marker in lower for marker in SECRET_MARKERS)
    return False


def _raw_event_summary(raw_event: dict[str, Any]) -> dict[str, Any]:
    author = raw_event.get("author", {})
    guild_id = raw_event.get("guild_id")
    text = raw_event.get("content") or raw_event.get("message_text") or raw_event.get("text") or ""
    return {
        "event_type": raw_event.get("event_type"),
        "guild_id_placeholder": bool(isinstance(guild_id, str) and guild_id.startswith("TODO_")),
        "channel_name": raw_event.get("channel_name") or raw_event.get("channel"),
        "category_name": raw_event.get("category_name") or raw_event.get("channel_category"),
        "author_display_name": author.get("display_name") or raw_event.get("author_display_name"),
        "author_role": (author.get("roles") or [raw_event.get("author_role") or ""])[0],
        "content_preview": _preview(text),
        "attachment_count": len(raw_event.get("attachments", [])),
        "timestamp": raw_event.get("timestamp"),
    }


def _apply_replay_guardrails(event_result: dict[str, Any]) -> None:
    channel_name = event_result.get("normalized_request", {}).get("source_channel")
    actor_agent = event_result.get("normalized_request", {}).get("actor_agent")
    dispatch_plan = event_result.get("dispatch_plan", {})
    evaluator_result = event_result.get("evaluator_result", {})
    if channel_name not in KNOWN_CHANNELS:
        reason = f"Unknown Discord channel for local replay: {channel_name}"
        dispatch_plan["blocked"] = True
        dispatch_plan["should_dispatch"] = False
        dispatch_plan["human_only_execution"] = True
        dispatch_plan["block_reasons"] = list(dict.fromkeys(list(dispatch_plan.get("block_reasons", [])) + [reason]))
        evaluator_result["blocked"] = True
        evaluator_result["block_reasons"] = list(dict.fromkeys(list(evaluator_result.get("block_reasons", [])) + [reason]))
    if channel_name in {"최종-승인요청", "理쒖쥌-?뱀씤?붿껌"} and actor_agent in {"marin", "kasumi"}:
        reason = f"Junior agent direct approval shortcut is forbidden: {actor_agent}"
        dispatch_plan["blocked"] = True
        dispatch_plan["should_dispatch"] = False
        dispatch_plan["human_only_execution"] = True
        dispatch_plan["block_reasons"] = list(dict.fromkeys(list(dispatch_plan.get("block_reasons", [])) + [reason]))
        evaluator_result["blocked"] = True
        evaluator_result["block_reasons"] = list(dict.fromkeys(list(evaluator_result.get("block_reasons", [])) + [reason]))
    payload = event_result.get("would_send_payload", {})
    payload.setdefault("safety", {})
    if dispatch_plan.get("blocked") and payload.get("message_kind") == "agent_dispatch":
        payload["message_kind"] = "blocked_request"
        payload["target_channel"] = channel_name
        payload["content"] = "Request blocked by local Discord replay guardrails. No Discord message is sent."
        payload.setdefault("metadata", {})
        payload["metadata"]["blocked"] = True
        payload["metadata"]["block_reasons"] = list(dispatch_plan.get("block_reasons", []))
    payload["safety"]["discord_api_called"] = False
    payload["safety"]["message_sent"] = False
    payload["safety"]["external_execution"] = False
    payload["safety"]["human_only_execution"] = True


def _process_one(
    raw_event: dict[str, Any],
    index: int,
    queue: ApprovalQueue,
    root: str | Path | None,
) -> dict[str, Any]:
    source_event_id = _event_id(raw_event, index)
    adapter_result = run_discord_adapter_stub(raw_event, root=root)
    normalized = adapter_result["normalized_request"]
    evaluator_result = adapter_result["evaluator_result"]
    dispatch_plan = adapter_result["dispatch_plan"]
    event_result = {
        "event_index": index,
        "event_id": source_event_id,
        "raw_event_summary": _raw_event_summary(raw_event),
        "normalized_request": normalized,
        "evaluator_result": evaluator_result,
        "classification": evaluator_result.get("classification", {}),
        "dispatch_plan": dispatch_plan,
        "would_send_payload": adapter_result["would_send_payload"],
        "approval_queue_item": None,
        "audit_payload": {},
        "blocked": bool(dispatch_plan.get("blocked")),
        "block_reasons": list(dispatch_plan.get("block_reasons", [])),
        "notes": list(evaluator_result.get("notes", [])),
    }
    _apply_replay_guardrails(event_result)
    dispatch_plan = event_result["dispatch_plan"]
    evaluator_result = event_result["evaluator_result"]
    queue_item = queue.add_if_required(source_event_id, evaluator_result, dispatch_plan)
    event_result["approval_queue_item"] = queue_item
    audit_payload = build_audit_payload(
        raw_event.get("event_type", "discord_raw_event"),
        normalized,
        evaluator_result,
        dispatch_plan,
        event_id=source_event_id,
    )
    event_result["audit_payload"] = audit_payload
    event_result["blocked"] = bool(dispatch_plan.get("blocked"))
    event_result["block_reasons"] = list(dispatch_plan.get("block_reasons", []))
    return redact_sensitive_values(event_result)


def apply_discord_replay_approval_actions(
    replay_result: dict[str, Any],
    approval_actions: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    if not approval_actions:
        return applied
    queue_items = replay_result.get("approval_queue", [])
    for action in approval_actions:
        match = None
        for item in queue_items:
            if item.get("approval_id") == action.get("approval_id") or item.get("source_event_id") == action.get("source_event_id"):
                match = item
                break
        result = {
            "action": redact_sensitive_values(dict(action)),
            "applied": False,
            "warning": None,
            "approval_id": action.get("approval_id"),
            "source_event_id": action.get("source_event_id"),
            "status_after": None,
        }
        if action.get("decision_role") != "Decision Maker":
            result["warning"] = "Only Decision Maker role can approve or reject"
        elif action.get("decision") not in {"approve", "reject"}:
            result["warning"] = f"Unknown approval decision: {action.get('decision')}"
        elif not match:
            result["warning"] = "Unknown approval_id or source_event_id"
        else:
            match["status"] = "approved" if action.get("decision") == "approve" else "rejected"
            match["decided_at"] = action.get("decided_at") or utc_now()
            match["decision_by"] = action.get("decision_by")
            match["decision_note"] = action.get("decision_note")
            match["human_only_execution"] = True
            match["external_execution_allowed"] = False
            result["applied"] = True
            result["approval_id"] = match.get("approval_id")
            result["source_event_id"] = match.get("source_event_id")
            result["status_after"] = match.get("status")
        applied.append(result)
    replay_result["approval_actions"] = applied
    return applied


def build_discord_replay_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    payloads = [result.get("would_send_payload", {}) for result in results]
    queue_items = [result.get("approval_queue_item") for result in results if result.get("approval_queue_item")]
    return {
        "blocked_count": sum(1 for result in results if result.get("blocked")),
        "dispatch_count": sum(1 for result in results if result.get("dispatch_plan", {}).get("should_dispatch")),
        "approval_required_count": len(queue_items),
        "would_send_count": sum(1 for payload in payloads if payload.get("would_send") is True),
        "message_sent_count": 0,
        "external_execution_count": 0,
        "human_only_execution_count": len(queue_items),
        "secret_redaction_count": sum(1 for result in results if "[REDACTED]" in json.dumps(result, ensure_ascii=False)),
    }


def assert_discord_replay_safety(replay_result: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = replay_result.get("would_send_payloads", [])
    summary = replay_result.get("summary", {})
    assertions = [
        {
            "rule": "message_sent_count_is_zero",
            "passed": summary.get("message_sent_count") == 0,
            "details": "Local replay never sends Discord messages.",
        },
        {
            "rule": "external_execution_count_is_zero",
            "passed": summary.get("external_execution_count") == 0,
            "details": "Local replay never performs external execution.",
        },
        {
            "rule": "payloads_do_not_call_discord_api",
            "passed": all(payload.get("safety", {}).get("discord_api_called") is False for payload in payloads),
            "details": "Would-send payloads keep discord_api_called=false.",
        },
        {
            "rule": "payloads_do_not_send_messages",
            "passed": all(payload.get("safety", {}).get("message_sent") is False for payload in payloads),
            "details": "Would-send payloads keep message_sent=false.",
        },
        {
            "rule": "payloads_do_not_execute_external_actions",
            "passed": all(payload.get("safety", {}).get("external_execution") is False for payload in payloads),
            "details": "Would-send payloads keep external_execution=false.",
        },
        {
            "rule": "approval_queue_remains_human_only",
            "passed": all(item.get("human_only_execution") is True and item.get("external_execution_allowed") is False for item in replay_result.get("approval_queue", [])),
            "details": "Approval items do not become executable actions.",
        },
        {
            "rule": "sensitive_values_are_redacted",
            "passed": not _contains_secret(redact_sensitive_values(replay_result)),
            "details": "Sensitive markers are redacted from replay output.",
        },
    ]
    replay_result["safety_assertions"] = assertions
    return assertions


def run_discord_raw_event_replay(
    events: list[dict[str, Any]],
    root: str | Path | None = None,
    approval_actions: list[dict[str, Any]] | None = None,
    include_review_packet: bool = False,
) -> dict[str, Any]:
    created_at = utc_now()
    queue = ApprovalQueue()
    results = [_process_one(event, index, queue, root) for index, event in enumerate(events, start=1)]
    replay_id = "discord_replay_" + sha256(f"{created_at}|{len(results)}".encode("utf-8")).hexdigest()[:12]
    replay_result = {
        "replay_type": "discord_raw_event_replay",
        "version": "phase19_local_only",
        "replay_id": replay_id,
        "created_at": created_at,
        "source_event_file": "",
        "events_processed": len(results),
        "events": results,
        "approval_queue": queue.snapshot(),
        "approval_actions": [],
        "would_send_payloads": [result.get("would_send_payload", {}) for result in results],
        "audit_trail": [result.get("audit_payload", {}) for result in results],
        "review_packet": None,
        "summary": build_discord_replay_summary(results),
        "external_execution_count": 0,
        "human_only_execution_count": 0,
        "exportable": True,
        "safety_assertions": [],
        "warnings": list(queue.warnings),
    }
    replay_result["human_only_execution_count"] = replay_result["summary"]["human_only_execution_count"]
    if approval_actions:
        apply_discord_replay_approval_actions(replay_result, approval_actions)
        replay_result["summary"]["approved_count"] = sum(1 for item in replay_result["approval_queue"] if item.get("status") == "approved")
        replay_result["summary"]["rejected_count"] = sum(1 for item in replay_result["approval_queue"] if item.get("status") == "rejected")
    else:
        replay_result["summary"]["approved_count"] = 0
        replay_result["summary"]["rejected_count"] = 0
    assert_discord_replay_safety(replay_result)
    if include_review_packet:
        from review_packet import build_review_packet

        replay_result["review_packet"] = build_review_packet(replay_result)
    return redact_sensitive_values(replay_result)
