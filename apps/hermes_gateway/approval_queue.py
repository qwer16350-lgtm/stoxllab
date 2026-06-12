"""In-memory approval queue mock for local replay runs."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


DECISION_MAKER_ROLE = "Decision Maker"
VALID_DECISIONS = {"approve", "reject"}
TERMINAL_STATUSES = {"approved", "rejected", "expired"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_approval_id(source_event_id: str, requested_action: str | None) -> str:
    seed = f"{source_event_id}|{requested_action or 'approval'}"
    return "approval_" + sha256(seed.encode("utf-8")).hexdigest()[:12]


def build_queue_item(
    source_event_id: str,
    evaluator_result: dict[str, Any],
    dispatch_plan: dict[str, Any],
) -> dict[str, Any]:
    gate = evaluator_result.get("approval_gate", {})
    classification = evaluator_result.get("classification", {})
    requested_action = gate.get("action_type") or classification.get("action_type")
    approval_id = make_approval_id(source_event_id, requested_action)
    return {
        "approval_id": approval_id,
        "source_event_id": source_event_id,
        "requested_action": requested_action,
        "primary_agent": dispatch_plan.get("dispatch_to_agent"),
        "reviewer_agent": dispatch_plan.get("reviewer_agent"),
        "final_report_channel": dispatch_plan.get("final_report_channel"),
        "approver_role_required": DECISION_MAKER_ROLE,
        "status": "pending",
        "human_only_execution": True,
        "external_execution_allowed": False,
        "block_reasons": list(dispatch_plan.get("block_reasons", [])),
        "created_at": utc_now(),
        "decided_at": None,
        "decision_by": None,
        "decision_note": None,
    }


class ApprovalQueue:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []
        self.actions: list[dict[str, Any]] = []
        self.warnings: list[str] = []

    def add_if_required(
        self,
        source_event_id: str,
        evaluator_result: dict[str, Any],
        dispatch_plan: dict[str, Any],
    ) -> dict[str, Any] | None:
        if dispatch_plan.get("approval_required") is not True:
            return None
        item = build_queue_item(source_event_id, evaluator_result, dispatch_plan)
        if self.find(item["approval_id"]) or self.find_by_source(source_event_id):
            self.warnings.append(f"Duplicate approval queue item ignored for source_event_id={source_event_id}")
            return None
        self.items.append(item)
        return item

    def find(self, approval_id: str | None) -> dict[str, Any] | None:
        if not approval_id:
            return None
        for item in self.items:
            if item.get("approval_id") == approval_id:
                return item
        return None

    def find_by_source(self, source_event_id: str | None) -> dict[str, Any] | None:
        if not source_event_id:
            return None
        for item in self.items:
            if item.get("source_event_id") == source_event_id:
                return item
        return None

    def apply_action(self, action: dict[str, Any]) -> dict[str, Any]:
        decision = action.get("decision")
        result = {
            "action": dict(action),
            "applied": False,
            "warning": None,
            "approval_id": action.get("approval_id"),
            "source_event_id": action.get("source_event_id"),
            "status_after": None,
        }
        if decision not in VALID_DECISIONS:
            result["warning"] = f"Unknown approval decision: {decision}"
            self.warnings.append(result["warning"])
            self.actions.append(result)
            return result
        if action.get("decision_role") != DECISION_MAKER_ROLE:
            result["warning"] = "Only Decision Maker role can approve or reject"
            self.warnings.append(result["warning"])
            self.actions.append(result)
            return result

        item = self.find(action.get("approval_id")) or self.find_by_source(action.get("source_event_id"))
        if not item:
            result["warning"] = "Unknown approval_id or source_event_id"
            self.warnings.append(result["warning"])
            self.actions.append(result)
            return result
        if item.get("status") in TERMINAL_STATUSES:
            result["warning"] = f"Approval already decided: {item.get('status')}"
            self.warnings.append(result["warning"])
            self.actions.append(result)
            return result

        item["status"] = "approved" if decision == "approve" else "rejected"
        item["decided_at"] = action.get("decided_at") or utc_now()
        item["decision_by"] = action.get("decision_by")
        item["decision_note"] = action.get("decision_note")
        item["human_only_execution"] = True
        item["external_execution_allowed"] = False
        if decision == "reject":
            item["block_reasons"] = list(item.get("block_reasons", [])) + ["Approval rejected by Decision Maker"]

        result["applied"] = True
        result["approval_id"] = item.get("approval_id")
        result["source_event_id"] = item.get("source_event_id")
        result["status_after"] = item.get("status")
        self.actions.append(result)
        return result

    def apply_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.apply_action(action) for action in actions]

    def snapshot(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.items]
