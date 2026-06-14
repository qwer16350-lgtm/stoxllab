"""Phase 33D RAG context safety tests."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_context_safety import build_rag_context_safety_report, render_rag_context_safety_markdown
from rag_local_retrieval import run_rag_local_retrieval


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def retrieval(results: list[dict], source: str = "operation") -> dict:
    return {"source": source, "source_valid": source == "operation", "results": results}


def test_safe_local_retrieval_context_allowed() -> None:
    report = build_rag_context_safety_report(retrieval([{"source": "operation", "path": "knowledge/operation/a.md", "excerpt": "safe context"}]))
    assert_true(report["allowed_for_llm_prompt"] is True, "Safe context should be allowed")


def test_too_many_docs_blocked() -> None:
    results = [{"source": "operation", "path": f"knowledge/operation/{idx}.md", "excerpt": "safe"} for idx in range(6)]
    assert_true("too_many_documents" in build_rag_context_safety_report(retrieval(results), max_documents=5)["blocked_reasons"], "Too many docs should block")


def test_too_many_chars_blocked() -> None:
    report = build_rag_context_safety_report(retrieval([{"path": "knowledge/operation/a.md", "excerpt": "x" * 20}]), max_context_chars=10)
    assert_true("context_too_large" in report["blocked_reasons"], "Large context should block")


def test_operations_source_blocked() -> None:
    report = build_rag_context_safety_report(retrieval([], source="operations"), source="operations")
    assert_true("invalid_source" in report["blocked_reasons"], "operations should be invalid")
    assert_true("operations_source_not_allowed" in report["blocked_reasons"], "operations should be explicitly blocked")


def test_absolute_path_and_runtime_paths_blocked() -> None:
    report = build_rag_context_safety_report(retrieval([{"path": "C:\\Users\\name\\.env", "excerpt": "safe"}]))
    assert_true("absolute_private_path_detected" in report["blocked_reasons"], "Absolute paths should block")
    assert_true("blocked_runtime_path_detected" in report["blocked_reasons"], "Runtime paths should block")


def test_secret_and_raw_id_blocked() -> None:
    secret = build_rag_context_safety_report(retrieval([{"path": "knowledge/operation/a.md", "excerpt": "token=secret"}]))
    raw_id = build_rag_context_safety_report(retrieval([{"path": "knowledge/operation/a.md", "excerpt": "123456789012345678"}]))
    assert_true("secret_like_value_detected" in secret["blocked_reasons"], "Secret-like values should block")
    assert_true("raw_discord_id_detected" in raw_id["blocked_reasons"], "Raw Discord IDs should block")


def test_binary_content_blocked() -> None:
    report = build_rag_context_safety_report(retrieval([{"path": "knowledge/operation/a.md", "excerpt": "abc\x00def"}]))
    assert_true("binary_content_detected" in report["blocked_reasons"], "Binary-like content should block")


def test_local_retrieval_report_and_markdown_safe() -> None:
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp) / "knowledge" / "operation"
        base.mkdir(parents=True)
        (base / "safe.md").write_text("STOXL brand tone safe context.", encoding="utf-8")
        local = run_rag_local_retrieval(temp, query="STOXL brand tone")
        report = build_rag_context_safety_report(local)
        assert_true(report["llm_api_called"] is False, "No LLM")
        assert_true(report["discord_message_sent"] is False, "No Discord send")
        assert_true("STOXL RAG Context Safety" in render_rag_context_safety_markdown(report), "Markdown should render")


def main() -> int:
    tests = [
        test_safe_local_retrieval_context_allowed,
        test_too_many_docs_blocked,
        test_too_many_chars_blocked,
        test_operations_source_blocked,
        test_absolute_path_and_runtime_paths_blocked,
        test_secret_and_raw_id_blocked,
        test_binary_content_blocked,
        test_local_retrieval_report_and_markdown_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG context safety tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
