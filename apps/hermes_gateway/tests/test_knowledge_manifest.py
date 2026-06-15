"""Phase 34A knowledge manifest tests."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from knowledge_manifest import build_knowledge_manifest, render_knowledge_manifest_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_root() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    for source in ["marketing", "operation", "strategy", "brand", "archive"]:
        (root / "knowledge" / source).mkdir(parents=True)
        (root / "knowledge" / source / ".gitkeep").write_text("", encoding="utf-8")
    (root / "knowledge" / "operation" / "allowed.md").write_text("token=secret 123456789012345678", encoding="utf-8")
    (root / "knowledge" / "operation" / "deferred.pdf").write_text("fake", encoding="utf-8")
    (root / "knowledge" / "operation" / "blocked.env").write_text("TOKEN=secret", encoding="utf-8")
    return temp


def test_canonical_source_folders_exist() -> None:
    with make_root() as temp:
        report = build_knowledge_manifest(temp)
        for source in ["marketing", "operation", "strategy", "brand", "archive"]:
            assert_true(report["sources"][source]["exists"] is True, f"{source} should exist")


def test_operation_exists_and_operations_forbidden() -> None:
    with make_root() as temp:
        report = build_knowledge_manifest(temp)
        assert_true("operation" in report["canonical_sources"], "operation should be canonical")
        assert_true("operations" not in report["canonical_sources"], "operations should not be canonical")
        assert_true(report["operations_source_present"] is False, "operations folder should be absent")


def test_extension_counts() -> None:
    with make_root() as temp:
        counts = build_knowledge_manifest(temp)["sources"]["operation"]["counts"]
        assert_true(counts["allowed"] == 1, "Allowed file should count")
        assert_true(counts["deferred"] == 1, "Deferred file should count")
        assert_true(counts["blocked"] == 1, "Blocked file should count")


def test_manifest_does_not_dump_content_or_secrets() -> None:
    with make_root() as temp:
        report = build_knowledge_manifest(temp)
        text = json.dumps(report, ensure_ascii=False).lower()
        assert_true("token=secret" not in text, "File content should not be dumped")
        assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")
        assert_true(report["full_content_included"] is False, "Full content should be false")


def test_safety_flags_and_markdown() -> None:
    with make_root() as temp:
        report = build_knowledge_manifest(temp)
        assert_true(report["ready_for_local_text_ingestion"] is True, "Local text ingestion true")
        assert_true(report["ready_for_embedding"] is False, "Embedding false")
        assert_true(report["ready_for_external_sources"] is False, "External sources false")
        assert_true(report["embedding_api_called"] is False, "Embedding API false")
        assert_true(report["llm_api_called"] is False, "LLM API false")
        assert_true(report["discord_message_sent"] is False, "Discord false")
        assert_true(report["external_execution"] is False, "External false")
        assert_true("Knowledge Manifest" in render_knowledge_manifest_markdown(report), "Markdown should render")


def main() -> int:
    tests = [
        test_canonical_source_folders_exist,
        test_operation_exists_and_operations_forbidden,
        test_extension_counts,
        test_manifest_does_not_dump_content_or_secrets,
        test_safety_flags_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All knowledge manifest tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
