from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase41b_reply_adapters import (
    DETERMINISTIC_REPLY_TEXT,
    FakePhase41BReplyAdapter,
    Phase41BReplyEvent,
    Phase41BReplySendResult,
    RealDiscordPhase41BReplyAdapter,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_fake_adapter_send_result_contract() -> None:
    adapter = FakePhase41BReplyAdapter(events=[Phase41BReplyEvent()])
    event = adapter.collect_events(timeout_seconds=1, max_events=1)[0]
    result = adapter.send_reply(event, DETERMINISTIC_REPLY_TEXT)
    expected_keys = set(asdict(Phase41BReplySendResult()).keys())
    assert_true(set(asdict(result).keys()) == expected_keys, "Send result shape matches contract")
    assert_true(result.adapter_type == "fake", "Fake adapter type")
    assert_true(result.message_sent_count == 1, "Fake sends once")
    assert_true(result.sent_scope == "private_test_only", "Fake private-test scope")
    assert_true(result.error_value_logged is False, "No error value logged")


def test_real_adapter_constructs_without_logging_values() -> None:
    adapter = RealDiscordPhase41BReplyAdapter(
        token="SENSITIVE_TOKEN_VALUE_DO_NOT_LOG",
        private_test_channel_id="123456789012345678",
    )
    safe_summary = {
        "adapter_type": adapter.adapter_type,
        "real_discord_send_adapter_wired": True,
        "token_value_logged": False,
        "private_test_channel_id_value_logged": False,
        "raw_discord_ids_logged": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
    }
    text = json.dumps(safe_summary, ensure_ascii=False).lower()
    assert_true("sensitive_token_value_do_not_log" not in text, "No token value")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw channel ID")
    assert_true(safe_summary["discord_message_sent"] is False, "No actual send")


def test_runtime_error_result_contract_is_sanitized() -> None:
    result = Phase41BReplySendResult(
        api_send_called=False,
        message_sent=False,
        message_sent_count=0,
        sent_scope="none",
        adapter_type="real_discord",
        error_type="RuntimeError",
        error_category="adapter_not_wired_or_contract_error",
        error_value_logged=False,
    )
    payload = asdict(result)
    assert_true(payload["error_type"] == "RuntimeError", "RuntimeError type kept")
    assert_true(payload["error_category"] == "adapter_not_wired_or_contract_error", "RuntimeError category")
    assert_true(payload["error_value_logged"] is False, "No error value")
    assert_true(payload["message_sent_count"] == 0, "No send count")


def main() -> int:
    tests = [
        test_fake_adapter_send_result_contract,
        test_real_adapter_constructs_without_logging_values,
        test_runtime_error_result_contract_is_sanitized,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 41B reply adapter tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
