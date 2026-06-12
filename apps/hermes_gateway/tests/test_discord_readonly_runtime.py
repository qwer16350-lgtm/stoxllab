"""Phase 29 read-only Discord runtime tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_discord_readonly_runtime.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from discord_readonly_runtime import build_discord_intents, build_readonly_runtime_report, run_readonly_discord_bot
from discord_safety_wrapper import OUTGOING_ACTION_TYPES, build_send_block_report
from discord_token_loader import build_token_loader_report, get_required_env_keys


ROOT = APP_DIR.parents[1]
FORBIDDEN_SOURCE_SNIPPETS = [".send(", ".reply(", "add_reaction", "create_channel", "create_role"]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_required_env_key_names_present() -> None:
    keys = get_required_env_keys()
    assert_true("DISCORD_BOT_TOKEN" in keys, "DISCORD_BOT_TOKEN key should be documented")
    assert_true("HERMES_DISCORD_SEND_MESSAGES" in keys, "send flag key should be documented")


def test_token_report_never_returns_token_value() -> None:
    previous = os.environ.get("DISCORD_BOT_TOKEN")
    os.environ["DISCORD_BOT_TOKEN"] = "phase29_test_token_value"
    try:
        report = build_token_loader_report(ROOT)
        text = json.dumps(report, ensure_ascii=False)
        assert_true(report["token_present"] is True, "Token presence should be reported as a boolean")
        assert_true("phase29_test_token_value" not in text, "Token value must not appear in token report")
        assert_true(report["token_value_logged"] is False, "Token value must not be logged")
    finally:
        if previous is None:
            os.environ.pop("DISCORD_BOT_TOKEN", None)
        else:
            os.environ["DISCORD_BOT_TOKEN"] = previous


def test_send_block_report_blocks_every_action() -> None:
    report = build_send_block_report()
    assert_true(report["default_allowed"] is False, "Outgoing actions should be blocked by default")
    assert_true(len(report["blocked_actions"]) == len(OUTGOING_ACTION_TYPES), "Every outgoing action type should be represented")
    assert_true(all(item["allowed"] is False for item in report["blocked_actions"]), "No outgoing action should be allowed")


def test_intents_are_readonly_minimal() -> None:
    intents = build_discord_intents()
    assert_true(intents["guilds"] is True, "Guild intent should be enabled for read-only context")
    assert_true(intents["guild_messages"] is True, "Message read intent should be enabled for read-only context")
    assert_true(intents["write_permissions_required"] is False, "Write permissions should not be required")


def test_runtime_report_safety_flags() -> None:
    report = build_readonly_runtime_report(ROOT)
    assert_true(report["can_connect_gateway"] is True, "Report may describe a future Gateway connection path")
    assert_true(report["can_send_messages"] is False, "Runtime report must block message sending")
    assert_true(report["can_execute_external_actions"] is False, "Runtime report must block external execution")
    assert_true(report["llm_enabled"] is False, "LLM should be disabled")
    assert_true(report["rag_enabled"] is False, "RAG should be disabled")
    assert_true(report["token_value_logged"] is False, "Token value must not be logged")


def test_runtime_run_stops_without_token() -> None:
    report = run_readonly_discord_bot(ROOT, runtime_env={"token_present": False})
    assert_true(report["started"] is False, "Runtime should not start without token")
    assert_true(report["blocked"] is True, "Runtime should be blocked without token")
    assert_true(report["token_value_logged"] is False, "Token value must not be logged")


def test_runtime_run_stops_when_send_flag_enabled() -> None:
    report = run_readonly_discord_bot(ROOT, runtime_env={"token_present": True, "send_messages": True})
    assert_true(report["started"] is False, "Runtime should not start when send flag is enabled")
    assert_true(report["blocked"] is True, "Runtime should be blocked when send flag is enabled")


def test_runtime_source_has_no_direct_write_calls() -> None:
    source = (APP_DIR / "discord_readonly_runtime.py").read_text(encoding="utf-8")
    for snippet in FORBIDDEN_SOURCE_SNIPPETS:
        assert_true(snippet not in source, f"Runtime source should not contain direct write snippet: {snippet}")


def main() -> int:
    tests = [
        test_required_env_key_names_present,
        test_token_report_never_returns_token_value,
        test_send_block_report_blocks_every_action,
        test_intents_are_readonly_minimal,
        test_runtime_report_safety_flags,
        test_runtime_run_stops_without_token,
        test_runtime_run_stops_when_send_flag_enabled,
        test_runtime_source_has_no_direct_write_calls,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Discord read-only runtime tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
