"""Build local dispatch plans without sending messages anywhere."""

from __future__ import annotations

from typing import Any

DispatchPlan = dict[str, Any]
EvaluatorResult = dict[str, Any]
NormalizedRequest = dict[str, Any]

HANDOFF_TARGET_CHANNELS = {
    "marin_to_lucy_for_review": "lucy-검토",
    "lucy_to_decision_makers_for_approval": "최종-승인요청",
    "kasumi_to_meiko_for_review": "meiko-검토",
    "meiko_to_decision_makers_for_approval": "최종-승인요청",
    "reze_to_decision_makers_for_strategy_report": "대표-회의실",
}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def build_dispatch_plan(request: NormalizedRequest, result: EvaluatorResult) -> DispatchPlan:
    route: dict[str, Any] = result.get("routing", {})
    handoff: dict[str, Any] = result.get("handoff", {})
    gate: dict[str, Any] = result.get("approval_gate", {})
    blocked = bool(result.get("blocked", False))
    source_candidates = route.get("source_channel_candidates") or []
    handoff_id = handoff.get("handoff_id")
    dispatch_channel = HANDOFF_TARGET_CHANNELS.get(handoff_id) or handoff.get("target_channel") or (source_candidates[0] if source_candidates else request.get("source_channel"))
    approval_required = gate.get("approval_required", route.get("approval_required"))
    human_only = bool(gate.get("human_only_execution", False)) or approval_required is True
    if any(item == "human_only_execution=true" for item in result.get("guardrails", [])):
        human_only = True
    return {
        "should_dispatch": not blocked,
        "dispatch_to_agent": route.get("primary_agent"),
        "reviewer_agent": route.get("reviewer_agent"),
        "dispatch_channel": dispatch_channel,
        "final_report_channel": route.get("final_report_channel"),
        "approval_required": approval_required,
        "human_only_execution": human_only,
        "required_handoff": handoff_id,
        "blocked": blocked,
        "block_reasons": _dedupe(list(result.get("block_reasons", []))),
    }
