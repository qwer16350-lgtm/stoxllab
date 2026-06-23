from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_web_reference import cleanup_html_to_text, extract_official_source_details, fetch_official_source_text


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeResponse:
    def __init__(self, body: str) -> None:
        self.body = body.encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int = -1) -> bytes:
        return self.body


def fake_opener(request, timeout: int = 15) -> FakeResponse:
    assert_true(request.get_method() == "GET", "official fetch must use GET")
    assert_true(timeout <= 15, "timeout bounded")
    return FakeResponse(
        """
        <html><head><style>.x{}</style><script>alert(1)</script></head>
        <body><header>menu</header><nav>nav</nav><main class="board_view">
        <h1>2026 디자인개발 지원사업 모집 공고</h1>
        신청기간 2026년 6월 9일 ~ 2026년 6월 25일.
        지원대상 중소기업 및 디자인 전문기업.
        지원내용 제품디자인 BI CI 패키지 UX UI 지원금 최대 2천만원.
        자부담 기업부담금 20%.
        제출서류 신청서 사업계획서 사업자등록증.
        신청방법 온라인 접수 기업마당 신청서 제출.
        문의처 디자인지원팀.
        </main><footer>footer</footer></body></html>
        """
    )


def test_fetch_official_source_text_get_only_and_cleanup() -> None:
    fetched = fetch_official_source_text("https://www.bizinfo.go.kr/notice/1", opener=fake_opener)
    assert_true(fetched["fetch_attempted"] is True, "official fetch attempted")
    assert_true(fetched["fetch_succeeded"] is True, "official fetch succeeded")
    assert_true("alert" not in fetched["text"], "script removed")
    assert_true("footer" not in fetched["text"], "footer removed")
    assert_true("지원대상 중소기업" in fetched["text"], "body extracted")
    assert_true(fetched["external_execution"] is False, "no external")


def test_intermediary_source_is_not_fetched_by_default() -> None:
    fetched = fetch_official_source_text("https://govhelpers.com/support/1", opener=fake_opener)
    assert_true(fetched["fetch_attempted"] is False, "intermediary fetch skipped")
    assert_true(fetched["failure_reason"] == "non_official_source", "safe reason")


def test_official_extract_failure_does_not_break_flow() -> None:
    def failed_fetch(_url: str) -> dict:
        return {"fetch_attempted": True, "fetch_succeeded": False, "failure_reason": "timeout", "text": ""}

    result = extract_official_source_details(
        [
            {
                "title": "2026 디자인개발 지원사업 모집 공고",
                "url": "https://www.bizinfo.go.kr/notice/1",
                "snippet": "신청기간 2026.05.06 ~ 2026.06.25 지원대상 중소기업 지원내용 디자인개발",
                "institution": "기업마당",
            }
        ],
        official_fetcher=failed_fetch,
    )
    assert_true(result["official_extract_attempted"] is True, "attempted")
    assert_true(result["official_extract_failed_count"] == 1, "failed count")
    assert_true(result["candidate_extraction_succeeded"] is True, "summary fallback")
    assert_true(result["ready_for_meiko_verification"] is True, "flow continues")


def test_cleanup_html_to_text_removes_noise() -> None:
    text = cleanup_html_to_text("<nav>menu</nav><article>본문 공고내용</article><footer>foot</footer>")
    assert_true("본문 공고내용" in text, "content kept")
    assert_true("menu" not in text and "foot" not in text, "chrome removed")


def main() -> int:
    for test in (
        test_fetch_official_source_text_get_only_and_cleanup,
        test_intermediary_source_is_not_fetched_by_default,
        test_official_extract_failure_does_not_break_flow,
        test_cleanup_html_to_text_removes_noise,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All company agent web reference official extract tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
