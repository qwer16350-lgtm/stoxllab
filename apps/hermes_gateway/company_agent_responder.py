"""Company agent response builder with deterministic fallback by default."""

from __future__ import annotations

import os
from typing import Any, Mapping

from company_agent_registry import get_agent, get_report_format
from llm_client import build_llm_client_config, build_mock_llm_response, public_llm_client_config


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _reply_mode(env: Mapping[str, str] | None = None) -> str:
    env_map = os.environ if env is None else env
    return str(env_map.get("HERMES_COMPANY_AGENT_REPLY_MODE", "deterministic_fallback") or "deterministic_fallback")


def _llm_enabled(env: Mapping[str, str] | None = None) -> bool:
    env_map = os.environ if env is None else env
    return _flag(env_map.get("HERMES_COMPANY_AGENT_LLM_ENABLED", "false"))


def build_prompt_envelope(agent_id: str, message: str, route: dict[str, Any]) -> dict[str, Any]:
    agent = get_agent(agent_id) or {}
    return {
        "envelope_type": "company_agent_prompt_envelope",
        "agent_id": agent_id,
        "agent_display_name": agent.get("display_name"),
        "prompt_path": agent.get("prompt_path"),
        "report_format": get_report_format(agent_id),
        "route_reason": route.get("reason"),
        "external_execution_allowed": False,
        "messages_preview": [
            {"role": "system", "content": f"Use {agent.get('display_name', agent_id)} persona. External execution is forbidden."},
            {"role": "user", "content": message[:1200]},
        ],
    }


def build_deterministic_company_agent_reply(agent_id: str, message: str, route: dict[str, Any]) -> dict[str, Any]:
    agent = get_agent(agent_id) or {}
    target = route.get("target_channel") or agent.get("default_channel")
    handoff = route.get("handoff_to") or agent.get("handoff_target")
    handoff_channel = route.get("handoff_channel") or target
    role = agent.get("role", "company agent")
    display_name = agent.get("display_name", agent_id)
    persona = agent.get("webhook_persona", agent_id.upper())
    content = (
        f"[{persona} / {display_name}]\n"
        f"요청: {message[:120] or 'agent command'}\n"
        f"역할: {role}\n"
        "결과:\n"
        "1. 요청을 회사 agent workflow 안에서 접수했습니다.\n"
        "2. 외부 실행 없이 Discord 답변 초안만 준비합니다.\n"
        "3. 필요한 경우 다음 검토 채널로 handoff합니다.\n"
        f"target_channel: {target}\n"
        f"handoff: {handoff}\n"
        f"handoff_channel: {handoff_channel}\n"
        "external_execution_allowed: false\n"
        "approval_required_for_external_action: true"
    )
    return {
        "response_type": "company_agent_response",
        "reply_text_source": "deterministic_fallback",
        "agent_id": agent_id,
        "webhook_persona": agent.get("webhook_persona"),
        "content": content,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "external_execution": False,
        "raw_content_logged": False,
        "secret_values_logged": False,
    }


def build_company_agent_response(
    agent_id: str,
    message: str,
    route: dict[str, Any],
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    mode = _reply_mode(env)
    if mode == "llm" and _llm_enabled(env):
        config = build_llm_client_config(dict(env or {}))
        envelope = build_prompt_envelope(agent_id, message, route)
        llm_result = build_mock_llm_response(envelope, config=config)
        return {
            "response_type": "company_agent_response",
            "reply_text_source": "llm_mock_boundary",
            "agent_id": agent_id,
            "llm_config": public_llm_client_config(config),
            "llm_result": llm_result,
            "llm_api_call_attempted": False,
            "llm_api_called": False,
            "rag_called": False,
            "external_execution": False,
            "raw_content_logged": False,
            "secret_values_logged": False,
        }
    return build_deterministic_company_agent_reply(agent_id, message, route)
