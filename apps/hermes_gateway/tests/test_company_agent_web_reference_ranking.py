from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_web_reference import classify_source_type, rank_search_results


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_source_type_and_official_ranking() -> None:
    results = [
        {"title": "민간 요약", "url": "https://govhelpers.com/a", "snippet": ""},
        {"title": "블로그", "url": "https://blog.naver.com/a", "snippet": ""},
        {"title": "기업마당 공고", "url": "https://www.bizinfo.go.kr/a", "snippet": ""},
        {"title": "디자인진흥원 공고", "url": "https://kidp.or.kr/a", "snippet": ""},
        {"title": "부산 공고", "url": "https://busan.go.kr/a", "snippet": ""},
        {"title": "디자인센터 공고", "url": "https://dcb.or.kr/a", "snippet": ""},
        {"title": "서울디자인재단 공고", "url": "https://seouldesign.or.kr/a", "snippet": ""},
    ]
    ranked = rank_search_results(results)
    assert_true(classify_source_type("https://govhelpers.com/a") == "intermediary", "govhelpers intermediary")
    for host in ("bizinfo.go.kr", "kidp.or.kr", "busan.go.kr", "dcb.or.kr", "seouldesign.or.kr"):
        assert_true(classify_source_type(f"https://{host}/a") == "official", f"{host} official")
    assert_true([item["source_type"] for item in ranked[:5]] == ["official"] * 5, "officials first")
    assert_true(ranked[-1]["source_type"] == "intermediary", "intermediary last")


def main() -> int:
    test_source_type_and_official_ranking()
    print("PASS test_source_type_and_official_ranking")
    print("All company agent web reference ranking tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
