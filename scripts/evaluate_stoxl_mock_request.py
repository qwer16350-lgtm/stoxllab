#!/usr/bin/env python
"""Read-only mock evaluator for STOXL Hermes agent routing and guardrails."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REGISTRY_PATH = "registry/stoxl_agent_registry.example.json"
JUNIOR_AGENTS = {"marin", "kasumi"}
APPROVAL_ACTIONS = {
    "sns_publish",
    "homepage_upload",
    "competition_submit",
    "grant_submit",
    "external_email_send",
    "price_confirm",
    "contract_confirm",
    "delivery_schedule_confirm",
    "official_brand_direction_confirm",
    "external_collaboration_condition_confirm",
}
ACTION_ALIASES = {
    "sns_publish": "sns_publish",
    "homepage_upload": "homepage_upload",
    "competition_submit": "competition_submit",
    "grant_submit": "grant_submit",
    "external_email_send": "external_email_send",
    "price_confirm": "price_confirm",
    "contract_confirm": "contract_confirm",
    "delivery_schedule_confirm": "delivery_schedule_confirm",
    "official_brand_direction_confirm": "official_brand_direction_confirm",
    "external_collaboration_condition_confirm": "external_collaboration_condition_confirm",
    "direct_order_to_team": "direct_order_to_team",
    "final_publish_copy": "final_publish_copy",
    "final_recommendation": "final_recommendation",
    "bot_external_execution": "bot_external_execution",
}


def find_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "registry").exists() and (candidate / "config/stoxl").exists():
            return candidate
    return current


def load_registry(root: Path) -> dict[str, Any]:
    path = root / REGISTRY_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Missing registry file: {REGISTRY_PATH}. Run: python scripts\\load_stoxl_agent_registry.py --out {REGISTRY_PATH}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_action(action: str | None) -> str | None:
    if not action:
        return None
    return ACTION_ALIASES.get(action, action)


def text_has(text: str, *words: str) -> bool:
    lower = text.lower()
    return any(word.lower() in lower for word in words)


def classify(text: str, action: str | None = None, requested_source: str | None = None) -> tuple[str, str | None]:
    action = normalize_action(action)
    if requested_source or text_has(text, "rag", "db", "자료 찾아", "자료", "source"):
        return "rag_access_request", action
    if action == "direct_order_to_team":
        return "strategy_review_of_marketing_or_operation", action
    if action in APPROVAL_ACTIONS:
        return "external_execution_request", action
    if text_has(text, "토큰", "api key", "apikey", "비밀번호", "password", "secret"):
        return "rag_access_request", action
    if text_has(text, "게시해줘", "올려줘", "업로드해줘", "제출해줘", "지원해줘", "신청해줘", "이메일", "가격 확정", "계약 확정", "납기 확정"):
        if text_has(text, "홈페이지", "웹사이트", "상세페이지"):
            return "external_execution_request", "homepage_upload"
        if text_has(text, "이메일"):
            return "external_execution_request", "external_email_send"
        if text_has(text, "가격"):
            return "external_execution_request", "price_confirm"
        if text_has(text, "계약"):
            return "external_execution_request", "contract_confirm"
        if text_has(text, "납기"):
            return "external_execution_request", "delivery_schedule_confirm"
        if text_has(text, "지원사업", "공모전", "제출", "지원해", "신청"):
            return "grant_or_competition_decision", "grant_submit"
        return "external_execution_request", "sns_publish"
    if text_has(text, "sns", "인스타", "업로드 문구", "게시물"):
        return "sns_post_draft", action
    if text_has(text, "홈페이지", "웹사이트", "상세페이지"):
        return "homepage_copy_draft", action
    if text_has(text, "마감", "일정", "팔로우업"):
        return "schedule_deadline_followup", action
    if text_has(text, "찾아줘", "서칭", "검색", "공모전", "지원사업"):
        return "competition_search", action
    if text_has(text, "스톡슬다워", "마케팅 방향", "운영팀 제안"):
        return "strategy_review_of_marketing_or_operation", action
    if text_has(text, "전략", "사업방향", "사업 방향", "제품 아이디어", "브랜드 방향", "신규 제품"):
        return "strategy_product_idea", action
    return "unknown", action


def default_result(input_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "input": input_data,
        "classification": {},
        "routing": {},
        "approval_gate": {},
        "permission_check": {},
        "handoff": {},
        "rag_access": {},
        "status_transition": {},
        "guardrails": [],
        "blocked": False,
        "block_reasons": [],
        "recommended_next_action": "",
        "notes": [],
    }


def add_block(result: dict[str, Any], reason: str) -> None:
    result["blocked"] = True
    result["block_reasons"].append(reason)


def route_for_type(registry: dict[str, Any], request_type: str) -> dict[str, Any]:
    if request_type == "external_execution_request":
        return {}
    return registry.get("routing", {}).get(request_type, {})


def gate_for_action(registry: dict[str, Any], action: str | None) -> dict[str, Any]:
    if not action:
        return {}
    for gate in registry.get("approval_gates", {}).values():
        if gate.get("action_type") == action:
            return gate
    return {}


def infer_handoff(request_type: str, action: str | None) -> str | None:
    if request_type in {"sns_post_draft", "homepage_copy_draft", "marketing_strategy_request"}:
        return "marin_to_lucy_for_review"
    if action in {"sns_publish", "homepage_upload"}:
        return "lucy_to_decision_makers_for_approval"
    if request_type == "competition_search":
        return "kasumi_to_meiko_for_review"
    if action in {"grant_submit", "competition_submit", "external_email_send"} or request_type == "grant_or_competition_decision":
        return "meiko_to_decision_makers_for_approval"
    if request_type == "strategy_product_idea":
        return "reze_to_decision_makers_for_strategy_report"
    if request_type == "strategy_review_of_marketing_or_operation":
        return "reze_to_lucy_for_marketing_strategy_opinion"
    return None


def evaluate_one(registry: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    text = item.get("text", "") or ""
    actor = item.get("actor_agent") or item.get("agent")
    action = normalize_action(item.get("requested_action") or item.get("action"))
    requested_source = item.get("requested_source")
    request_type, inferred_action = classify(text, action, requested_source)
    action = action or inferred_action

    result = default_result(item)
    result["classification"] = {"request_type": request_type, "keyword_based": True, "action_type": action}

    route = route_for_type(registry, request_type)
    if route:
        result["routing"] = route
    elif request_type == "external_execution_request" and action:
        result["routing"] = {
            "primary_agent": actor,
            "reviewer_agent": None,
            "final_report_channel": "최종-승인요청",
            "approval_required": True,
            "forbidden_shortcuts": ["agent_external_execution"],
        }
    else:
        result["notes"].append("No matching route found; request_type is unknown or handled only by guardrail.")

    gate = gate_for_action(registry, action)
    if gate:
        result["approval_gate"] = gate
        if gate.get("approval_required"):
            add_block(result, f"Approval gate required for action: {action}")
        if gate.get("external_execution_allowed_after_approval") is False:
            result["guardrails"].append("external_execution_allowed_after_approval=false")
        if gate.get("human_only_execution") is True:
            result["guardrails"].append("human_only_execution=true")

    result["permission_check"] = permission_check(registry, actor, action, request_type)
    if result["permission_check"].get("blocked"):
        add_block(result, result["permission_check"].get("reason", "Permission check blocked"))

    handoff_id = infer_handoff(request_type, action)
    if handoff_id:
        result["handoff"] = registry.get("handoff_rules", {}).get(handoff_id, {"handoff_id": handoff_id})

    result["rag_access"] = rag_check(registry, actor, requested_source, text)
    if result["rag_access"].get("blocked"):
        add_block(result, result["rag_access"].get("reason", "RAG access blocked"))

    result["status_transition"] = status_check(
        registry,
        item.get("current_status"),
        item.get("requested_next_status"),
        actor,
        action,
    )
    if result["status_transition"].get("blocked"):
        add_block(result, result["status_transition"].get("reason", "Status transition blocked"))

    if not result["recommended_next_action"]:
        result["recommended_next_action"] = recommend_next_action(result)
    return result


def permission_check(registry: dict[str, Any], actor: str | None, action: str | None, request_type: str) -> dict[str, Any]:
    check = {"actor_agent": actor, "action": action, "blocked": False, "reason": "", "permission_source": "registry"}
    if not actor or actor not in registry.get("agents", {}):
        if actor:
            check.update({"blocked": True, "reason": f"Unknown or non-agent actor: {actor}"})
        return check
    agent = registry["agents"][actor]
    if agent.get("external_execution_allowed") is not False or agent.get("final_approval_allowed") is not False:
        check.update({"blocked": True, "reason": f"Agent {actor} must not have external execution or final approval"})
        return check
    levels = agent.get("permission_levels", {})
    if levels.get("L5_External_Execute") or levels.get("L6_Final_Approval"):
        check.update({"blocked": True, "reason": f"Agent {actor} must not use L5/L6 permissions"})
        return check
    if action in APPROVAL_ACTIONS:
        check.update({"blocked": True, "reason": f"Agent {actor} cannot execute approval-gated external action: {action}"})
        return check
    if actor == "marin" and action in {"final_publish_copy", "sns_publish"}:
        check.update({"blocked": True, "reason": "Marin cannot finalize or publish marketing copy"})
    elif actor == "lucy" and action in {"sns_publish", "homepage_upload"}:
        check.update({"blocked": True, "reason": "Lucy must route publish/upload to approval; no direct execution"})
    elif actor == "kasumi" and action == "final_recommendation":
        check.update({"blocked": True, "reason": "Kasumi cannot finalize support recommendations"})
    elif actor == "meiko" and action in {"grant_submit", "competition_submit", "external_email_send"}:
        check.update({"blocked": True, "reason": "Meiko cannot submit or contact externally without approval and human-only execution"})
    elif actor == "reze" and action == "direct_order_to_team":
        check.update({"blocked": True, "reason": "Reze cannot directly command practical teams"})
    elif request_type == "strategy_review_of_marketing_or_operation" and actor == "reze":
        check["reason"] = "Allowed as opinion only; direct_order_to_team remains forbidden"
    return check


def rag_check(registry: dict[str, Any], actor: str | None, requested_source: str | None, text: str) -> dict[str, Any]:
    check = {"actor_agent": actor, "requested_source": requested_source, "allowed_sources": [], "blocked": False, "reason": ""}
    sensitive_words = ["token", "토큰", "password", "비밀번호", "api key", "apikey", "secret", "개인 민감정보"]
    if text_has(text, *sensitive_words):
        check.update({"blocked": True, "reason": "Sensitive data exposure request is forbidden"})
        return check
    if text_has(text, "repo로 복사", "레포로 복사", "복사해", "copy"):
        if text_has(text, "db", "rag", "원본"):
            check.update({"blocked": True, "reason": "Copying external DB/RAG originals into repo is forbidden"})
            return check
    if not requested_source:
        return check
    if not actor or actor not in registry.get("agents", {}):
        check.update({"blocked": True, "reason": "RAG access requires a known agent"})
        return check
    allowed = registry["agents"][actor].get("allowed_rag_sources", [])
    check["allowed_sources"] = allowed
    if requested_source not in allowed:
        check.update({"blocked": True, "reason": f"Agent {actor} cannot access RAG source group: {requested_source}"})
    return check


def status_check(registry: dict[str, Any], current: str | None, requested: str | None, actor: str | None, action: str | None) -> dict[str, Any]:
    check = {"current_status": current, "requested_next_status": requested, "actor_agent": actor, "blocked": False, "reason": ""}
    if not current or not requested:
        return check
    status = registry.get("status_tags", {}).get(current)
    allowed = status.get("allowed_next_statuses", []) if status else []
    check["allowed_next_statuses"] = allowed
    if actor in JUNIOR_AGENTS and requested in {"승인됨", "아카이브"}:
        check.update({"blocked": True, "reason": "Junior agents cannot directly approve or archive"})
    elif requested == "승인됨" and current != "승인대기":
        check.update({"blocked": True, "reason": "Cannot jump to 승인됨 without 승인대기"})
    elif current in {"완료", "폐기"} and requested != "아카이브":
        check.update({"blocked": True, "reason": "완료/폐기 can only move to 아카이브"})
    elif requested == "bot_external_execution" or action == "bot_external_execution":
        check.update({"blocked": True, "reason": "Approved external work remains human-only, not bot execution"})
    elif requested not in allowed:
        check.update({"blocked": True, "reason": f"Transition {current} -> {requested} is not allowed"})
    return check


def recommend_next_action(result: dict[str, Any]) -> str:
    if result["blocked"]:
        if result.get("approval_gate"):
            return "Create an approval request report; execution remains human-only."
        return "Stop the requested action and route to the correct reviewer or decision maker."
    handoff = result.get("handoff", {})
    if handoff:
        return f"Send required payload to {handoff.get('target_channel')} via {handoff.get('handoff_id')}."
    route = result.get("routing", {})
    if route:
        return f"Route to {route.get('primary_agent')}."
    return "No deterministic route found; ask for clarification."


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("scenarios", [])
    if isinstance(data, list):
        return data
    raise ValueError("Scenario file must contain a list or an object with scenarios")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate STOXL mock routing and guardrails without external calls.")
    parser.add_argument("--root", help="Repository root. Defaults to auto-detection.")
    parser.add_argument("--json", action="store_true", help="Print JSON output. JSON is also used for scenario output.")
    parser.add_argument("--text", help="Single request text to evaluate.")
    parser.add_argument("--scenario", help="Scenario JSON file to evaluate.")
    parser.add_argument("--out", help="Write result JSON to this path. Relative paths resolve from repo root.")
    parser.add_argument("--agent", help="Actor agent id for permission/RAG/status checks.")
    parser.add_argument("--action", help="Requested action for permission/approval checks.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_root(Path.cwd())
    try:
        registry = load_registry(root)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    try:
        if args.scenario:
            scenario_path = Path(args.scenario)
            if not scenario_path.is_absolute():
                scenario_path = root / scenario_path
            scenarios = load_scenarios(scenario_path)
            output: Any = {
                "meta": {"scenario_file": str(scenario_path), "scenario_count": len(scenarios)},
                "results": [evaluate_one(registry, scenario) for scenario in scenarios],
            }
        else:
            item = {"text": args.text or "", "actor_agent": args.agent, "requested_action": args.action}
            output = evaluate_one(registry, item)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    text = json.dumps(output, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = root / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote mock results: {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
