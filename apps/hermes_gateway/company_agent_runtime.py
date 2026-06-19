"""Company agent runtime reports for STOXL Discord Agent OS v0."""

from __future__ import annotations

from typing import Any

from company_agent_router import build_company_agent_org_report, route_company_agent_message
from company_agent_responder import build_company_agent_response
from safety_report_builders import build_blocked_report


COMMAND_SYNTAX = ["!lucy", "!marin", "!meiko", "!kasumi", "!reze", "!agent", "!route", "!handoff", "!agents", "!help"]


def build_company_agent_router_dry_run(channel: str, message: str) -> dict[str, Any]:
    route = route_company_agent_message(channel, message)
    if route.get("selected_agent"):
        response = build_company_agent_response(str(route["selected_agent"]), message, route)
    else:
        response = {
            "response_type": "company_agent_response",
            "reply_text_source": "command_help",
            "llm_api_call_attempted": False,
            "rag_called": False,
            "external_execution": False,
        }
    return {
        **route,
        "response_preview": {
            "reply_text_source": response.get("reply_text_source"),
            "agent_id": response.get("agent_id"),
            "webhook_persona": response.get("webhook_persona"),
        },
    }


def build_company_agent_runtime_report(allow_flag_present: bool = False) -> dict[str, Any]:
    if not allow_flag_present:
        return build_blocked_report(
            "company_agent_runtime_blocked",
            ["company_agent_runtime_requires_manual_allow_flag"],
            {
                "allow_flag_present": False,
                "runtime_default_blocked": True,
                "actual_discord_runtime_executed": False,
                "discord_gateway_live_connection_executed": False,
                "discord_api_send_called": False,
                "discord_message_sent": False,
                "message_sent_count": 0,
                "command_syntax": list(COMMAND_SYNTAX),
                "external_execution": False,
                "webhook_url_value_logged": False,
                "raw_discord_ids_logged": False,
                "secret_values_logged": False,
            },
        )
    return build_blocked_report(
        "company_agent_runtime_manual_gate_required",
        ["actual_company_agent_runtime_not_executed_by_codex"],
        {
            "allow_flag_present": True,
            "runtime_branch_prepared": True,
            "actual_discord_runtime_executed": False,
            "discord_gateway_live_connection_executed": False,
            "discord_api_send_called": False,
            "discord_message_sent": False,
            "message_sent_count": 0,
            "command_syntax": list(COMMAND_SYNTAX),
            "external_execution": False,
            "webhook_url_value_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        },
    )


def build_company_agent_org_runtime_report() -> dict[str, Any]:
    return build_company_agent_org_report()
