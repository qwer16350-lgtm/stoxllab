"""Agent response interface placeholder with LLM/RAG disabled."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_agent_response_request(normalized_request: dict[str, Any], dispatch_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_type": "agent_response_request",
        "agent_id": dispatch_plan.get("dispatch_to_agent") or normalized_request.get("actor_agent") or "",
        "normalized_request": {
            "source_channel": normalized_request.get("source_channel"),
            "actor_agent": normalized_request.get("actor_agent"),
            "text_preview": str(normalized_request.get("text", ""))[:160],
        },
        "dispatch_plan": dict(dispatch_plan),
        "llm_enabled": False,
        "rag_enabled": False,
    }


def build_agent_response_placeholder(request: dict[str, Any]) -> dict[str, Any]:
    response = {
        "response_type": "agent_response_placeholder",
        "agent_id": request.get("agent_id", ""),
        "llm_enabled": False,
        "rag_enabled": False,
        "response_generated": False,
        "placeholder_content": "Agent response generation is disabled in this phase.",
        "requires_future_llm_phase": True,
        "requires_future_rag_phase": False,
        "safety": {
            "llm_called": False,
            "rag_called": False,
            "discord_api_called": False,
            "message_sent": False,
            "external_execution": False,
        },
    }
    assert_agent_response_safe(response)
    return response


def assert_agent_response_safe(response: dict[str, Any]) -> None:
    if response.get("llm_enabled") or response.get("rag_enabled") or response.get("response_generated"):
        raise ValueError("Agent response generation must remain disabled.")
    safety = response.get("safety", {})
    if safety.get("llm_called") or safety.get("rag_called") or safety.get("discord_api_called") or safety.get("message_sent") or safety.get("external_execution"):
        raise ValueError("Agent response safety flags are unsafe.")


def build_agent_response_interface_report(root: str | Path) -> dict[str, Any]:
    placeholder = build_agent_response_placeholder({"agent_id": "example_agent"})
    return {
        "report_type": "agent_response_interface",
        "version": "phase28_interface_only",
        "llm_enabled": False,
        "rag_enabled": False,
        "response_generation_enabled": False,
        "placeholder_example": placeholder,
        "safety_assertions": {
            "llm_called": False,
            "rag_called": False,
            "discord_api_called": False,
            "message_sent": False,
            "external_execution": False,
        },
    }
