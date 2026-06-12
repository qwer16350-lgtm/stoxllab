"""Read the generated STOXL registry without creating or modifying it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import GatewayConfig, load_config


def load_registry(config: GatewayConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config(Path.cwd())
    if not cfg.registry_path.exists():
        raise FileNotFoundError(
            "Missing registry/stoxl_agent_registry.example.json. "
            "Generate it with: python scripts\\load_stoxl_agent_registry.py --out registry\\stoxl_agent_registry.example.json"
        )
    return json.loads(cfg.registry_path.read_text(encoding="utf-8"))


def registry_summary(registry: dict[str, Any]) -> dict[str, Any]:
    return {
        "agents": sorted(registry.get("agents", {}).keys()),
        "route_count": len(registry.get("routing", {})),
        "approval_gate_count": len(registry.get("approval_gates", {})),
        "channel_count": len(registry.get("channels", {})),
    }
