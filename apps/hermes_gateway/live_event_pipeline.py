"""Audit-only processing for live Discord message events."""

from __future__ import annotations

import re
import json
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit_log import build_audit_payload
from agent_placeholder_response import build_agent_placeholder_response
from discord_adapter_stub import build_dispatch_from_evaluation, build_would_send_payload, evaluate_discord_raw_event
from discord_safety_wrapper import block_outgoing_action
from live_event_audit_persistence import append_live_event_audit_record, build_live_event_audit_record
from live_event_review_packet import build_live_event_review_packet, write_live_event_review_packet
from live_event_routing_report import build_live_event_routing_report
from reply_planner import build_reply_plan
from would_send_preview import build_would_send_preview, write_would_send_preview


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
KNOWN_MAPPED_CHANNELS = {
    "marketing-brief": "marketing_intake",
    "homepage": "homepage_copy",
    "operation-brief": "operation_intake",
    "brand-rag": "rag_summary",
    "new-business": "new_business",
    "product-ideas": "product_ideas",
    "marin-초안": "junior_draft",
    "lucy-검토": "senior_review",
    "sns-콘텐츠": "sns_content",
    "meiko-검토": "senior_operation_review",
    "kasumi-리서치": "junior_research",
    "공모전-지원사업": "grant_competition",
    "일정-마감관리": "deadline_management",
    "reze-전략기획": "strategy_planning",
    "marin-珥덉븞": "junior_draft",
    "lucy-寃??": "senior_review",
    "sns-肄섑뀗痢?": "sns_content",
    "meiko-寃??": "senior_operation_review",
    "kasumi-由ъ꽌移?": "junior_research",
    "reze-?꾨왂湲고쉷": "strategy_planning",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def redact_discord_id(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    if LONG_ID_RE.fullmatch(text):
        return f"discord_id_redacted:{text[-4:]}"
    return LONG_ID_RE.sub(lambda match: f"discord_id_redacted:{match.group(0)[-4:]}", text)


def _encode_internal_id(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    return "encoded_id:" + base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


def _decode_internal_id(value: Any) -> str:
    text = str(value or "")
    if not text.startswith("encoded_id:"):
        return text
    try:
        return base64.urlsafe_b64decode(text.split(":", 1)[1].encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _author_dict(message: Any) -> dict[str, Any]:
    author = _value(message, "author", {}) or {}
    return {
        "id": redact_discord_id(_value(author, "id", "")),
        "display_name": _value(author, "display_name", _value(author, "name", "")),
        "bot": bool(_value(author, "bot", False)),
        "roles": _value(author, "roles", []) if isinstance(_value(author, "roles", []), list) else [],
    }


def normalize_live_discord_message_event(message: Any, mapping: dict[str, Any] | None = None) -> dict[str, Any]:
    channel = _value(message, "channel", {}) or {}
    guild = _value(message, "guild", {}) or {}
    raw_guild_id = str(_value(guild, "id", _value(message, "guild_id", "")) or "")
    raw_channel_id = str(_value(channel, "id", _value(message, "channel_id", "")) or "")
    author = _value(message, "author", {}) or {}
    raw_author_id = str(_value(author, "id", "") or "")
    raw = {
        "event_type": "live_discord_message_create",
        "event_id": redact_discord_id(_value(message, "id", "")),
        "guild_id": redact_discord_id(raw_guild_id),
        "channel_id": redact_discord_id(raw_channel_id),
        "channel_name": _value(channel, "name", _value(message, "channel_name", "")),
        "category_name": _value(message, "category_name", ""),
        "content": _value(message, "content", ""),
        "author": _author_dict(message),
        "author_is_bot": bool(_value(message, "author_is_bot", False)),
        "attachments": _value(message, "attachments", []) or [],
        "mentions": _value(message, "mentions", []) or [],
        "timestamp": str(_value(message, "created_at", _value(message, "timestamp", ""))),
        "_raw_guild_id": _encode_internal_id(raw_guild_id),
        "_raw_channel_id": _encode_internal_id(raw_channel_id),
        "_raw_author_id": _encode_internal_id(raw_author_id),
    }
    if isinstance(message, dict):
        for key in ("requested_action", "requested_source", "current_status", "requested_next_status", "actor_agent"):
            if key in message:
                raw[key] = message[key]
    return raw


def load_visibility_context(root: str | Path | None = None) -> dict[str, Any]:
    repo_root = Path(root or Path.cwd()).resolve()
    candidates = [
        repo_root / "apps" / "hermes_gateway" / "local" / "discord_runtime_mapping.local.json",
        repo_root / "apps" / "hermes_gateway" / "examples" / "discord_runtime_mapping.template.json",
    ]
    context: dict[str, Any] = {
        "guild_configured": False,
        "allowed_guild_id": "",
        "mapped_channel_names": dict(KNOWN_MAPPED_CHANNELS),
        "mapped_channel_ids": {},
    }
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        guild = payload.get("guild", {})
        guild_id = str(guild.get("guild_id") or "")
        if guild_id and not guild_id.startswith("TODO"):
            context["guild_configured"] = True
            context["allowed_guild_id"] = guild_id
        channels = payload.get("channels", {})
        for key, value in channels.items():
            if not isinstance(value, dict):
                continue
            name = value.get("channel_name") or key
            workflow_role = value.get("workflow_role") or KNOWN_MAPPED_CHANNELS.get(name, "")
            if name:
                context["mapped_channel_names"][name] = workflow_role
            channel_id = str(value.get("channel_id") or "")
            if channel_id and not channel_id.startswith("TODO"):
                context["mapped_channel_ids"][channel_id] = {"channel_name": name, "workflow_role": workflow_role}
        break
    return context


def _channel_mapping(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    raw_channel_id = _decode_internal_id(event.get("_raw_channel_id", ""))
    channel_name = event.get("channel_name", "")
    if raw_channel_id and raw_channel_id in context.get("mapped_channel_ids", {}):
        item = context["mapped_channel_ids"][raw_channel_id]
        return {"mapped": True, "channel_name": item.get("channel_name") or channel_name, "workflow_role": item.get("workflow_role", "")}
    workflow_role = context.get("mapped_channel_names", {}).get(channel_name)
    return {"mapped": bool(workflow_role), "channel_name": channel_name, "workflow_role": workflow_role or ""}


def build_visibility_event(event: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    visibility_context = context or load_visibility_context()
    initial_channel = _channel_mapping(event, visibility_context)
    raw_guild_id = _decode_internal_id(event.get("_raw_guild_id", ""))
    allowed_guild_id = visibility_context.get("allowed_guild_id", "")
    target_guild_configured = bool(visibility_context.get("guild_configured") and allowed_guild_id)
    guild_matches_target = target_guild_configured and bool(raw_guild_id) and raw_guild_id == allowed_guild_id
    guild_unknown = not bool(raw_guild_id)
    guild_allowed = guild_matches_target or (not target_guild_configured and not guild_unknown)
    channel = dict(initial_channel)
    if not guild_allowed:
        channel["mapped"] = False
        channel["workflow_role"] = ""
    guild_configured = bool(guild_matches_target or (guild_allowed and initial_channel["mapped"]))
    author_is_bot = bool(event.get("author", {}).get("bot") or event.get("author_is_bot"))
    content = str(event.get("content") or "")
    content_present = bool(content.strip())

    if author_is_bot:
        decision = "ignored_self_message"
        reason = "ignored_self_message"
    elif not guild_allowed:
        decision = "ignored_guild_not_allowed"
        reason = "ignored_guild_not_allowed"
    elif not channel["mapped"]:
        decision = "ignored_unmapped_channel"
        reason = "ignored_unmapped_channel"
    elif not content_present:
        decision = "content_unavailable_or_empty"
        reason = "content_unavailable_or_empty"
    else:
        decision = "accepted_mapped_channel"
        reason = "accepted_mapped_channel"

    return {
        "created_at": utc_now(),
        "event_type": event.get("event_type", "live_discord_message_create"),
        "decision": decision,
        "reason": reason,
        "guild_configured": guild_configured,
        "channel_mapped": bool(channel["mapped"]),
        "channel_name": channel["channel_name"],
        "workflow_role": channel["workflow_role"],
        "author_is_bot": author_is_bot,
        "author_id": redact_discord_id(_decode_internal_id(event.get("_raw_author_id", ""))),
        "content_present": content_present,
        "content_length": len(content),
        "message_sent": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
        "safety_assertions": {
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
            "raw_token_logged": False,
            "raw_discord_ids_logged": False,
        },
    }


def get_visibility_log_path(root: str | Path | None = None, created_at: str | None = None) -> Path:
    repo_root = Path(root or Path.cwd()).resolve()
    stamp = (created_at or utc_now())[:10].replace("-", "")
    return repo_root / "logs" / "hermes_gateway" / "live_events" / f"readonly_events_{stamp}.jsonl"


def write_visibility_log(event: dict[str, Any], root: str | Path | None = None, log_path: str | Path | None = None) -> Path:
    path = Path(log_path) if log_path else get_visibility_log_path(root, event.get("created_at"))
    if not path.is_absolute():
        path = Path(root or Path.cwd()).resolve() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _pipeline_safety(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "gateway_connected_by_pipeline": False,
        "discord_api_called_by_pipeline": False,
        "message_sent": False,
        "write_action_blocked": block.get("blocked") is True,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
        "human_only_execution_preserved": True,
    }


def process_live_event_audit_only(
    raw_event: Any,
    root: str | Path | None = None,
    visibility_context: dict[str, Any] | None = None,
    write_log: bool = False,
    log_path: str | Path | None = None,
) -> dict[str, Any]:
    event = normalize_live_discord_message_event(raw_event)
    block = block_outgoing_action("message_create", "Live event pipeline is audit-only in Phase 29.")
    visibility = build_visibility_event(event, visibility_context or load_visibility_context(root))
    written_log_path = str(write_visibility_log(visibility, root=root, log_path=log_path)) if write_log else ""
    audit_record = build_live_event_audit_record(visibility, content=event.get("content", ""))
    audit_record_path = str(append_live_event_audit_record(audit_record, root=root)) if write_log else ""
    routing_report = build_live_event_routing_report(audit_record)
    placeholder = build_agent_placeholder_response(audit_record, routing_report, event.get("content", ""))
    preview = build_would_send_preview(audit_record, routing_report, placeholder)
    if visibility["decision"] != "accepted_mapped_channel":
        review_packet = build_live_event_review_packet(audit_record, routing_report, preview, placeholder)
        return {
            "pipeline_mode": "audit_only",
            "status": visibility["decision"],
            "decision": visibility["decision"],
            "reason": visibility["reason"],
            "raw_event_summary": {
                "event_type": event.get("event_type"),
                "channel_name": event.get("channel_name"),
                "author_is_bot": visibility["author_is_bot"],
                "event_id": event.get("event_id"),
            },
            "visibility_event": visibility,
            "visibility_log_path": written_log_path,
            "audit_record": audit_record,
            "audit_record_path": audit_record_path,
            "routing_report": routing_report,
            "would_send_preview": preview,
            "review_packet": review_packet,
            "agent_placeholder_response": placeholder,
            "would_send_payload": {"will_send": False, "message_sent": False},
            "reply_plan": {"will_send": False, "reply_enabled": False},
            "outgoing_action_guard": block,
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
            "safety": _pipeline_safety(block),
        }

    evaluation = evaluate_discord_raw_event(event, root=root)
    dispatch_plan = build_dispatch_from_evaluation(evaluation)
    payload = build_would_send_payload(dispatch_plan, evaluation)
    payload["will_send"] = False
    payload["message_sent"] = False
    reply_plan = build_reply_plan(evaluation.get("evaluator_result", {}), payload)
    audit = build_audit_payload(
        event.get("event_type", "live_discord_message_create"),
        evaluation["normalized_request"],
        evaluation["evaluator_result"],
        dispatch_plan,
        event.get("event_id"),
    )
    preview_path = str(write_would_send_preview(preview, root=root)) if write_log else ""
    review_packet = build_live_event_review_packet(audit_record, routing_report, preview, placeholder)
    review_packet_paths = write_live_event_review_packet(review_packet, root=root) if write_log else {}
    return {
        "pipeline_mode": "audit_only",
        "status": "processed_audit_only",
        "decision": visibility["decision"],
        "reason": visibility["reason"],
        "raw_event_summary": {
            "event_type": event.get("event_type"),
            "channel_name": event.get("channel_name"),
            "author_is_bot": False,
            "event_id": event.get("event_id"),
        },
        "visibility_event": visibility,
        "visibility_log_path": written_log_path,
        "audit_record": audit_record,
        "audit_record_path": audit_record_path,
        "routing_report": routing_report,
        "would_send_preview": preview,
        "would_send_preview_path": preview_path,
        "review_packet": review_packet,
        "review_packet_paths": review_packet_paths,
        "agent_placeholder_response": placeholder,
        "normalized_request": evaluation["normalized_request"],
        "dispatch_plan": dispatch_plan,
        "would_send_payload": payload,
        "reply_plan": reply_plan,
        "audit_log_payload": audit,
        "outgoing_action_guard": block,
        "message_sent": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
        "safety": _pipeline_safety(block),
    }


def build_live_event_pipeline_report(root: str | Path | None = None) -> dict[str, Any]:
    sample = {
        "id": "123456789012345678",
        "guild_id": "234567890123456789",
        "channel_id": "345678901234567890",
        "channel_name": "marin-초안",
        "content": "SNS 초안 후보를 검토해 주세요.",
        "author": {"id": "456789012345678901", "display_name": "local_user", "bot": False, "roles": ["Decision Maker"]},
        "attachments": [],
        "mentions": [],
    }
    result = process_live_event_audit_only(sample, root=root)
    return {
        "report_type": "live_event_pipeline_report",
        "version": "phase29_readonly",
        "pipeline_mode": "audit_only",
        "sample_result": result,
        "safety_assertions": {
            "gateway_connected_by_report": False,
            "discord_api_called_by_report": False,
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
            "raw_long_discord_ids_logged": False,
        },
    }
