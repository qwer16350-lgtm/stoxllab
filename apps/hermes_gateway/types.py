"""Shared runtime shapes for the fresh STOXL Hermes Gateway skeleton."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class RuntimeEvent(TypedDict, total=False):
    event_type: str
    event_id: str
    text: str
    message_text: str
    content: str
    channel: str
    channel_name: str
    channel_category: str
    author_role: str
    author_display_name: str
    author_is_agent: bool
    actor_agent: str | None
    mentioned_agents: list[str]
    requested_action: str | None
    requested_source: str | None
    current_status: str | None
    requested_next_status: str | None
    timestamp: str
    attachments: list[dict[str, Any]]


class NormalizedRequest(TypedDict):
    text: str
    actor_role: str
    actor_agent: str | None
    author_display_name: str
    source_channel: str
    source_category: str
    mentioned_agents: list[str]
    requested_action: str | None
    requested_source: str | None
    current_status: str | None
    requested_next_status: str | None
    attachments: list[dict[str, Any]]
    timestamp: str


class EvaluatorResult(TypedDict, total=False):
    input: dict[str, Any]
    classification: dict[str, Any]
    routing: dict[str, Any]
    approval_gate: dict[str, Any]
    permission_check: dict[str, Any]
    handoff: dict[str, Any]
    rag_access: dict[str, Any]
    status_transition: dict[str, Any]
    guardrails: list[str]
    blocked: bool
    block_reasons: list[str]
    recommended_next_action: str
    notes: list[str]


class DispatchPlan(TypedDict):
    should_dispatch: bool
    dispatch_to_agent: str | None
    reviewer_agent: str | None
    dispatch_channel: str | None
    final_report_channel: str | None
    approval_required: bool | str | None
    human_only_execution: bool
    required_handoff: str | None
    blocked: bool
    block_reasons: list[str]


class AuditLogPayload(TypedDict):
    audit_id: str
    timestamp: str
    event_type: str
    source_channel: str
    actor_role: str
    actor_agent: str | None
    normalized_request: dict[str, Any]
    evaluator_result: dict[str, Any]
    dispatch_plan: dict[str, Any]
    blocked: bool
    block_reasons: list[str]
    human_review_required: bool
    redaction_notes: NotRequired[list[str]]
