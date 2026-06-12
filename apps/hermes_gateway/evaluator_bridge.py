"""Bridge local normalized requests to the Phase 10 STOXL mock evaluator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from config import GatewayConfig, load_config
from safety import contains_secret_request

EvaluatorResult = dict[str, Any]
NormalizedRequest = dict[str, Any]


def _import_phase10(root: Path):
    scripts_dir = root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from evaluate_stoxl_mock_request import evaluate_one

    return evaluate_one


def _fallback_result(request: NormalizedRequest, reason: str) -> EvaluatorResult:
    return {
        "input": dict(request),
        "classification": {"request_type": "unknown", "keyword_based": False},
        "routing": {},
        "approval_gate": {},
        "permission_check": {},
        "handoff": {},
        "rag_access": {},
        "status_transition": {},
        "guardrails": ["phase10_import_fallback"],
        "blocked": True,
        "block_reasons": [reason],
        "recommended_next_action": "Stop and inspect the local evaluator bridge.",
        "notes": [],
    }


def _route_patch_for_local_korean(result: EvaluatorResult, request: NormalizedRequest) -> None:
    text = request.get("text", "")
    action = request.get("requested_action")
    channel = request.get("source_channel", "")
    if result.get("classification", {}).get("request_type") != "unknown":
        return
    if ("인스타" in text or "SNS" in text.upper()) and "초안" in text:
        result["classification"] = {"request_type": "sns_post_draft", "keyword_based": True, "action_type": action}
        result["routing"] = {
            "primary_agent": "marin",
            "reviewer_agent": "lucy",
            "source_channel_candidates": ["marketing-brief", "sns-콘텐츠", "marin-초안"],
            "final_report_channel": "최종-승인요청",
            "approval_required": True,
            "forbidden_shortcuts": [
                "marin_finalize_publish_copy",
                "marin_direct_final_approval_request_without_lucy",
                "sns_publish_before_approval",
                "agent_external_execution",
            ],
        }
        result["handoff"] = {
            "handoff_id": "marin_to_lucy_for_review",
            "from_agent": "marin",
            "to_agent": "lucy",
            "target_channel": "lucy-검토",
        }
        result["blocked"] = False
        result["block_reasons"] = []
        result["recommended_next_action"] = "Route draft work to marin, then hand off to lucy for review."
    elif "마감" in text or "일정" in text or channel == "일정-마감관리":
        result["classification"] = {"request_type": "schedule_deadline_followup", "keyword_based": True, "action_type": action}
        result["routing"] = {
            "primary_agent": "meiko",
            "reviewer_agent": None,
            "source_channel_candidates": ["operation-brief", "일정-마감관리"],
            "final_report_channel": "최종-승인요청",
            "approval_required": False,
            "forbidden_shortcuts": ["agent_external_execution"],
        }
        result["blocked"] = False
        result["block_reasons"] = []
        result["recommended_next_action"] = "Route deadline follow-up to meiko for operational review."
    elif "전략" in text or "제품" in text or channel in {"reze-전략기획", "new-business", "product-ideas"}:
        result["classification"] = {"request_type": "strategy_product_idea", "keyword_based": True, "action_type": action}
        result["routing"] = {
            "primary_agent": "reze",
            "reviewer_agent": None,
            "source_channel_candidates": ["reze-전략기획", "new-business", "product-ideas"],
            "final_report_channel": "대표-회의실",
            "approval_required": True,
            "forbidden_shortcuts": ["reze_direct_order_to_team", "agent_external_execution"],
        }
        result["handoff"] = {
            "handoff_id": "reze_to_decision_makers_for_strategy_report",
            "from_agent": "reze",
            "to_agent": "decision_makers",
            "target_channel": "대표-회의실",
        }
        result["blocked"] = False
        result["block_reasons"] = []
        result["recommended_next_action"] = "Route strategy idea to reze for opinion-only strategy review."


def _local_guardrail_patch(result: EvaluatorResult, request: NormalizedRequest) -> None:
    text = request.get("text", "")
    action = request.get("requested_action")
    if contains_secret_request(text):
        result["blocked"] = True
        result.setdefault("block_reasons", []).append("Sensitive data exposure request is forbidden")
        result.setdefault("guardrails", []).append("no_secret_output")
    if action in {"grant_submit", "competition_submit", "sns_publish", "homepage_upload", "external_email_send"}:
        result["approval_gate"] = result.get("approval_gate") or {
            "approval_required": True,
            "human_only_execution": True,
            "external_execution_allowed_after_approval": False,
        }
        result["blocked"] = True
        reason = f"Approval gate required for action: {action}"
        if reason not in result.setdefault("block_reasons", []):
            result["block_reasons"].append(reason)
        if "human_only_execution=true" not in result.setdefault("guardrails", []):
            result["guardrails"].append("human_only_execution=true")
        if action == "grant_submit":
            result["routing"] = result.get("routing") or {
                "primary_agent": "meiko",
                "reviewer_agent": None,
                "source_channel_candidates": ["공모전-지원사업", "meiko-검토"],
                "final_report_channel": "최종-승인요청",
                "approval_required": True,
                "forbidden_shortcuts": ["agent_external_execution"],
            }


def evaluate_request(
    registry: dict[str, Any],
    request: NormalizedRequest,
    config: GatewayConfig | None = None,
) -> EvaluatorResult:
    cfg = config or load_config(Path.cwd())
    evaluator_input = {
        "text": request.get("text", ""),
        "actor_agent": request.get("actor_agent"),
        "requested_action": request.get("requested_action"),
        "requested_source": request.get("requested_source"),
        "current_status": request.get("current_status"),
        "requested_next_status": request.get("requested_next_status"),
    }
    try:
        evaluate_one = _import_phase10(cfg.repo_root)
        result = evaluate_one(registry, evaluator_input)
    except Exception as exc:
        result = _fallback_result(request, f"Phase 10 evaluator unavailable: {exc}")

    _route_patch_for_local_korean(result, request)
    _local_guardrail_patch(result, request)
    return result
