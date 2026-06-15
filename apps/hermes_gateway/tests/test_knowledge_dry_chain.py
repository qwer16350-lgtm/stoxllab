"""Phase 34F local sample knowledge dry chain tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from knowledge_dry_chain import SAMPLE_FILES, build_knowledge_dry_chain_report, render_knowledge_dry_chain_markdown


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_sample_operation_files_present() -> None:
    for path in SAMPLE_FILES:
        assert_true((ROOT / path).exists(), f"Sample file should exist: {path}")


def test_knowledge_dry_chain_creates_full_chain() -> None:
    report = build_knowledge_dry_chain_report(ROOT)
    assert_true(report["sample_files_present"] is True, "Sample files should be present")
    assert_true(report["manifest_available"] is True, "Manifest should be available")
    assert_true(report["evidence_packet_available"] is True, "Evidence packet should be available")
    assert_true(report["rag_response_packet_available"] is True, "RAG response packet should be available")
    assert_true(report["review_packet_available"] is True, "Review packet should be available")
    assert_true(report["citation_count"] >= 1, "At least one citation should be returned")


def test_paths_content_and_flags() -> None:
    report = build_knowledge_dry_chain_report(ROOT)
    assert_true(report["relative_paths_only"] is True, "Relative paths only")
    assert_true(report["full_content_included"] is False, "Full content false")
    assert_true(report["content_preview_only"] is True, "Preview only true")
    assert_true(report["ready_for_private_test_review"] is True, "Private test review true")
    assert_true(report["ready_for_llm_prompt"] is False, "LLM prompt false")
    assert_true(report["ready_for_discord_send"] is False, "Discord send false")
    assert_true(report["ready_for_embedding"] is False, "Embedding false")
    assert_true(report["ready_for_external_sources"] is False, "External false")


def test_no_secret_or_raw_id_logged() -> None:
    report = build_knowledge_dry_chain_report(ROOT)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text and "api_key=" not in text, "Secret-like values should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_runtime_flags_false_and_markdown() -> None:
    report = build_knowledge_dry_chain_report(ROOT)
    assert_true(report["embedding_api_called"] is False, "Embedding API false")
    assert_true(report["llm_api_called"] is False, "LLM API false")
    assert_true(report["discord_message_sent"] is False, "Discord false")
    assert_true(report["external_execution"] is False, "External false")
    assert_true("Knowledge Dry Chain" in render_knowledge_dry_chain_markdown(report), "Markdown should render")


def main() -> int:
    tests = [
        test_sample_operation_files_present,
        test_knowledge_dry_chain_creates_full_chain,
        test_paths_content_and_flags,
        test_no_secret_or_raw_id_logged,
        test_runtime_flags_false_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All knowledge dry chain tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
