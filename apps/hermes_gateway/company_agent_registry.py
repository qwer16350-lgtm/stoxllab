"""STOXL Discord company agent registry loader.

The registry layer reads the generated registry and agent prompt files, then
normalizes the five company agents into a stable v0 map used by routing,
handoff, runtime, and documentation reports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


AGENT_IDS = ["lucy", "marin", "meiko", "kasumi", "reze"]

AGENT_DEFINITIONS: dict[str, dict[str, Any]] = {
    "lucy": {
        "agent_id": "lucy",
        "display_name": "루시",
        "webhook_persona": "LUCY_STOXL",
        "department": "marketing_team",
        "department_display_name": "마케팅팀",
        "seniority": "senior",
        "role": "마케팅 검토와 발행 가능 판단",
        "reports_to": ["final-approval"],
        "reviews": ["marin"],
        "handoff_target": "final-approval",
        "default_channel": "lucy-검토",
        "report_format": "marketing_review_report",
        "external_execution_allowed": False,
    },
    "marin": {
        "agent_id": "marin",
        "display_name": "마린",
        "webhook_persona": "MARIN_STOXL",
        "department": "marketing_team",
        "department_display_name": "마케팅팀",
        "seniority": "junior",
        "role": "SNS/홈페이지/콘텐츠 초안",
        "reports_to": ["lucy"],
        "reviews": [],
        "handoff_target": "lucy",
        "default_channel": "marin-초안",
        "report_format": "marketing_draft_report",
        "external_execution_allowed": False,
    },
    "meiko": {
        "agent_id": "meiko",
        "display_name": "메이코",
        "webhook_persona": "MEIKO_STOXL",
        "department": "operation_team",
        "department_display_name": "운영팀",
        "seniority": "senior",
        "role": "지원 판단, 일정, 리스크 검토",
        "reports_to": ["final-approval"],
        "reviews": ["kasumi"],
        "handoff_target": "final-approval",
        "default_channel": "meiko-검토",
        "report_format": "operation_decision_report",
        "external_execution_allowed": False,
    },
    "kasumi": {
        "agent_id": "kasumi",
        "display_name": "카스미",
        "webhook_persona": "KASUMI_STOXL",
        "department": "operation_team",
        "department_display_name": "운영팀",
        "seniority": "junior",
        "role": "공모전/지원사업 리서치",
        "reports_to": ["meiko"],
        "reviews": [],
        "handoff_target": "meiko",
        "default_channel": "kasumi-리서치",
        "report_format": "operation_research_report",
        "external_execution_allowed": False,
    },
    "reze": {
        "agent_id": "reze",
        "display_name": "레제",
        "webhook_persona": "REZE_STOXL",
        "department": "strategy_office",
        "department_display_name": "전략기획실",
        "seniority": "strategy",
        "role": "전략기획과 브랜드 해석",
        "reports_to": ["decision-makers"],
        "reviews": [],
        "handoff_target": "decision-meeting",
        "default_channel": "reze-전략기획",
        "report_format": "strategy_report",
        "external_execution_allowed": False,
    },
}

DEPARTMENTS = {
    "marketing_team": {"display_name": "마케팅팀", "agents": ["lucy", "marin"]},
    "operation_team": {"display_name": "운영팀", "agents": ["meiko", "kasumi"]},
    "strategy_office": {"display_name": "전략기획실", "agents": ["reze"]},
    "decision_makers": {"display_name": "결정권자", "agents": []},
}

CHANNEL_STRUCTURE: dict[str, list[str]] = {
    "00-결정권자": ["공지-결정사항", "대주주회의실", "최종-승인요청"],
    "10-마케팅팀": ["marketing-brief", "lucy-검토", "marin-초안", "sns-콘텐츠", "homepage"],
    "20-운영팀": ["operation-brief", "meiko-검토", "kasumi-리서치", "공모전-지원사업", "일정-마감관리"],
    "30-전략기획실": ["reze-전략기획", "brand-rag", "new-business", "product-ideas"],
    "90-archive": ["완료된-안건", "보류된-안건", "폐기된-안건"],
    "99-HERMES-TEST": ["hermes-private-test", "hermes-canary"],
}

CHANNEL_DEFAULT_AGENT = {
    "marin-초안": "marin",
    "lucy-검토": "lucy",
    "marketing-brief": "marin",
    "sns-콘텐츠": "marin",
    "homepage": "marin",
    "kasumi-리서치": "kasumi",
    "meiko-검토": "meiko",
    "operation-brief": "kasumi",
    "공모전-지원사업": "kasumi",
    "일정-마감관리": "meiko",
    "reze-전략기획": "reze",
    "brand-rag": "reze",
    "new-business": "reze",
    "product-ideas": "reze",
    "대주주회의실": "reze",
    "최종-승인요청": "lucy",
    "hermes-private-test": "marin",
    "hermes-canary": "marin",
}

PROMPT_PATHS = {agent_id: f"prompts/agents/{agent_id}.md" for agent_id in AGENT_IDS}


def _repo_root(repo_root: Path | None = None) -> Path:
    return repo_root or Path(__file__).resolve().parents[2]


def _load_json_if_present(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _read_prompt(repo_root: Path, agent_id: str) -> str:
    prompt_path = repo_root / PROMPT_PATHS[agent_id]
    if not prompt_path.exists():
        return ""
    return prompt_path.read_text(encoding="utf-8", errors="replace")


def load_company_registry(repo_root: Path | None = None) -> dict[str, Any]:
    root = _repo_root(repo_root)
    source_registry = _load_json_if_present(root / "registry" / "stoxl_agent_registry.example.json")
    agents: dict[str, dict[str, Any]] = {}
    for agent_id in AGENT_IDS:
        prompt_text = _read_prompt(root, agent_id)
        agents[agent_id] = {
            **AGENT_DEFINITIONS[agent_id],
            "prompt_path": PROMPT_PATHS[agent_id],
            "prompt_present": bool(prompt_text),
            "prompt_chars": len(prompt_text),
        }
    return {
        "registry_type": "stoxl_company_agent_registry_v0",
        "source_registry_loaded": bool(source_registry),
        "agents": agents,
        "departments": DEPARTMENTS,
        "channel_structure": CHANNEL_STRUCTURE,
        "channel_default_agent": CHANNEL_DEFAULT_AGENT,
        "webhook_personas": {agent_id: agents[agent_id]["webhook_persona"] for agent_id in AGENT_IDS},
        "external_execution_allowed": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "webhook_url_values_logged": False,
    }


def get_agent(agent_id: str, registry: dict[str, Any] | None = None) -> dict[str, Any] | None:
    selected_registry = registry or load_company_registry()
    return selected_registry.get("agents", {}).get(str(agent_id).lower())


def list_agents(registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    selected_registry = registry or load_company_registry()
    return [selected_registry["agents"][agent_id] for agent_id in AGENT_IDS]


def get_channel_policy(channel_name: str, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_registry = registry or load_company_registry()
    known_channels = {
        channel
        for channels in selected_registry.get("channel_structure", {}).values()
        for channel in channels
    }
    return {
        "channel_name": channel_name,
        "known_channel": channel_name in known_channels,
        "default_agent": selected_registry.get("channel_default_agent", {}).get(channel_name),
        "send_allowed": False,
        "external_execution_allowed": False,
        "raw_discord_ids_logged": False,
    }


def get_default_agent_for_channel(channel_name: str, registry: dict[str, Any] | None = None) -> str | None:
    selected_registry = registry or load_company_registry()
    return selected_registry.get("channel_default_agent", {}).get(channel_name)


def get_handoff_target(agent_id: str, registry: dict[str, Any] | None = None) -> str | None:
    agent = get_agent(agent_id, registry)
    if not agent:
        return None
    return agent.get("handoff_target")


def get_report_format(agent_id: str, registry: dict[str, Any] | None = None) -> str | None:
    agent = get_agent(agent_id, registry)
    if not agent:
        return None
    return agent.get("report_format")
