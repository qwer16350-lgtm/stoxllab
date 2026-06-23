from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
    "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
    "HERMES_COMPANY_AGENT_LLM_MODE": "off",
    "HERMES_COMPANY_AGENT_REPLY_MODE": "deterministic_fallback",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def raising_search(_agent_id: str, _queries: list[str], _limit: int) -> dict:
    raise RuntimeError("provider exploded with secret-like value should not appear")


def failed_search(_agent_id: str, _queries: list[str], _limit: int) -> dict:
    return {"search_succeeded": False, "failure_reason": "web_reference_provider_exception", "provider": "mock", "results": []}


def test_bridge_runtime_exception_returns_guarded_fallback() -> None:
    result = build_company_agent_message_result(
        "operation-brief",
        "!kasumi 지원사업 후보 찾아줘",
        env=WEB_ENV,
        web_search_runner=raising_search,
    )
    content = result["response"]["content"]
    assert_true(result["agent_command_web_bridge"] is True, "agent bridge")
    assert_true(result["web_reference_bridge_attempted"] is True, "bridge attempted")
    assert_true(result["web_reference_succeeded"] is False, "not succeeded")
    assert_true(result["web_reference_failure_reason"] == "web_reference_runtime_exception", "bounded reason")
    assert_true(result["response"]["reply_text_source"] == "web_reference_bridge_failure", "fallback source")
    assert_true("web_reference_runtime_exception" in content, "reason visible")
    assert_true("secret-like value" not in content, "raw exception hidden")
    assert_true(result["outbound_guard_applied"] is True, "guard applied")
    assert_true(result["discord_message_sent"] is False, "no Discord in test")
    assert_true(result["response"]["llm_api_called"] is False, "no LLM")
    assert_true(result["response"]["rag_called"] is False, "no RAG")
    assert_true(result["response"]["external_execution"] is False, "no external")


def test_bridge_provider_failure_returns_reason_fallback() -> None:
    result = build_company_agent_message_result(
        "operation-brief",
        "!kasumi 지원사업 후보 찾아줘",
        env=WEB_ENV,
        web_search_runner=failed_search,
    )
    assert_true(result["response"]["reply_text_source"] == "web_reference_bridge_failure", "fallback")
    assert_true(result["web_reference_failure_reason"] == "web_reference_provider_exception", "provider reason")
    assert_true(result["outbound_guard_applied"] is True, "guard")
    assert_true(result["raw_discord_ids_logged"] is False, "no raw IDs")
    assert_true(result["secret_values_logged"] is False, "no secrets")


def main() -> int:
    test_bridge_runtime_exception_returns_guarded_fallback()
    print("PASS test_bridge_runtime_exception_returns_guarded_fallback")
    test_bridge_provider_failure_returns_reason_fallback()
    print("PASS test_bridge_provider_failure_returns_reason_fallback")
    print("All company agent web reference bridge failure visibility tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
