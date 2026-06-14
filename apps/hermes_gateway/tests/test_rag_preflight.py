"""Phase 33A RAG preflight tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_preflight import build_rag_preflight_report, render_rag_preflight_markdown
from rag_source_registry import get_canonical_rag_sources, validate_rag_source_name


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_default_no_retrieval() -> None:
    report = build_rag_preflight_report()
    assert_true(report["ready_for_rag_retrieval"] is False, "Phase 33A should not be ready for retrieval")
    assert_true(report["rag_enabled"] is False, "RAG should be disabled")
    assert_true(report["retrieval_executed"] is False, "Retrieval must not run")


def test_no_external_calls() -> None:
    report = build_rag_preflight_report()
    assert_true(report["embedding_api_called"] is False, "Embedding API should not be called")
    assert_true(report["llm_api_called"] is False, "LLM API should not be called")
    assert_true(report["discord_message_sent"] is False, "Discord send should be false")
    assert_true(report["external_execution"] is False, "External execution should be false")


def test_source_validation() -> None:
    assert_true(validate_rag_source_name("operation")["valid"] is True, "operation should be valid")
    operations = validate_rag_source_name("operations")
    assert_true(operations["valid"] is False, "operations should be invalid")
    assert_true(operations["suggested_source"] == "operation", "operations should suggest operation")
    assert_true(validate_rag_source_name("unknown")["valid"] is False, "unknown should be invalid")


def test_canonical_sources_exact() -> None:
    assert_true(get_canonical_rag_sources() == ["marketing", "operation", "strategy", "brand", "archive"], "Canonical sources should match exactly")


def test_safe_and_markdown() -> None:
    report = build_rag_preflight_report()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secret values should appear")
    assert_true(not LONG_ID_RE.search(text), "No raw Discord-like IDs should appear")
    assert_true("STOXL RAG Preflight" in render_rag_preflight_markdown(report), "Markdown should render")
    assert_true(report["ready_for_phase33b_local_readonly_retrieval"] is True, "Phase 33B readiness should be true")


def test_example_json_safe() -> None:
    data = json.loads((APP_DIR / "examples" / "rag_preflight_report.example.json").read_text(encoding="utf-8"))
    text = json.dumps(data, ensure_ascii=False)
    assert_true(not LONG_ID_RE.search(text), "Example should not contain raw IDs")
    assert_true(data["safety_assertions"]["embedding_called"] is False, "Example embedding false")


def main() -> int:
    tests = [
        test_default_no_retrieval,
        test_no_external_calls,
        test_source_validation,
        test_canonical_sources_exact,
        test_safe_and_markdown,
        test_example_json_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
