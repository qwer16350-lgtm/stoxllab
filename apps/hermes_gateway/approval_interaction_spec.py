"""Approval interaction spec and mock-only safety contract."""

from __future__ import annotations

from typing import Any


def build_approval_interaction_spec() -> dict[str, Any]:
    spec = {
        "interaction_type": "approval_interaction_spec",
        "version": "phase27_spec_only",
        "current_mode": "manual_cli_mock_only",
        "enabled_in_runtime": False,
        "supported_future_modes": ["reaction", "button", "slash_command"],
        "approval_after_effect": {
            "external_execution_allowed": False,
            "human_only_execution": True,
            "message_send_allowed": False,
        },
        "safety": {
            "discord_api_called": False,
            "interaction_registered": False,
            "message_sent": False,
            "external_execution": False,
        },
    }
    assert_approval_interaction_safe(spec)
    return spec


def assert_approval_interaction_safe(spec: dict[str, Any]) -> None:
    if spec.get("enabled_in_runtime") is not False:
        raise ValueError("Approval interactions are spec/mock only.")
    effect = spec.get("approval_after_effect", {})
    if effect.get("external_execution_allowed") or effect.get("message_send_allowed"):
        raise ValueError("Approval interaction after-effect is unsafe.")
    safety = spec.get("safety", {})
    if safety.get("discord_api_called") or safety.get("interaction_registered") or safety.get("message_sent") or safety.get("external_execution"):
        raise ValueError("Approval interaction safety flags are unsafe.")
