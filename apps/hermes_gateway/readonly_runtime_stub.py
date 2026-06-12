"""Read-only runtime skeleton that never connects to Discord."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from connection_preflight import build_connection_preflight_report


def build_readonly_runtime_config(root: str | Path) -> dict[str, Any]:
    preflight = build_connection_preflight_report(root)
    return {
        "runtime_mode": "readonly_stub",
        "local_mapping_path": str(Path(root) / "apps" / "hermes_gateway" / "local" / "discord_runtime_mapping.local.json"),
        "can_connect_gateway": False,
        "can_send_messages": False,
        "can_execute_external_actions": False,
        "token_loaded": False,
        "env_file_read": False,
        "dependency_required_now": False,
        "preflight_ready": bool(preflight.get("ready_for_phase24_readonly_connection")),
    }


def assert_readonly_runtime_safe(config: dict[str, Any]) -> None:
    unsafe = [
        key
        for key in ("can_connect_gateway", "can_send_messages", "can_execute_external_actions", "token_loaded", "env_file_read", "dependency_required_now")
        if config.get(key) is not False
    ]
    if unsafe:
        raise ValueError(f"Readonly runtime stub is unsafe: {unsafe}")


def build_readonly_runtime_stub_report(root: str | Path) -> dict[str, Any]:
    config = build_readonly_runtime_config(root)
    assert_readonly_runtime_safe(config)
    return {
        "report_type": "readonly_runtime_stub",
        "version": "phase24_no_gateway",
        **config,
        "safety_assertions": {
            "discord_api_called": False,
            "gateway_connected": False,
            "message_sent": False,
            "external_execution_enabled": False,
            "human_only_execution_preserved": True,
        },
    }


def main_stub() -> dict[str, Any]:
    return build_readonly_runtime_stub_report(Path.cwd())
