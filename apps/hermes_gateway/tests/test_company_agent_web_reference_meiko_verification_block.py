from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_persistent_memory import load_recent_records
from company_web_reference import build_company_agent_web_reference_one_shot


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


WEB_ENV = {
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "true",
    "HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE": "manual_command_only",
    "HERMES_WEB_SEARCH_PROVIDER": "tavily",
    "HERMES_WEB_SEARCH_API_KEY": "mock-key-value-not-logged",
}


def mock_search(_agent_id: str, _queries: list[str], _limit: int) -> dict:
    return {
        "search_succeeded": True,
        "failure_reason": "",
        "provider": "tavily",
        "results": [
            {"title": "2026 디자인개발 지원사업 모집 공고", "url": "https://www.bizinfo.go.kr/notice/1", "snippet": "공식", "institution": "기업마당"},
            {"title": "부산 디자인 지원사업 모집 공고", "url": "https://busan.go.kr/notice/2", "snippet": "공식", "institution": "부산광역시"},
            {"title": "민간 요약", "url": "https://govhelpers.com/notice/3", "snippet": "요약", "institution": "GovHelpers"},
        ],
    }


def mock_fetch(url: str) -> dict:
    return {
        "fetch_attempted": True,
        "fetch_succeeded": True,
        "failure_reason": "",
        "text": (
            "신청기간 2026년 6월 9일 ~ 2026년 6월 25일. "
            "지원대상 중소기업 및 디자인 전문기업. "
            "지원내용 디자인개발 BI CI 패키지 UX UI 지원금 최대 2천만원. "
            "자부담 기업부담금 20%. 제출서류 신청서 사업계획서. "
            "신청방법 온라인 접수 기업마당 신청서 제출. 문의처 담당부서."
        ),
        "url_seen": url,
    }


def test_one_shot_writes_meiko_verification_block_and_memory() -> None:
    with tempfile.TemporaryDirectory() as memory_dir:
        os.environ["HERMES_COMPANY_MEMORY_DIR"] = memory_dir
        result = build_company_agent_web_reference_one_shot(
            "kasumi",
            "이번 달 전국 중소기업 디자인개발 지원사업 후보 찾아줘",
            allow_web_reference=True,
            env=WEB_ENV,
            search_runner=mock_search,
            official_fetcher=mock_fetch,
            context={"command": "kasumi"},
        )
        recent = load_recent_records("recent_item", 5, memory_dir)
    assert_true(result["web_search_succeeded"] is True, "search succeeded")
    assert_true(result["official_result_count"] == 2, "official count")
    assert_true(result["intermediary_result_count"] == 1, "intermediary count")
    assert_true(result["official_extract_attempted"] is True, "official extract attempted")
    assert_true(result["official_extract_success_count"] == 2, "official extract success")
    assert_true(result["candidate_count"] == 2, "official candidates prioritized")
    assert_true(result["candidate_extraction_succeeded"] is True, "candidate extraction")
    assert_true(result["verification_block_written"] is True, "verification block")
    assert_true(result["ready_for_meiko_verification"] is True, "ready for Meiko")
    assert_true(result["ready_for_rag_phase"] is True, "ready for RAG phase")
    assert_true("[SUPPORT_PROGRAM_VERIFICATION]" in result["reference_report"], "verification block in report")
    assert_true("지원금/지원규모" in result["reference_report"], "expanded candidate card")
    assert_true(result["discord_api_send_called"] is False, "no Discord")
    assert_true(result["llm_api_called"] is False, "no LLM")
    assert_true(result["rag_called"] is False, "no RAG")
    assert_true(result["embedding_called"] is False, "no embedding")
    assert_true(result["external_execution"] is False, "no external")
    assert_true(result["api_key_value_logged"] is False, "API key hidden")
    dumped = json.dumps({"result": result, "recent": recent}, ensure_ascii=False)
    assert_true("mock-key-value-not-logged" not in dumped, "key value omitted")
    assert_true("<html" not in dumped.lower() and "<script" not in dumped.lower(), "no HTML dump")
    assert_true(any(record.get("type") == "web_reference_support_program_candidates" for record in recent), "memory type")


def main() -> int:
    test_one_shot_writes_meiko_verification_block_and_memory()
    print("PASS test_one_shot_writes_meiko_verification_block_and_memory")
    print("All company agent web reference Meiko verification block tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
