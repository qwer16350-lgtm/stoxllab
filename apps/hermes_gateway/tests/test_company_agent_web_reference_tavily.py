from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_web_reference import build_company_agent_web_reference_one_shot


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_tavily(_agent_id: str, _queries: list[str], _limit: int) -> dict:
    return {
        "search_succeeded": True,
        "failure_reason": "",
        "provider": "tavily",
        "results": [
            {"title": "중개 사이트 요약", "url": "https://govhelpers.com/grant/design", "snippet": "민간 요약", "institution": "GovHelpers"},
            {"title": "2026 디자인개발 지원사업 모집 공고", "url": "https://www.bizinfo.go.kr/notice/1", "snippet": "신청기간 2026.05.06 ~ 2026.06.25 지원대상 중소기업 지원내용 디자인개발", "institution": "기업마당"},
        ],
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def test_tavily_one_shot_uses_mock_and_safe_report() -> None:
    with tempfile.TemporaryDirectory() as memory_dir:
        os.environ["HERMES_COMPANY_MEMORY_DIR"] = memory_dir
        result = build_company_agent_web_reference_one_shot(
            "kasumi",
            "이번 달 디자인 지원사업 후보 찾아줘",
            allow_web_reference=True,
            env={
                "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
                "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
                "HERMES_WEB_SEARCH_PROVIDER": "tavily",
                "HERMES_WEB_SEARCH_API_KEY": "present-but-not-logged",
            },
            search_runner=mock_tavily,
            context={"command": "kasumi"},
        )
    assert_true(result["provider"] == "tavily", "provider preserved")
    assert_true(result["web_search_succeeded"] is True, "search succeeded")
    assert_true(result["official_result_count"] == 1, "official count")
    assert_true(result["intermediary_result_count"] == 1, "intermediary count")
    assert_true(result["candidate_extraction_succeeded"] is True, "candidate extraction")
    assert_true(result["discord_api_send_called"] is False, "no Discord send")
    assert_true(result["llm_api_called"] is False, "no LLM")
    assert_true(result["rag_called"] is False, "no RAG")
    assert_true(result["embedding_called"] is False, "no embedding")
    assert_true(result["external_execution"] is False, "no external")
    assert_true(result["api_key_value_logged"] is False, "API key hidden")


def main() -> int:
    test_tavily_one_shot_uses_mock_and_safe_report()
    print("PASS test_tavily_one_shot_uses_mock_and_safe_report")
    print("All company agent web reference Tavily tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
