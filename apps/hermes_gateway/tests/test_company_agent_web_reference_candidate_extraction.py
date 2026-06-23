from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_web_reference import build_candidate_cards, classify_candidate_status, extract_deadline, format_agent_web_reference_block


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


MOCK_RESULTS = [
    {
        "title": "2026 서울 디자인개발 지원사업 모집 공고",
        "url": "https://www.bizinfo.go.kr/notice/1",
        "snippet": "신청기간 2026년 6월 9일 ~ 2026년 6월 25일 지원대상 중소기업 지원내용 디자인개발 제출서류 신청서",
        "institution": "기업마당",
    },
    {
        "title": "2026 부산 디자인 지원사업 공고",
        "url": "https://busan.go.kr/notice/2",
        "snippet": "2026.05.06 ~ 2026.06.25 지원대상 부산 소재 기업 지원내용 패키지 디자인",
        "institution": "부산광역시",
    },
    {
        "title": "금천구 디자인 지원사업 모집기간 안내",
        "url": "https://seouldesign.or.kr/notice/3",
        "snippet": "모집기간 : 공고일 ~ 2026.4.27.(월, 17:00까지) 필요자료 사업계획서",
        "institution": "서울디자인재단",
    },
    {
        "title": "디자인개발 지원사업 마감까지: D-12",
        "url": "https://kidp.or.kr/notice/4",
        "snippet": "지원내용 BI CI UX UI 지원금 확인 필요",
        "institution": "한국디자인진흥원",
    },
    {
        "title": "디자인 지원과제 선정평가 결과 안내",
        "url": "https://dcb.or.kr/notice/5",
        "snippet": "선정기업 결과 안내. 신규 신청 공고가 아닐 수 있음",
        "institution": "부산디자인진흥원",
    },
]


def test_candidate_cards_extract_five_and_deadlines() -> None:
    cards = build_candidate_cards(MOCK_RESULTS)
    by_name = {card["candidate_name"]: card for card in cards}
    assert_true(len(cards) == 5, "five candidate cards")
    assert_true(by_name["2026 서울 디자인개발 지원사업 모집 공고"]["deadline"] == "2026년 6월 25일", "Korean range deadline")
    assert_true(by_name["2026 부산 디자인 지원사업 공고"]["deadline"] == "2026년 6월 25일", "dot range deadline")
    assert_true(by_name["금천구 디자인 지원사업 모집기간 안내"]["deadline"] == "2026년 4월 27일", "notice-to-date deadline")
    assert_true(by_name["디자인개발 지원사업 마감까지: D-12"]["deadline"] == "D-12", "D-day deadline")
    assert_true(by_name["디자인 지원과제 선정평가 결과 안내"]["current_status"] == "선정결과/결과안내", "result guide classified")
    assert_true(all(card["source_type"] == "official" for card in cards), "all official")


def test_reference_report_contains_candidate_cards() -> None:
    report = format_agent_web_reference_block("kasumi", MOCK_RESULTS, "2026년 6월 디자인 지원사업")
    assert_true(report.count("후보명:") == 5, "five candidates rendered")
    assert_true("source_type: official" in report, "common source type rendered")
    assert_true("출처유형: official" in report, "candidate source type rendered")
    assert_true("선정결과/결과안내" in report, "result guide rendered")


def test_standalone_extractors() -> None:
    assert_true(extract_deadline("2026.05.06 ~ 2026.06.25") == "2026년 6월 25일", "dot deadline")
    assert_true(extract_deadline("공고일 ~ 2026.4.27.(월, 17:00까지)") == "2026년 4월 27일", "notice deadline")
    assert_true(classify_candidate_status("선정평가 결과 안내") == "선정결과/결과안내", "result status")


def main() -> int:
    test_candidate_cards_extract_five_and_deadlines()
    print("PASS test_candidate_cards_extract_five_and_deadlines")
    test_reference_report_contains_candidate_cards()
    print("PASS test_reference_report_contains_candidate_cards")
    test_standalone_extractors()
    print("PASS test_standalone_extractors")
    print("All company agent web reference candidate extraction tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
