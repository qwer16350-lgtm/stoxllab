"""Read-only Discord Gateway runtime boundary for Phase 29.

The runtime path may connect only when a human explicitly runs the CLI mode.
All message writes and external actions remain blocked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import os

from connection_preflight import build_phase29_runtime_readiness_report
from discord_safety_wrapper import assert_send_disabled, block_outgoing_action
from discord_token_loader import build_token_loader_report, load_discord_runtime_env
from live_event_pipeline import load_visibility_context, process_live_event_audit_only, redact_discord_id
from llm_private_test_reply import (
    build_llm_private_test_reply_attempt,
    build_llm_private_test_reply_payload,
    build_llm_private_test_reply_preflight,
    send_llm_private_test_reply_only,
    write_llm_private_test_reply_audit,
)
from private_test_reply import (
    build_private_test_reply_payload,
    build_private_test_reply_policy,
    send_private_test_reply_only,
)


PHASE32D_ENV_KEYS = [
    "HERMES_LLM_ENABLED",
    "HERMES_LLM_API_CALL_ENABLED",
    "HERMES_LLM_PROVIDER",
    "HERMES_LLM_MODEL",
    "HERMES_LLM_API_KEY",
    "HERMES_LLM_BASE_URL",
    "HERMES_LLM_DRY_RUN_ONLY",
    "HERMES_LLM_DRY_CALL_MODE",
    "HERMES_LLM_DISCORD_SEND_ENABLED",
    "HERMES_LLM_PRIVATE_TEST_ONLY",
    "HERMES_LLM_COST_GUARD_ENABLED",
    "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED",
    "HERMES_LLM_PRIVATE_TEST_REPLY_MODE",
    "HERMES_LLM_PRIVATE_TEST_REPLY_REQUIRE_PACKET",
    "HERMES_LLM_PRIVATE_TEST_REPLY_MAX_PER_SESSION",
    "HERMES_LLM_PRIVATE_TEST_REPLY_COOLDOWN_SECONDS",
    "HERMES_LLM_RAG_ENABLED",
    "HERMES_LLM_EXTERNAL_EXECUTION",
]


def _phase32d_env(runtime_env: dict[str, Any]) -> dict[str, Any]:
    env = dict(runtime_env)
    for key in PHASE32D_ENV_KEYS:
        if key in os.environ:
            env[key] = os.environ.get(key, "")
    env["HERMES_DISCORD_SEND_MESSAGES"] = str(bool(env.get("send_messages"))).lower()
    env["HERMES_DISCORD_PRIVATE_TEST_REPLY"] = str(bool(env.get("private_test_reply_enabled"))).lower()
    env["HERMES_DISCORD_REPLY_MODE"] = str(env.get("reply_mode", "disabled"))
    env["HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID"] = str(env.get("_private_test_channel_id", ""))
    env["HERMES_DISCORD_EXTERNAL_EXECUTION"] = str(bool(env.get("external_execution"))).lower()
    env["HERMES_DISCORD_RAG_ENABLED"] = str(bool(env.get("rag_enabled"))).lower()
    return env
from private_test_reply_safety import (
    build_private_test_reply_safety_policy,
    build_private_test_reply_safety_state,
    check_private_test_reply_safety,
    record_private_test_reply_blocked,
    record_private_test_reply_send_exception,
    record_private_test_reply_sent,
)


def build_discord_intents() -> dict[str, Any]:
    return {
        "guilds": True,
        "guild_messages": True,
        "message_content": True,
        "members": False,
        "reactions": False,
        "write_permissions_required": False,
    }


def build_ready_visibility(client: Any, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    env = runtime_env or {}
    private_policy = build_private_test_reply_policy(env)
    user = getattr(client, "user", None)
    guilds = getattr(client, "guilds", []) or []
    return {
        "runtime_mode": env.get("runtime_mode", "readonly"),
        "bot_user_name": getattr(user, "name", "") if user else "",
        "bot_user_id": redact_discord_id(getattr(user, "id", "")) if user else "",
        "connected_guild_count": len(guilds),
        "target_guild_configured": bool(env.get("guild_id_present") or env.get("target_guild_configured")),
        "send_disabled": not bool(env.get("send_messages")),
        "general_send_disabled": True,
        "private_test_reply_enabled": bool(private_policy.get("private_test_reply_enabled") and private_policy.get("send_messages")),
        "private_test_channel_configured": bool(private_policy.get("private_test_channel_id_present")),
        "external_disabled": not bool(env.get("external_execution")),
        "llm_disabled": not bool(env.get("llm_enabled")),
        "rag_disabled": not bool(env.get("rag_enabled")),
        "token_value_logged": False,
    }


def print_ready_visibility(client: Any, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    visibility = build_ready_visibility(client, runtime_env)
    print(
        "[READONLY_READY] "
        f"runtime_mode={visibility['runtime_mode']} "
        f"bot_user={visibility['bot_user_name']}:{visibility['bot_user_id']} "
        f"guilds={visibility['connected_guild_count']} "
        f"target_guild_configured={str(visibility['target_guild_configured']).lower()} "
        f"general_send_disabled={str(visibility['general_send_disabled']).lower()} "
        f"private_test_reply_enabled={str(visibility['private_test_reply_enabled']).lower()} "
        f"private_test_channel_configured={str(visibility['private_test_channel_configured']).lower()} "
        f"external_disabled={str(visibility['external_disabled']).lower()} "
        f"llm_disabled={str(visibility['llm_disabled']).lower()} "
        f"rag_disabled={str(visibility['rag_disabled']).lower()}",
        flush=True,
    )
    return visibility


def print_private_test_ready_visibility(client: Any, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    visibility = build_ready_visibility(client, runtime_env)
    print(
        "[PRIVATE_TEST_READY] "
        "runtime_mode=private_test_reply "
        f"general_send_disabled={str(visibility['general_send_disabled']).lower()} "
        f"private_test_reply_enabled={str(visibility['private_test_reply_enabled']).lower()} "
        f"private_test_channel_configured={str(visibility['private_test_channel_configured']).lower()} "
        f"external_disabled={str(visibility['external_disabled']).lower()} "
        f"llm_disabled={str(visibility['llm_disabled']).lower()} "
        f"rag_disabled={str(visibility['rag_disabled']).lower()}",
        flush=True,
    )
    return visibility


def print_private_test_llm_ready_visibility(client: Any, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    env = _phase32d_env(runtime_env or {})
    preflight = build_llm_private_test_reply_preflight(env)
    print(
        "[PRIVATE_TEST_LLM_READY] "
        "runtime_mode=private_test_llm_reply "
        f"private_test_channel_configured={str(preflight.get('private_test_channel_configured')).lower()} "
        f"llm_enabled={str(env.get('HERMES_LLM_ENABLED', '').lower() == 'true').lower()} "
        f"provider={preflight.get('llm_provider', '')} "
        f"model_configured={str(preflight.get('llm_model_configured')).lower()} "
        f"discord_send_enabled={str(preflight.get('discord_send_enabled')).lower()} "
        "public_send_disabled=true "
        f"rag_disabled={str(not preflight.get('rag_enabled')).lower()} "
        f"external_disabled={str(not preflight.get('external_execution')).lower()}",
        flush=True,
    )
    return preflight


def format_readonly_event_line(result: dict[str, Any]) -> str:
    event = result.get("visibility_event", {})
    return (
        "[READONLY_EVENT] "
        f"{event.get('decision', 'unknown')} "
        f"channel={event.get('channel_name', '')} "
        f"author={event.get('author_id', '')} "
        f"content_present={str(event.get('content_present', False)).lower()} "
        f"content_length={event.get('content_length', 0)}"
    )


def handle_readonly_message_event(
    message: Any,
    root: str | Path | None = None,
    write_log: bool = False,
    visibility_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return process_live_event_audit_only(
        message,
        root=root,
        visibility_context=visibility_context,
        write_log=write_log,
    )


def _message_value(message: Any, key: str, default: Any = "") -> Any:
    if isinstance(message, dict):
        return message.get(key, default)
    return getattr(message, key, default)


def _message_author_value(message: Any, key: str, default: Any = "") -> Any:
    author = _message_value(message, "author", {}) or {}
    if isinstance(author, dict):
        return author.get(key, default)
    return getattr(author, key, default)


def get_message_identity(message: Any) -> str:
    return str(_message_value(message, "id", _message_value(message, "event_id", "")) or "")


def should_skip_private_test_reply_event(
    message: Any,
    result: dict[str, Any],
    bot_user_id: Any = "",
    processed_message_ids: set[str] | None = None,
) -> str:
    visibility = result.get("visibility_event", {})
    decision = visibility.get("decision") or result.get("decision", "")
    author_is_bot = bool(_message_author_value(message, "bot", False) or visibility.get("author_is_bot") or result.get("author_is_bot"))
    author_id = str(_message_author_value(message, "id", "") or "")
    bot_id = str(bot_user_id or "")
    if author_is_bot or (bot_id and author_id and author_id == bot_id) or decision == "ignored_self_message":
        return "self_message"
    if str(decision).startswith("ignored_"):
        return str(decision)
    if decision != "accepted_private_test_channel":
        return "not_private_test_channel"
    message_id = get_message_identity(message)
    if processed_message_ids is not None and message_id and message_id in processed_message_ids:
        return "skipped_duplicate_message"
    return ""


def build_readonly_client(root: str | Path | None = None) -> dict[str, Any]:
    return {
        "client_type": "discord.py Client",
        "constructed_in_report": False,
        "root": str(Path(root or Path.cwd()).resolve()),
        "intents": build_discord_intents(),
        "outbound_guard": block_outgoing_action("message_create", "Client boundary is read-only."),
    }


async def execute_private_test_reply_with_safety(
    message: Any,
    payload: dict[str, Any],
    private_reply_policy: dict[str, Any],
    safety_policy: dict[str, Any],
    safety_state: dict[str, Any],
) -> dict[str, Any]:
    safety_decision = check_private_test_reply_safety(message, safety_policy, safety_state)
    if not safety_decision.get("allowed"):
        record_private_test_reply_blocked(message, safety_state, safety_decision.get("reason", "blocked"))
        return {
            "sent": False,
            "safety_decision": safety_decision,
            "reply_audit": {},
            "log_line": f"[PRIVATE_TEST_REPLY_SAFETY] blocked reason={safety_decision.get('reason', '')}",
        }
    try:
        reply_audit = await send_private_test_reply_only(message.channel, payload, private_reply_policy)
    except Exception as exc:
        record_private_test_reply_send_exception(message, safety_state, type(exc).__name__)
        return {
            "sent": False,
            "safety_decision": safety_decision,
            "reply_audit": {},
            "log_line": "[PRIVATE_TEST_REPLY_SAFETY] circuit_breaker_open reason=send_exception",
        }
    if reply_audit.get("message_sent"):
        record_private_test_reply_sent(message, safety_state)
        return {
            "sent": True,
            "safety_decision": safety_decision,
            "reply_audit": reply_audit,
            "log_line": (
                "[PRIVATE_TEST_REPLY_SAFETY] "
                f"allowed reply_count={safety_state.get('reply_count')} max={safety_policy.get('max_replies_per_session')}"
            ),
        }
    record_private_test_reply_blocked(message, safety_state, reply_audit.get("reason", "send_not_confirmed"))
    return {
        "sent": False,
        "safety_decision": safety_decision,
        "reply_audit": reply_audit,
        "log_line": f"[PRIVATE_TEST_REPLY_SAFETY] blocked reason={reply_audit.get('reason', 'send_not_confirmed')}",
    }


def build_private_test_reply_runtime_preflight(root: str | Path | None = None, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    env = runtime_env or load_discord_runtime_env(root or Path.cwd(), load_dotenv_file=False, include_token_value=False)
    policy = build_private_test_reply_policy(env)
    checks = [
        ("token_present", bool(env.get("token_present"))),
        ("send_messages_enabled", bool(policy.get("send_messages"))),
        ("private_test_reply_enabled", bool(policy.get("private_test_reply_enabled"))),
        ("reply_mode_private_test_only", policy.get("reply_mode") == "private_test_only"),
        ("private_test_channel_id_present", bool(policy.get("private_test_channel_id_present"))),
        ("external_execution_disabled", not bool(policy.get("external_execution"))),
        ("llm_disabled", not bool(policy.get("llm_enabled"))),
        ("rag_disabled", not bool(policy.get("rag_enabled"))),
    ]
    failed = [name for name, passed in checks if not passed]
    return {
        "report_type": "private_test_reply_runtime_preflight",
        "version": "phase31b_private_test_only",
        "ready": not failed,
        "blocked": bool(failed),
        "blocked_reasons": failed,
        "reason": "" if not failed else "private_test_reply_preflight_failed:" + failed[0],
        "token_present": bool(env.get("token_present")),
        "private_test_reply_enabled": bool(policy.get("private_test_reply_enabled")),
        "private_test_channel_configured": bool(policy.get("private_test_channel_id_present")),
        "message_sent": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
        "policy": {key: value for key, value in policy.items() if not key.startswith("_")},
    }


def build_private_test_llm_reply_runtime_preflight(root: str | Path | None = None, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    env = runtime_env or load_discord_runtime_env(root or Path.cwd(), load_dotenv_file=False, include_token_value=False)
    report = build_llm_private_test_reply_preflight(_phase32d_env(env))
    if not env.get("token_present"):
        report["ready"] = False
        report["blocked"] = True
        if "token_missing" not in report["blocked_reasons"]:
            report["blocked_reasons"].insert(0, "token_missing")
    report["report_type"] = "llm_private_test_reply_runtime_preflight"
    report["token_present"] = bool(env.get("token_present"))
    return report


def build_readonly_runtime_report(root: str | Path | None = None) -> dict[str, Any]:
    token_report = build_token_loader_report(root=root)
    runtime_env = {
        "token_present": token_report["token_present"],
        **token_report.get("runtime_flags", {}),
    }
    readiness = build_phase29_runtime_readiness_report(root or Path.cwd(), runtime_env=runtime_env)
    return {
        "report_type": "discord_readonly_runtime_report",
        "version": "phase29_readonly",
        "runtime_mode": "readonly_live",
        "can_connect_gateway": True,
        "can_send_messages": False,
        "can_execute_external_actions": False,
        "llm_enabled": False,
        "rag_enabled": False,
        "token_present": token_report["token_present"],
        "token_value_logged": False,
        "private_test_reply_enabled": bool(runtime_env.get("private_test_reply_enabled")),
        "private_test_channel_configured": bool(runtime_env.get("private_test_channel_id_present")),
        "runtime_readiness": readiness,
        "ready_for_phase29_readonly_runtime": readiness["ready_for_phase29_readonly_runtime"],
        "intents": build_discord_intents(),
        "client_boundary": build_readonly_client(root),
        "safety_assertions": {
            "message_sent": False,
            "discord_write_api_called": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
            "human_only_execution_preserved": True,
        },
    }


def run_readonly_discord_bot(root: str | Path | None = None, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    repo_root = Path(root or Path.cwd()).resolve()
    env = runtime_env or load_discord_runtime_env(repo_root, load_dotenv_file=True, include_token_value=True)
    private_reply_policy = build_private_test_reply_policy(env)
    readiness = build_phase29_runtime_readiness_report(repo_root, runtime_env=env)
    try:
        assert_send_disabled(env)
    except ValueError as exc:
        return {
            "started": False,
            "blocked": True,
            "reason": str(exc),
            "token_value_logged": False,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }
    if readiness.get("ready_for_phase29_readonly_runtime") is not True:
        return {
            "started": False,
            "blocked": True,
            "reason": "Phase 29 read-only runtime readiness is not ready.",
            "blocked_reasons": readiness.get("blocked_reasons", []),
            "runtime_readiness": readiness,
            "token_value_logged": False,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }
    try:
        import discord
    except ImportError:
        return {
            "started": False,
            "blocked": True,
            "reason": "discord.py dependency is not installed in the current environment.",
            "token_value_logged": False,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }

    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    client = discord.Client(intents=intents)

    visibility_context = load_visibility_context(repo_root)
    visibility_context["private_test_channel_id"] = private_reply_policy.get("_private_test_channel_id", "")
    processed_private_reply_message_ids: set[str] = set()
    safety_policy = build_private_test_reply_safety_policy(env)
    safety_state = build_private_test_reply_safety_state()

    @client.event
    async def on_ready() -> None:
        print_ready_visibility(client, env)

    @client.event
    async def on_message(message: Any) -> None:
        result = handle_readonly_message_event(
            message,
            root=repo_root,
            write_log=True,
            visibility_context=visibility_context,
        )
        print(format_readonly_event_line(result), flush=True)
        skip_reason = should_skip_private_test_reply_event(
            message,
            result,
            bot_user_id=getattr(client.user, "id", ""),
            processed_message_ids=processed_private_reply_message_ids,
        )
        if skip_reason:
            if skip_reason in {"self_message", "skipped_duplicate_message"} or result.get("visibility_event", {}).get("channel_is_private_test"):
                print(f"[PRIVATE_TEST_REPLY] skipped reason={skip_reason}", flush=True)
            return
        placeholder = result.get("agent_placeholder_response", {})
        payload = build_private_test_reply_payload(message, placeholder, private_reply_policy)
        if payload.get("will_send"):
            message_id = get_message_identity(message)
            if message_id:
                processed_private_reply_message_ids.add(message_id)
            print(
                "[PRIVATE_TEST_REPLY] "
                f"private_test_reply_allowed channel={payload.get('decision', {}).get('channel_name', '')} "
                "source=agent_placeholder_response "
                f"will_send={str(payload.get('will_send', False)).lower()}",
                flush=True,
            )
            safety_result = await execute_private_test_reply_with_safety(message, payload, private_reply_policy, safety_policy, safety_state)
            print(safety_result["log_line"], flush=True)
            if not safety_result.get("sent"):
                return
            reply_audit = safety_result["reply_audit"]
            print(
                "[PRIVATE_TEST_REPLY_SENT] "
                f"message_sent={str(reply_audit.get('message_sent', False)).lower()} "
                f"channel={payload.get('decision', {}).get('channel_name', '')}",
                flush=True,
            )
        elif result.get("visibility_event", {}).get("channel_is_private_test") or private_reply_policy.get("private_test_reply_enabled"):
            print(
                "[PRIVATE_TEST_REPLY] "
                f"blocked reason={payload.get('decision', {}).get('reason', '')}",
                flush=True,
            )

    client.run(env["_token_value"])
    return {
        "started": True,
        "blocked": False,
        "token_value_logged": False,
        "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
    }


def run_discord_private_test_reply_bot(root: str | Path | None = None, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    repo_root = Path(root or Path.cwd()).resolve()
    env = runtime_env or load_discord_runtime_env(repo_root, load_dotenv_file=True, include_token_value=True)
    preflight = build_private_test_reply_runtime_preflight(repo_root, env)
    if preflight.get("ready") is not True:
        return {
            "started": False,
            "blocked": True,
            "reason": preflight.get("reason", "private_test_reply_preflight_failed:unknown"),
            "message_sent": False,
            "token_value_logged": False,
            "preflight": preflight,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }
    private_reply_policy = build_private_test_reply_policy(env)
    try:
        import discord
    except ImportError:
        return {
            "started": False,
            "blocked": True,
            "reason": "private_test_reply_preflight_failed:discord_dependency_missing",
            "message_sent": False,
            "token_value_logged": False,
            "preflight": preflight,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }

    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    client = discord.Client(intents=intents)

    visibility_context = load_visibility_context(repo_root)
    visibility_context["private_test_channel_id"] = private_reply_policy.get("_private_test_channel_id", "")
    processed_private_reply_message_ids: set[str] = set()
    safety_policy = build_private_test_reply_safety_policy(env)
    safety_state = build_private_test_reply_safety_state()

    @client.event
    async def on_ready() -> None:
        print_private_test_ready_visibility(client, env)

    @client.event
    async def on_message(message: Any) -> None:
        result = handle_readonly_message_event(
            message,
            root=repo_root,
            write_log=True,
            visibility_context=visibility_context,
        )
        print(format_readonly_event_line(result), flush=True)
        skip_reason = should_skip_private_test_reply_event(
            message,
            result,
            bot_user_id=getattr(client.user, "id", ""),
            processed_message_ids=processed_private_reply_message_ids,
        )
        if skip_reason:
            if skip_reason in {"self_message", "skipped_duplicate_message"} or result.get("visibility_event", {}).get("channel_is_private_test"):
                print(f"[PRIVATE_TEST_REPLY] skipped reason={skip_reason}", flush=True)
            return
        placeholder = result.get("agent_placeholder_response", {})
        payload = build_private_test_reply_payload(message, placeholder, private_reply_policy)
        if payload.get("will_send"):
            message_id = get_message_identity(message)
            if message_id:
                processed_private_reply_message_ids.add(message_id)
            print(
                "[PRIVATE_TEST_REPLY] "
                f"private_test_reply_allowed channel={payload.get('decision', {}).get('channel_name', '')} "
                "source=agent_placeholder_response "
                f"will_send={str(payload.get('will_send', False)).lower()}",
                flush=True,
            )
            safety_result = await execute_private_test_reply_with_safety(message, payload, private_reply_policy, safety_policy, safety_state)
            print(safety_result["log_line"], flush=True)
            if not safety_result.get("sent"):
                return
            reply_audit = safety_result["reply_audit"]
            print(
                "[PRIVATE_TEST_REPLY_SENT] "
                f"message_sent={str(reply_audit.get('message_sent', False)).lower()} "
                f"channel={payload.get('decision', {}).get('channel_name', '')}",
                flush=True,
            )
        elif result.get("visibility_event", {}).get("channel_is_private_test") or private_reply_policy.get("private_test_reply_enabled"):
            print(
                "[PRIVATE_TEST_REPLY] "
                f"blocked reason={payload.get('decision', {}).get('reason', '')}",
                flush=True,
            )

    client.run(env["_token_value"])
    return {
        "started": True,
        "blocked": False,
        "message_sent": False,
        "token_value_logged": False,
        "preflight": preflight,
        "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
    }


def run_discord_private_test_llm_reply_bot(root: str | Path | None = None, runtime_env: dict[str, Any] | None = None) -> dict[str, Any]:
    repo_root = Path(root or Path.cwd()).resolve()
    env = runtime_env or load_discord_runtime_env(repo_root, load_dotenv_file=True, include_token_value=True)
    phase_env = _phase32d_env(env)
    preflight = build_private_test_llm_reply_runtime_preflight(repo_root, env)
    if preflight.get("ready") is not True:
        return {
            "started": False,
            "blocked": True,
            "reason": "llm_private_test_reply_preflight_failed:" + str(preflight.get("blocked_reasons", ["unknown"])[0]),
            "message_sent": False,
            "token_value_logged": False,
            "preflight": preflight,
            "safety_assertions": {
                "message_sent": False,
                "discord_write_api_called": False,
                "external_execution": False,
                "llm_called": False,
                "rag_called": False,
            },
        }
    try:
        import discord
    except ImportError:
        return {
            "started": False,
            "blocked": True,
            "reason": "llm_private_test_reply_preflight_failed:discord_dependency_missing",
            "message_sent": False,
            "token_value_logged": False,
            "preflight": preflight,
            "safety_assertions": build_readonly_runtime_report(repo_root)["safety_assertions"],
        }

    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    client = discord.Client(intents=intents)
    visibility_context = load_visibility_context(repo_root)
    visibility_context["private_test_channel_id"] = env.get("_private_test_channel_id", "")
    processed_message_ids: set[str] = set()
    safety_state = build_private_test_reply_safety_state()

    @client.event
    async def on_ready() -> None:
        print_private_test_llm_ready_visibility(client, env)

    @client.event
    async def on_message(message: Any) -> None:
        result = handle_readonly_message_event(message, root=repo_root, write_log=True, visibility_context=visibility_context)
        print(format_readonly_event_line(result), flush=True)
        skip_reason = should_skip_private_test_reply_event(
            message,
            result,
            bot_user_id=getattr(client.user, "id", ""),
            processed_message_ids=processed_message_ids,
        )
        if skip_reason:
            print(f"[PRIVATE_TEST_LLM_REPLY] skipped reason={skip_reason}", flush=True)
            return
        message_id = get_message_identity(message)
        if message_id:
            processed_message_ids.add(message_id)
        attempt = build_llm_private_test_reply_attempt(
            message,
            env=phase_env,
            safety_state=safety_state,
            agent_route_candidate=result.get("routing_report", {}).get("agent_route_candidate", "marin"),
        )
        if not attempt.get("allowed"):
            write_llm_private_test_reply_audit(attempt, root=repo_root)
            print(f"[PRIVATE_TEST_LLM_REPLY] blocked reason={attempt.get('reason', '')}", flush=True)
            return
        print("[PRIVATE_TEST_LLM_REPLY] llm_call_allowed", flush=True)
        if not attempt.get("output_safety_allowed"):
            print("[PRIVATE_TEST_LLM_REPLY] blocked reason=output_safety_blocked", flush=True)
            return
        print("[PRIVATE_TEST_LLM_REPLY] output_safety_allowed", flush=True)
        payload = build_llm_private_test_reply_payload(attempt.get("packet", {})) if attempt.get("packet") else {}
        if not payload:
            print("[PRIVATE_TEST_LLM_REPLY] blocked reason=packet_safety_failed", flush=True)
            return
        try:
            send_result = await send_llm_private_test_reply_only(message.channel, payload)
        except Exception as exc:
            record_private_test_reply_send_exception(message, safety_state, type(exc).__name__)
            print("[PRIVATE_TEST_LLM_REPLY] blocked reason=send_exception", flush=True)
            return
        if send_result.get("message_sent"):
            record_private_test_reply_sent(message, safety_state)
            sent_record = dict(attempt)
            sent_record["message_sent"] = True
            sent_record["discord_send_attempted"] = True
            write_llm_private_test_reply_audit(sent_record, root=repo_root)
            print(
                "[PRIVATE_TEST_LLM_REPLY_SENT] "
                f"message_sent=true channel={result.get('visibility_event', {}).get('channel_name', '')}",
                flush=True,
            )

    client.run(env["_token_value"])
    return {"started": True, "blocked": False, "message_sent": False, "token_value_logged": False, "preflight": preflight}
