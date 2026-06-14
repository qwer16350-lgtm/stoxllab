"""Phase 33B local read-only RAG retrieval tests."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_local_retrieval import run_rag_local_retrieval, render_rag_local_retrieval_markdown


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_root() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    base = root / "knowledge" / "operation"
    base.mkdir(parents=True)
    (base / "example.md").write_text("STOXL brand tone is calm and review-only.", encoding="utf-8")
    (base / "data.json").write_text('{"note": "STOXL brand tone json"}', encoding="utf-8")
    (base / "skip.exe").write_text("STOXL brand tone should skip", encoding="utf-8")
    (root / ".env").write_text("TOKEN=secret", encoding="utf-8")
    (root / "exports").mkdir()
    (root / "exports" / "export.md").write_text("STOXL brand tone export skip", encoding="utf-8")
    (root / "logs").mkdir()
    (root / "logs" / "log.md").write_text("STOXL brand tone log skip", encoding="utf-8")
    (root / "apps" / "hermes_gateway" / "local").mkdir(parents=True)
    (root / "apps" / "hermes_gateway" / "local" / "mapping.md").write_text("STOXL brand tone local skip", encoding="utf-8")
    return temp


def test_missing_source_folder_warning() -> None:
    with tempfile.TemporaryDirectory() as temp:
        report = run_rag_local_retrieval(temp, source="operation")
        assert_true(report["missing_source_folder_warning"] is True, "Missing folder should warn")
        assert_true(report["documents_returned"] == 0, "Missing folder should return no docs")


def test_operation_valid_and_operations_invalid() -> None:
    with make_root() as temp:
        valid = run_rag_local_retrieval(temp, source="operation")
        invalid = run_rag_local_retrieval(temp, source="operations")
        unknown = run_rag_local_retrieval(temp, source="unknown")
        assert_true(valid["source_valid"] is True, "operation should be valid")
        assert_true(invalid["source_valid"] is False, "operations should be invalid")
        assert_true(invalid["source_validation"]["suggested_source"] == "operation", "operations should suggest operation")
        assert_true(unknown["source_valid"] is False, "unknown should be invalid")


def test_allowed_and_disallowed_extensions() -> None:
    with make_root() as temp:
        report = run_rag_local_retrieval(temp, source="operation", query="STOXL brand tone")
        paths = [item["path"] for item in report["results"]]
        assert_true(any(path.endswith("example.md") for path in paths), "Allowed md should be read")
        assert_true(all(not path.endswith(".exe") for path in paths), "Disallowed extension should skip")


def test_exclusions_and_path_safety() -> None:
    with make_root() as temp:
        report = run_rag_local_retrieval(temp, source="operation", query="STOXL brand tone")
        text = json.dumps(report, ensure_ascii=False)
        assert_true(".env" not in text, ".env should be excluded")
        assert_true("exports/" not in text, "exports should be excluded")
        assert_true("logs/" not in text, "logs should be excluded")
        assert_true("apps/hermes_gateway/local" not in text, "local mapping should be excluded")


def test_local_only_flags_and_markdown() -> None:
    with make_root() as temp:
        report = run_rag_local_retrieval(temp, source="operation")
        assert_true(report["local_read_only"] is True, "Retrieval should be local read-only")
        assert_true(report["embedding_api_called"] is False, "Embedding false")
        assert_true(report["llm_api_called"] is False, "LLM false")
        assert_true(report["discord_message_sent"] is False, "Discord false")
        assert_true(report["external_execution"] is False, "External false")
        assert_true(report["safety_assertions"]["write_performed"] is False, "Write false")
        assert_true("STOXL RAG Local" in render_rag_local_retrieval_markdown(report), "Markdown should render")


def test_redaction_and_example_safe() -> None:
    with make_root() as temp:
        path = Path(temp) / "knowledge" / "operation" / "secret.md"
        path.write_text("STOXL brand tone token=secret 123456789012345678", encoding="utf-8")
        report = run_rag_local_retrieval(temp, source="operation", query="STOXL brand tone")
        text = json.dumps(report, ensure_ascii=False).lower()
        assert_true("token=secret" not in text, "Token-like values should be redacted")
        assert_true(not LONG_ID_RE.search(text), "Raw Discord IDs should be absent")
    example = json.loads((APP_DIR / "examples" / "rag_local_retrieval_report.example.json").read_text(encoding="utf-8"))
    assert_true(example["embedding_api_called"] is False, "Example embedding false")


def main() -> int:
    tests = [
        test_missing_source_folder_warning,
        test_operation_valid_and_operations_invalid,
        test_allowed_and_disallowed_extensions,
        test_exclusions_and_path_safety,
        test_local_only_flags_and_markdown,
        test_redaction_and_example_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG local retrieval tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
