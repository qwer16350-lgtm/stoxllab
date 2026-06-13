"""Phase 32B LLM client boundary tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_client.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from llm_client import (
    assert_llm_client_result_safe,
    build_llm_client_config,
    build_mock_llm_response,
    call_llm_once,
    validate_llm_client_config,
)
from llm_prompt_envelope import build_llm_prompt_envelope


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_default_config_provider_disabled() -> None:
    config = build_llm_client_config({})
    assert_true(config["provider"] == "disabled", "Default provider should be disabled")
    assert_true(validate_llm_client_config(config)["blocked"] is True, "Default config should be blocked")


def test_api_key_present_boolean_only() -> None:
    config = build_llm_client_config({"HERMES_LLM_API_KEY": "sk-secret"})
    public = {key: value for key, value in config.items() if not key.startswith("_")}
    text = json.dumps(public, ensure_ascii=False)
    assert_true(config["api_key_present"] is True, "API key presence should be boolean")
    assert_true("sk-secret" not in text, "API key value should not be public")


def test_api_key_value_logged_false() -> None:
    config = build_llm_client_config({"HERMES_LLM_API_KEY": "sk-secret"})
    assert_true(config["api_key_value_logged"] is False, "API key value should never be logged")


def test_api_call_enabled_false_blocks_actual_call() -> None:
    config = build_llm_client_config({"HERMES_LLM_PROVIDER": "openai", "HERMES_LLM_MODEL": "model", "HERMES_LLM_API_KEY": "present"})
    result = call_llm_once(build_llm_prompt_envelope("marin", "hello"), config)
    assert_true(result["api_call_attempted"] is False, "Disabled API call should not attempt network")
    assert_true(result["error_type"] == "client_config_blocked", "Disabled API call should return blocked result")


def test_unsupported_provider_blocked() -> None:
    config = build_llm_client_config({"HERMES_LLM_PROVIDER": "unknown", "HERMES_LLM_API_CALL_ENABLED": "true"})
    validation = validate_llm_client_config(config)
    assert_true("unsupported_provider" in validation["blocked_reasons"], "Unsupported provider should block")


def test_mock_response_creation_possible() -> None:
    result = build_mock_llm_response(build_llm_prompt_envelope("lucy", "review"))
    assert_true(result["response_text"], "Mock response should include text")
    assert_true(result["api_call_attempted"] is False, "Mock response should not attempt API")


def test_client_result_no_discord_send() -> None:
    result = build_mock_llm_response(build_llm_prompt_envelope("marin", "draft"))
    assert_true(result["safety_assertions"]["discord_message_sent"] is False, "Client must not send Discord messages")


def test_client_result_no_rag_external() -> None:
    result = build_mock_llm_response(build_llm_prompt_envelope("reze", "strategy"))
    assert_true(result["safety_assertions"]["rag_called"] is False, "Client must not call RAG")
    assert_true(result["safety_assertions"]["external_execution"] is False, "Client must not execute external actions")


def test_raw_token_redacted() -> None:
    result = build_mock_llm_response(build_llm_prompt_envelope("marin", "sk-secret token=abc"))
    text = json.dumps(result, ensure_ascii=False).lower()
    assert_true("sk-secret" not in text and "token=abc" not in text, "Token-like values should be redacted")
    assert_llm_client_result_safe(result)


def test_raw_discord_id_redacted() -> None:
    result = build_mock_llm_response(build_llm_prompt_envelope("marin", "123456789012345678"))
    text = json.dumps(result, ensure_ascii=False)
    assert_true("123456789012345678" not in text, "Discord-like IDs should be redacted")
    assert_llm_client_result_safe(result)


def main() -> int:
    tests = [
        test_default_config_provider_disabled,
        test_api_key_present_boolean_only,
        test_api_key_value_logged_false,
        test_api_call_enabled_false_blocks_actual_call,
        test_unsupported_provider_blocked,
        test_mock_response_creation_possible,
        test_client_result_no_discord_send,
        test_client_result_no_rag_external,
        test_raw_token_redacted,
        test_raw_discord_id_redacted,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM client tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
