"""Create redaction-friendly audit payloads. File persistence is handled elsewhere."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

AuditLogPayload = dict[str, Any]
DispatchPlan = dict[str, Any]
EvaluatorResult = dict[str, Any]
NormalizedRequest = dict[str, Any]


REDACTED_ATTACHMENT_NOTE = "attachment originals are not stored in the audit payload"


def _audit_id(request: NormalizedRequest, event_id: str | None = None) -> str:
    seed = f"{event_id or ''}|{request.get('timestamp')}|{request.get('source_channel')}|{request.get('text')}"
    return "audit_" + sha256(seed.encode("utf-8")).hexdigest()[:16]


def _redacted_request(request: NormalizedRequest) -> dict[str, Any]:
    safe = dict(request)
    safe["attachments"] = [{"redacted": True, "note": REDACTED_ATTACHMENT_NOTE} for _ in request.get("attachments", [])]
    return safe


def build_audit_payload(
    event_type: str,
    request: NormalizedRequest,
    result: EvaluatorResult,
    plan: DispatchPlan,
    event_id: str | None = None,
) -> AuditLogPayload:
    classification = result.get("classification", {})
    external_execution_allowed = False
    return {
        "audit_id": _audit_id(request, event_id),
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "event_type": event_type,
        "source_channel": request.get("source_channel", ""),
        "author_role": request.get("actor_role", ""),
        "actor_agent": request.get("actor_agent"),
        "classification": {
            "request_type": classification.get("request_type"),
            "action_type": classification.get("action_type"),
        },
        "primary_agent": plan.get("dispatch_to_agent"),
        "reviewer_agent": plan.get("reviewer_agent"),
        "blocked": bool(plan.get("blocked")),
        "block_reasons": list(plan.get("block_reasons", [])),
        "approval_required": plan.get("approval_required"),
        "human_only_execution": bool(plan.get("human_only_execution")),
        "external_execution_allowed": external_execution_allowed,
        "normalized_request": _redacted_request(request),
        "dispatch_plan": dict(plan),
        "human_review_required": bool(plan.get("approval_required") or plan.get("human_only_execution") or plan.get("blocked")),
        "redaction_notes": [REDACTED_ATTACHMENT_NOTE, "sensitive values are redacted during export"],
    }
