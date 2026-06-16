from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase44_llm_preflight_contract import build_phase44_llm_provider_preflight, build_phase44_prompt_packet, validate_phase44_llm_output_schema


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_provider_preflight_blocked_and_boolean_key() -> None:
    report = build_phase44_llm_provider_preflight({"OPENROUTER_API_KEY": "SENSITIVE_KEY_VALUE_DO_NOT_LOG"})
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true(report["openrouter_api_key_present"] is True, "Key presence only")
    assert_true(report["actual_llm_api_call"] is False, "No API call")
    assert_true(report["discord_message_sent"] is False, "No Discord send")
    assert_true("SENSITIVE_KEY_VALUE_DO_NOT_LOG" not in json.dumps(report, ensure_ascii=False), "No key value")


def test_prompt_packet_and_output_schema() -> None:
    packet = build_phase44_prompt_packet("hello")
    assert_true(packet["raw_message_content_included"] is False, "Redacted content")
    assert_true(packet["raw_discord_ids_included"] is False, "Redacted IDs")
    assert_true(validate_phase44_llm_output_schema({"schema_version": "phase44_fake_llm_output_v1", "reply_text": "ok", "safety": {}}) is True, "Schema valid")


def main() -> int:
    for test in (test_provider_preflight_blocked_and_boolean_key, test_prompt_packet_and_output_schema):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 44 preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
