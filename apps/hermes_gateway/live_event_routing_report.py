"""Local routing reports for read-only live Discord events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


VERSION = "phase30_routing_report"
ROUTE_BY_WORKFLOW = {
    "marketing_intake": "marin",
    "junior_draft": "marin",
    "sns_content": "marin",
    "homepage_copy": "marin",
    "senior_review": "lucy",
    "operation_intake": "kasumi",
    "junior_research": "kasumi",
    "grant_competition": "kasumi",
    "deadline_management": "kasumi",
    "senior_operation_review": "meiko",
    "strategy_planning": "reze",
    "rag_summary": "reze",
    "new_business": "reze",
    "product_ideas": "reze",
    "final_approval": "decision_maker_review",
    "owner_meeting": "decision_maker_review",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_agent_route_candidate(workflow_role: str, channel_name: str | None = None) -> str:
    return ROUTE_BY_WORKFLOW.get(workflow_role or "", "unrouted")


def _senior_required(agent: str) -> bool:
    return agent in {"marin", "kasumi"}


def _approval_relevant(workflow_role: str, agent: str) -> bool:
    return workflow_role in {"final_approval", "owner_meeting", "senior_review", "senior_operation_review"} or agent == "decision_maker_review"


def build_live_event_routing_report(audit_record: dict[str, Any]) -> dict[str, Any]:
    workflow_role = audit_record.get("workflow_role", "")
    channel_name = audit_record.get("channel_name", "")
    agent = resolve_agent_route_candidate(workflow_role, channel_name)
    report = {
        "report_type": "live_event_routing_report",
        "version": VERSION,
        "created_at": utc_now(),
        "event_id": audit_record.get("event_id", ""),
        "channel_name": channel_name,
        "workflow_role": workflow_role,
        "agent_route_candidate": agent,
        "senior_review_required": _senior_required(agent),
        "approval_relevant": _approval_relevant(workflow_role, agent),
        "external_execution_allowed": False,
        "routing_confidence": "high" if agent != "unrouted" else "low",
        "routing_reason": f"workflow_role={workflow_role} maps to {agent}" if agent != "unrouted" else "No known route for workflow role.",
        "message_sent": False,
        "llm_called": False,
        "rag_called": False,
    }
    assert_routing_report_safe(report)
    return report


def assert_routing_report_safe(report: dict[str, Any]) -> None:
    if report.get("message_sent") or report.get("llm_called") or report.get("rag_called") or report.get("external_execution_allowed"):
        raise ValueError("Routing report has unsafe execution flags.")
