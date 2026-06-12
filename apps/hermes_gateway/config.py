"""Repository path discovery for the fresh local Hermes Gateway skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GatewayConfig:
    repo_root: Path
    registry_path: Path
    config_dir: Path
    prompts_dir: Path
    dryrun_dir: Path
    env_example_path: Path
    env_example_exists: bool


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "config" / "stoxl").exists() and (candidate / "scripts").exists():
            return candidate
    raise RuntimeError("Could not find STOXL_LAB repo root from current path.")


def load_config(start: Path | None = None) -> GatewayConfig:
    root = find_repo_root(start)
    env_example = root / ".env.example"
    return GatewayConfig(
        repo_root=root,
        registry_path=root / "registry" / "stoxl_agent_registry.example.json",
        config_dir=root / "config" / "stoxl",
        prompts_dir=root / "prompts" / "agents",
        dryrun_dir=root / "discord",
        env_example_path=env_example,
        env_example_exists=env_example.exists(),
    )
