from __future__ import annotations

import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_rag_status_missing_index_fallback() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        result = build_company_agent_message_result("operation-brief", "!rag-status", env={"HERMES_RAG_INDEX_DIR": index_dir})
    content = result["response"]["content"]
    assert_true(result["response"]["index_available"] is False, "index missing")
    assert_true("index: not available" in content, "missing status")
    assert_true("--rag-index-nas" in content, "CLI instruction")
    assert_true(result["index_write_attempted_from_runtime"] is False, "no runtime index write")


def test_rag_search_empty_query_fallback() -> None:
    result = build_company_agent_message_result("operation-brief", "!rag-search", env={})
    content = result["response"]["content"]
    assert_true(result["response"]["blocked_reason"] == "query_missing", "query missing")
    assert_true("Please enter a search query" in content, "empty query fallback")


def test_rag_search_no_result_fallback() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        Path(index_dir, "nas_rag_index.json").write_text('{"records": []}', encoding="utf-8")
        result = build_company_agent_message_result("operation-brief", "!rag-search unknown", env={"HERMES_RAG_INDEX_DIR": index_dir})
    content = result["response"]["content"]
    assert_true(result["response"]["result_count"] == 0, "no results")
    assert_true("No matching results found" in content, "no result fallback")


def test_rag_search_long_query_is_bounded() -> None:
    result = build_company_agent_message_result("operation-brief", "!rag-search " + ("x" * 250), env={})
    assert_true(result["response"]["blocked_reason"] == "query_too_long", "long query bounded")
    assert_true("query_too_long" in result["response"]["content"], "long query reason")


def main() -> int:
    test_rag_status_missing_index_fallback()
    print("PASS test_rag_status_missing_index_fallback")
    test_rag_search_empty_query_fallback()
    print("PASS test_rag_search_empty_query_fallback")
    test_rag_search_no_result_fallback()
    print("PASS test_rag_search_no_result_fallback")
    test_rag_search_long_query_is_bounded()
    print("PASS test_rag_search_long_query_is_bounded")
    print("All RAG Discord index missing/fallback tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
