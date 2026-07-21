"""Safe repo-root .env loading for CLI/runtime entry points."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, MutableMapping


DISCORD_BOT_TOKEN_ALIASES = (
    "DISCORD_BOT_TOKEN",
    "HERMES_DISCORD_BOT_TOKEN",
    "HERMES_DISCORD_TOKEN",
)


def repo_root_from_cli_file(cli_file: str | Path) -> Path:
    return Path(cli_file).resolve().parents[2]


def _first_present(env: MutableMapping[str, str], names: tuple[str, ...]) -> tuple[str, str]:
    for name in names:
        value = str(env.get(name) or "")
        if value:
            return name, value
    return "", ""


def apply_discord_token_aliases(
    env: MutableMapping[str, str] | None = None,
    *,
    preexisting_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    target = os.environ if env is None else env
    before = dict(target if preexisting_env is None else preexisting_env)
    shell_key, shell_value = _first_present(before, DISCORD_BOT_TOKEN_ALIASES)
    source_key, source_value = (shell_key, shell_value) if shell_value else _first_present(target, DISCORD_BOT_TOKEN_ALIASES)
    if source_value:
        for alias in ("DISCORD_BOT_TOKEN", "HERMES_DISCORD_BOT_TOKEN"):
            if not target.get(alias) or (shell_value and alias != shell_key and alias not in before):
                target[alias] = source_value
    return {
        "discord_token_aliases_checked": ["DISCORD_BOT_TOKEN", "HERMES_DISCORD_BOT_TOKEN"],
        "discord_token_present": bool(source_value),
        "discord_token_source_key_present": bool(source_key),
        "discord_token_value_logged": False,
        "secret_values_logged": False,
    }


def load_cli_repo_root_dotenv(cli_file: str | Path, env: MutableMapping[str, str] | None = None) -> dict[str, Any]:
    target = os.environ if env is None else env
    repo_root = repo_root_from_cli_file(cli_file)
    env_path = repo_root / ".env"
    before = dict(target)
    loaded = False
    dependency_available = True
    if env_path.exists():
        try:
            from dotenv import dotenv_values, load_dotenv
        except ImportError:
            dependency_available = False
        else:
            if target is os.environ:
                load_dotenv(env_path, override=False)
            else:
                for key, value in dotenv_values(env_path).items():
                    if key and value is not None and key not in target:
                        target[key] = value
            loaded = True
    alias_report = apply_discord_token_aliases(target, preexisting_env=before)
    return {
        "repo_root_dotenv_checked": True,
        "repo_root_dotenv_present": env_path.exists(),
        "repo_root_dotenv_loaded": loaded,
        "python_dotenv_available": dependency_available,
        "repo_root_dotenv_path_logged": False,
        "repo_root_dotenv_content_logged": False,
        "env_override_used": False,
        **alias_report,
    }
