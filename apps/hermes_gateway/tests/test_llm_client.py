"""Phase 32B LLM client boundary tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_client.py
"""

from __future__ import annotations

import json
import socket
import sys
import urllib.error
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from llm_client import (
    assert_llm_client_result_safe,
    build_llm_client_config,
    build_mock_llm_response,
    call_llm_once,
    classify_provider_error,
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


def valid_openrouter_config(**overrides: object) -> dict:
    env = {
        "HERMES_LLM_ENABLED": "true",
        "HERMES_LLM_API_CALL_ENABLED": "true",
        "HERMES_LLM_PROVIDER": "openrouter",
        "HERMES_LLM_MODEL": "openai/gpt-5.4-mini",
        "HERMES_LLM_API_KEY": "sk-secret-value",
        "HERMES_LLM_BASE_URL": "https://openrouter.ai/api/v1",
        "HERMES_LLM_DRY_CALL_MODE": "private_test_only",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_DISCORD_SEND_MESSAGES": "false",
        "HERMES_LLM_PRIVATE_TEST_ONLY": "true",
        "HERMES_LLM_COST_GUARD_ENABLED": "true",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
    }
    env.update(overrides)
    return build_llm_client_config(env)


class FakeResponse:
    def __init__(self, body: dict) -> None:
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def make_http_error(status: int, body: dict) -> urllib.error.HTTPError:
    import io

    return urllib.error.HTTPError("https://openrouter.ai/api/v1/chat/completions", status, "error", {}, io.BytesIO(json.dumps(body).encode("utf-8")))


def test_openrouter_success_response_parsing() -> None:
    def opener(request: object, timeout: int = 30) -> FakeResponse:
        return FakeResponse({"choices": [{"message": {"content": "Review-only draft response."}}], "usage": {"prompt_tokens": 10}})

    result = call_llm_once(build_llm_prompt_envelope("marin", "hello"), valid_openrouter_config(), opener=opener)
    assert_true(result["api_call_attempted"] is True, "OpenRouter success should attempt call")
    assert_true(result["api_call_succeeded"] is True, "OpenRouter success should parse")
    assert_true(result["response_text"] == "Review-only draft response.", "OpenRouter content should be parsed")


def test_openrouter_non_2xx_sanitized_status_code() -> None:
    def opener(request: object, timeout: int = 30) -> FakeResponse:
        raise make_http_error(400, {"error": {"message": "Model not found sk-secret 123456789012345678"}})

    result = call_llm_once(build_llm_prompt_envelope("marin", "hello"), valid_openrouter_config(), opener=opener)
    assert_true(result["api_call_attempted"] is True, "HTTP error should attempt call")
    assert_true(result["provider_status_code"] == 400, "HTTP status should be visible")
    assert_true(result["provider_response_redacted"] is True, "Provider response should be marked redacted")
    assert_true("sk-secret" not in json.dumps(result, ensure_ascii=False), "Secret should be redacted")
    assert_true("123456789012345678" not in json.dumps(result, ensure_ascii=False), "Discord-like ID should be redacted")


def test_authorization_api_key_not_logged() -> None:
    result = call_llm_once(
        build_llm_prompt_envelope("marin", "hello"),
        valid_openrouter_config(),
        opener=lambda request, timeout=30: (_ for _ in ()).throw(make_http_error(401, {"error": {"message": "invalid api key sk-secret-value"}})),
    )
    text = json.dumps(result, ensure_ascii=False).lower()
    assert_true("authorization" not in text, "Authorization header should not be logged")
    assert_true("sk-secret-value" not in text, "API key should not be logged")


def test_provider_error_message_max_300_chars() -> None:
    long_message = "model not found " + ("x" * 500)
    result = call_llm_once(
        build_llm_prompt_envelope("marin", "hello"),
        valid_openrouter_config(),
        opener=lambda request, timeout=30: (_ for _ in ()).throw(make_http_error(404, {"error": {"message": long_message}})),
    )
    assert_true(len(result["provider_error_message"]) <= 300, "Provider error message should be truncated")


def test_provider_error_token_and_discord_id_redacted() -> None:
    result = call_llm_once(
        build_llm_prompt_envelope("marin", "hello"),
        valid_openrouter_config(),
        opener=lambda request, timeout=30: (_ for _ in ()).throw(make_http_error(400, {"error": {"message": "token=abc 123456789012345678"}})),
    )
    text = json.dumps(result, ensure_ascii=False)
    assert_true("token=abc" not in text and "123456789012345678" not in text, "Provider error details should be redacted")


def test_model_not_found_classification() -> None:
    assert_true(classify_provider_error(404, "model not found") == "model_not_found", "Model not found should classify")


def test_insufficient_credits_classification() -> None:
    assert_true(classify_provider_error(402, "insufficient credits") == "insufficient_credits", "Credits should classify")


def test_rate_limit_classification() -> None:
    assert_true(classify_provider_error(429, "rate limit exceeded") == "rate_limited", "Rate limit should classify")


def test_timeout_classification_possible() -> None:
    result = call_llm_once(
        build_llm_prompt_envelope("marin", "hello"),
        valid_openrouter_config(),
        opener=lambda request, timeout=30: (_ for _ in ()).throw(socket.timeout("timed out")),
    )
    assert_true(result["error_type"] == "timeout", "Timeout should be visible")
    assert_true(result["provider_error_code"] == "timeout", "Timeout code should be visible")


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
        test_openrouter_success_response_parsing,
        test_openrouter_non_2xx_sanitized_status_code,
        test_authorization_api_key_not_logged,
        test_provider_error_message_max_300_chars,
        test_provider_error_token_and_discord_id_redacted,
        test_model_not_found_classification,
        test_insufficient_credits_classification,
        test_rate_limit_classification,
        test_timeout_classification_possible,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM client tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
