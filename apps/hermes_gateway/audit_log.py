"""Create in-memory audit payloads. No file logging happens by default."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

AuditLogPayload = dict[str, Any]
DispatchPlan = dict[str, Any]
EvaluatorResult = dict[str, Any]
NormalizedRequest = dict[str, Any]


REDACTED_ATTACHMENT_NOTE = "attachment originals are not stored in the audit payload"


def _audit_id(request: NormalizedRequest) -> str:
    seed = f"{request.get('timestamp')}|{request.get('source_channel')}|{request.get('text')}"
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
) -> AuditLogPayload:
    return {
        "audit_id": _audit_id(request),
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "event_type": event_type,
        "source_channel": request.get("source_channel", ""),
        "actor_role": request.get("actor_role", ""),
        "actor_agent": request.get("actor_agent"),
        "normalized_request": _redacted_request(request),
        "evaluator_result": dict(result),
        "dispatch_plan": dict(plan),
        "blocked": bool(plan.get("blocked")),
        "block_reasons": list(plan.get("block_reasons", [])),
        "human_review_required": bool(plan.get("approval_required") or plan.get("human_only_execution") or plan.get("blocked")),
        "redaction_notes": [REDACTED_ATTACHMENT_NOTE],
    }
