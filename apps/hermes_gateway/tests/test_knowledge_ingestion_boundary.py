"""Phase 34A knowledge ingestion boundary tests."""

from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from knowledge_ingestion_boundary import (
    build_knowledge_ingestion_boundary_report,
    classify_knowledge_extension,
    render_knowledge_ingestion_boundary_markdown,
    validate_knowledge_source,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_canonical_sources_and_operation() -> None:
    report = build_knowledge_ingestion_boundary_report()
    assert_true("operation" in report["canonical_sources"], "operation source should exist")
    assert_true("operations" not in report["canonical_sources"], "operations should not be canonical")


def test_operations_source_forbidden() -> None:
    validation = validate_knowledge_source("operations")
    assert_true(validation["valid"] is False, "operations should be forbidden")
    assert_true(validation["suggested_source"] == "operation", "operations should suggest operation")


def test_extension_classification() -> None:
    assert_true(classify_knowledge_extension("x.md")["status"] == "allowed", "md should be allowed")
    assert_true(classify_knowledge_extension("x.pdf")["status"] == "deferred", "pdf should be deferred")
    assert_true(classify_knowledge_extension("x.env")["status"] == "blocked", ".env should be blocked")
    assert_true(classify_knowledge_extension("x.exe")["status"] == "blocked", ".exe should be blocked")


def test_safety_flags_false_and_markdown() -> None:
    report = build_knowledge_ingestion_boundary_report()
    assert_true(report["ready_for_local_text_ingestion"] is True, "Local text ingestion should be ready")
    assert_true(report["ready_for_embedding"] is False, "Embedding should be deferred")
    assert_true(report["ready_for_external_sources"] is False, "External sources should be deferred")
    assert_true(report["embedding_api_called"] is False, "Embedding API false")
    assert_true(report["llm_api_called"] is False, "LLM API false")
    assert_true(report["discord_message_sent"] is False, "Discord false")
    assert_true(report["external_execution"] is False, "External false")
    assert_true("Knowledge Ingestion Boundary" in render_knowledge_ingestion_boundary_markdown(report), "Markdown should render")


def main() -> int:
    tests = [
        test_canonical_sources_and_operation,
        test_operations_source_forbidden,
        test_extension_classification,
        test_safety_flags_false_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All knowledge ingestion boundary tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
