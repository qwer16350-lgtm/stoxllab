from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_web_reference import extract_application_period, extract_deadline, parse_support_program_details


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


DETAIL_TEXT = (
    "주관기관 서울디자인재단. 신청기간 2026년 6월 9일 ~ 2026년 6월 25일. "
    "지원대상 서울 소재 중소기업 및 디자인 전문기업. "
    "지원내용 제품디자인 시각디자인 브랜드 BI CI 패키지 UX UI 지원금 최대 2천만원. "
    "자부담 기업부담금 20% 매칭. "
    "제출서류 신청서 사업계획서 사업자등록증 개인정보 동의서. "
    "신청방법 온라인 접수 홈페이지 신청서 제출. 문의처 디자인지원팀."
)


def test_support_program_field_extraction() -> None:
    details = parse_support_program_details(
        {"title": "2026 디자인개발 지원사업 모집 공고", "url": "https://seouldesign.or.kr/notice/1", "snippet": "", "institution": "서울디자인재단"},
        DETAIL_TEXT,
    )
    assert_true(details["application_period"] == "2026년 6월 9일 ~ 2026년 6월 25일", "application period")
    assert_true(details["deadline"] == "2026년 6월 25일", "deadline")
    assert_true("중소기업" in details["eligibility"], "eligibility")
    assert_true(details["support_content"] != "확인 필요", "support content")
    assert_true("지원금" in details["support_scale"], "support scale")
    assert_true("자부담" in details["self_payment"], "self payment")
    assert_true("신청서" in details["required_documents"], "required documents")
    assert_true("온라인 접수" in details["application_method"], "application method")
    assert_true("문의처" in details["contact"], "contact")


def test_deadline_patterns() -> None:
    assert_true(extract_deadline("2026.05.06 ~ 2026.06.25") == "2026년 6월 25일", "dot range")
    assert_true(extract_deadline("공고일 ~ 2026.4.27.(월, 17:00까지)") == "2026년 4월 27일", "notice range")
    assert_true(extract_deadline("마감까지: D-12") == "D-12", "d-day")
    assert_true(extract_application_period("2026-05-06 ~ 2026-06-25") == "2026년 5월 6일 ~ 2026년 6월 25일", "dash period")


def main() -> int:
    test_support_program_field_extraction()
    print("PASS test_support_program_field_extraction")
    test_deadline_patterns()
    print("PASS test_deadline_patterns")
    print("All company agent web reference support program field tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
