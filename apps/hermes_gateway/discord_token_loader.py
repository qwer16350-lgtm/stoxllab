"""Discord runtime environment loading without token disclosure."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


REQUIRED_ENV_KEYS = [
    "DISCORD_BOT_TOKEN",
    "DISCORD_GUILD_ID",
    "OWNER_KIM_DISCORD_ID",
    "OWNER_LEE_DISCORD_ID",
    "HERMES_CONFIG_PATH",
    "HERMES_DISCORD_RUNTIME_MODE",
    "HERMES_DISCORD_SEND_MESSAGES",
    "HERMES_DISCORD_PRIVATE_TEST_REPLY",
    "HERMES_DISCORD_REPLY_MODE",
    "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID",
    "HERMES_DISCORD_EXTERNAL_EXECUTION",
    "HERMES_DISCORD_LLM_ENABLED",
    "HERMES_DISCORD_RAG_ENABLED",
    "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED",
    "HERMES_LLM_PRIVATE_TEST_REPLY_MODE",
    "HERMES_LLM_PRIVATE_TEST_REPLY_REQUIRE_PACKET",
]


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_required_env_keys() -> list[str]:
    return list(REQUIRED_ENV_KEYS)


def _load_dotenv_if_available(root: Path) -> bool:
    env_path = root / ".env"
    if not env_path.exists():
        return False
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False
    load_dotenv(env_path, override=False)
    return True


def load_discord_runtime_env(
    root: str | Path | None = None,
    load_dotenv_file: bool = True,
    include_token_value: bool = False,
) -> dict[str, Any]:
    repo_root = Path(root or Path.cwd()).resolve()
    env_file_loaded = _load_dotenv_if_available(repo_root) if load_dotenv_file else False
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    private_test_channel_id = os.environ.get("HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "")
    runtime = {
        "runtime_mode": os.environ.get("HERMES_DISCORD_RUNTIME_MODE", "readonly"),
        "token_present": bool(token and token != "TODO"),
        "guild_id_present": bool(os.environ.get("DISCORD_GUILD_ID")),
        "owner_kim_id_present": bool(os.environ.get("OWNER_KIM_DISCORD_ID")),
        "owner_lee_id_present": bool(os.environ.get("OWNER_LEE_DISCORD_ID")),
        "hermes_config_path_present": bool(os.environ.get("HERMES_CONFIG_PATH")),
        "send_messages": _bool_env("HERMES_DISCORD_SEND_MESSAGES", False),
        "private_test_reply_enabled": _bool_env("HERMES_DISCORD_PRIVATE_TEST_REPLY", False),
        "reply_mode": os.environ.get("HERMES_DISCORD_REPLY_MODE", "disabled"),
        "private_test_channel_id_present": bool(private_test_channel_id),
        "_private_test_channel_id": private_test_channel_id,
        "external_execution": _bool_env("HERMES_DISCORD_EXTERNAL_EXECUTION", False),
        "llm_enabled": _bool_env("HERMES_DISCORD_LLM_ENABLED", False),
        "rag_enabled": _bool_env("HERMES_DISCORD_RAG_ENABLED", False),
        "env_file_read_allowed": True,
        "env_file_loaded": env_file_loaded,
        "env_file_content_logged": False,
        "token_value_logged": False,
    }
    if include_token_value:
        runtime["_token_value"] = token
    return runtime


def build_token_loader_report(root: str | Path | None = None) -> dict[str, Any]:
    env = load_discord_runtime_env(root=root, load_dotenv_file=False, include_token_value=False)
    missing = [key for key in REQUIRED_ENV_KEYS if key not in os.environ]
    return {
        "report_type": "discord_token_loader_report",
        "version": "phase29_readonly",
        "required_env_keys": get_required_env_keys(),
        "missing_env_keys": missing,
        "token_present": env["token_present"],
        "token_value_logged": False,
        "token_value_returned": False,
        "env_file_read_allowed": True,
        "env_file_read_during_report": False,
        "env_file_content_logged": False,
        "runtime_flags": {
            "runtime_mode": env["runtime_mode"],
            "send_messages": env["send_messages"],
            "private_test_reply_enabled": env["private_test_reply_enabled"],
            "reply_mode": env["reply_mode"],
            "private_test_channel_id_present": env["private_test_channel_id_present"],
            "external_execution": env["external_execution"],
            "llm_enabled": env["llm_enabled"],
            "rag_enabled": env["rag_enabled"],
        },
        "safety_assertions": {
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
        },
    }
