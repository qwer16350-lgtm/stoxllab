from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_discord_outbound_guard import compact_web_reference_for_discord, prepare_discord_outbound_messages


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


FULL_REFERENCE = """
[WEB_REFERENCE]
결과:
1. 제목: 공식 공고
[/WEB_REFERENCE]

지원사업 후보:
1. 후보명: 2026 디자인개발 지원사업 모집 공고
   현재상태: 모집중 추정
   마감일: 2026년 6월 25일
   신뢰도: 높음
2. 후보명: 결과 안내 페이지
   현재상태: 선정결과/결과안내
   마감일: 확인 필요
   신뢰도: 낮음

[SUPPORT_PROGRAM_VERIFICATION]
candidate_count: 2
official_source_count: 2
extracted_from_official_pages: 2
[/SUPPORT_PROGRAM_VERIFICATION]
""" + ("상세 필드\n" * 500)


def test_web_reference_compacts_for_discord_but_keeps_meiko_notice() -> None:
    compact = compact_web_reference_for_discord(FULL_REFERENCE, "kasumi")
    assert_true(len(compact) < len(FULL_REFERENCE), "compacted")
    assert_true("지원사업 후보 검색 완료" in compact, "summary title")
    assert_true("Meiko 검토 가능: true" in compact, "Meiko readiness")
    assert_true("[SUPPORT_PROGRAM_VERIFICATION]" not in compact, "full block not dumped")
    assert_true("memory/context" in compact, "memory preserved notice")


def test_prepare_uses_compact_summary_then_guard() -> None:
    prepared = prepare_discord_outbound_messages(FULL_REFERENCE, "kasumi")
    assert_true(prepared["outbound_compacted_for_discord"] is True, "compacted flag")
    assert_true(prepared["outbound_full_content_preserved_in_memory"] is True, "full preserved")
    assert_true(all(len(message) <= 1900 for message in prepared["messages"]), "safe length")


def main() -> int:
    test_web_reference_compacts_for_discord_but_keeps_meiko_notice()
    print("PASS test_web_reference_compacts_for_discord_but_keeps_meiko_notice")
    test_prepare_uses_compact_summary_then_guard()
    print("PASS test_prepare_uses_compact_summary_then_guard")
    print("All company agent web reference compact summary tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
