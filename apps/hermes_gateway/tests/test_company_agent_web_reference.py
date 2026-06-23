from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_web_reference import build_agent_search_queries, detect_web_reference_intent


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_korean_intent_and_normalized_query() -> None:
    message = "이번 달 디자인 지원사업 후보 찾아줘"
    assert_true(detect_web_reference_intent("kasumi", message, {"command": "kasumi"}), "Kasumi Korean intent")
    queries = build_agent_search_queries("kasumi", message, {"command": "kasumi"})
    normalized = queries[0]
    for term in ("2026년", "6월", "전국", "중소기업", "디자인", "디자인개발", "지원대상", "지원내용", "마감"):
        assert_true(term in normalized, f"normalized query includes {term}")


def main() -> int:
    test_korean_intent_and_normalized_query()
    print("PASS test_korean_intent_and_normalized_query")
    print("All company agent web reference base tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
