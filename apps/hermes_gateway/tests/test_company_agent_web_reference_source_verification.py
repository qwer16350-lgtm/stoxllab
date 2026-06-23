from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_web_reference import extract_official_source_details


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


OFFICIAL_TEXT = (
    "신청기간 2026년 6월 9일 ~ 2026년 6월 25일. "
    "지원대상 중소기업 및 디자인 전문기업. "
    "지원내용 디자인개발 BI CI 패키지 UX UI 지원금 최대 2천만원. "
    "자부담 기업부담금 20%. 제출서류 신청서 사업계획서. "
    "신청방법 온라인 접수 기업마당 신청서 제출."
)


def test_source_confidence_high_for_official_success() -> None:
    result = extract_official_source_details(
        [
            {"title": "공식 공고", "url": "https://kidp.or.kr/notice/1", "snippet": "", "institution": "KIDP"},
            {"title": "민간 요약", "url": "https://govhelpers.com/notice/1", "snippet": "요약", "institution": "GovHelpers"},
        ],
        official_fetcher=lambda _url: {"fetch_attempted": True, "fetch_succeeded": True, "text": OFFICIAL_TEXT},
    )
    candidate = result["candidates"][0]
    assert_true(result["official_extract_success_count"] == 1, "official success")
    assert_true(result["candidate_count"] == 1, "intermediary skipped when official exists")
    assert_true(candidate["confidence"] == "높음", "high confidence")
    assert_true(candidate["source_confidence_score"] >= 0.8, "numeric confidence")
    assert_true(candidate["source_verified"] == "원문확인 성공", "source verified")


def test_intermediary_only_is_reference_low_confidence() -> None:
    result = extract_official_source_details(
        [{"title": "민간 요약", "url": "https://govhelpers.com/notice/1", "snippet": "지원사업 요약", "institution": "GovHelpers"}],
        official_fetcher=lambda _url: {"fetch_attempted": True, "fetch_succeeded": True, "text": "should not run"},
    )
    candidate = result["candidates"][0]
    assert_true(result["official_extract_attempted"] is False, "no official attempt")
    assert_true(candidate["source_type"] == "intermediary", "intermediary")
    assert_true(candidate["current_status"] == "참고용 비공식", "reference only")
    assert_true(candidate["confidence"] == "낮음", "low confidence")


def test_result_guide_is_low_confidence() -> None:
    result = extract_official_source_details(
        [{"title": "지원과제 선정평가 결과 안내", "url": "https://dcb.or.kr/notice/5", "snippet": "선정기업 결과 안내", "institution": "DCB"}],
        official_fetcher=lambda _url: {"fetch_attempted": True, "fetch_succeeded": True, "text": "최종 선정 평가 결과 안내"},
    )
    candidate = result["candidates"][0]
    assert_true(candidate["current_status"] == "선정결과/결과안내", "result guide")
    assert_true(candidate["confidence"] == "낮음", "low or reference confidence")
    assert_true("신규 신청 공고" in candidate["risk"], "risk explains non-application")


def main() -> int:
    for test in (
        test_source_confidence_high_for_official_success,
        test_intermediary_only_is_reference_low_confidence,
        test_result_guide_is_low_confidence,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All company agent web reference source verification tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
