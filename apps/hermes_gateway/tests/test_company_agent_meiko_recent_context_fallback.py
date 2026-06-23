from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result
from company_context_store import clear_handoff_context_store


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_missing_recent_context_returns_specific_fallback() -> None:
    with tempfile.TemporaryDirectory() as memory_dir:
        os.environ["HERMES_COMPANY_MEMORY_DIR"] = memory_dir
        clear_handoff_context_store()

        def should_not_search(_agent_id: str, _queries: list[str], _limit: int) -> dict:
            raise AssertionError("web search must not run for missing recent context")

        result = build_company_agent_message_result(
            "meiko-검토",
            "!meiko 방금 Kasumi가 찾은 지원사업 검토해줘",
            env=WEB_ENV,
            web_search_runner=should_not_search,
        )

    content = result["response"]["content"]
    assert_true(result["recent_context_intent_detected"] is True, "recent intent")
    assert_true(result["recent_context_lookup_attempted"] is True, "lookup attempted")
    assert_true(result["recent_context_lookup_succeeded"] is False, "lookup failed")
    assert_true(result["response"]["reply_text_source"] == "recent_kasumi_verification_context_not_found", "fallback source")
    assert_true("recent_kasumi_verification_context_not_found" == result["response"]["web_reference_failure_reason"], "bounded reason")
    assert_true("방금 Kasumi가 찾은 지원사업 context를 찾지 못했습니다." in content, "context-specific fallback")
    assert_true("!web <검색어>" not in content, "does not suggest web first")
    assert_true("blocked by policy" not in content.lower(), "not policy")
    assert_true(result["web_reference_attempted"] is False, "no web")
    assert_true(result["llm_api_called"] is False, "no LLM")
    assert_true(result["rag_called"] is False, "no RAG")
    assert_true(result["external_execution"] is False, "no external")


def main() -> int:
    test_missing_recent_context_returns_specific_fallback()
    print("PASS test_missing_recent_context_returns_specific_fallback")
    print("All Meiko recent context fallback tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
