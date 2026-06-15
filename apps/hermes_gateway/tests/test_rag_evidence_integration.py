"""Phase 34D RAG evidence integration tests."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_integration import build_rag_evidence_integration_report, render_rag_evidence_integration_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_root() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    base = Path(temp.name) / "knowledge" / "operation"
    base.mkdir(parents=True)
    for index in range(7):
        (base / f"doc_{index}.md").write_text("STOXL brand tone local review evidence. " * 40, encoding="utf-8")
    return temp


def test_operation_source_accepted() -> None:
    with make_root() as temp:
        report = build_rag_evidence_integration_report(temp, source="operation", agent="kasumi", query="STOXL brand tone")
        assert_true(report["source_valid"] is True, "operation should be valid")
        assert_true(report["rag_response_packet_created"] is True, "RAG packet should be created")


def test_operations_source_blocked_before_packet_creation() -> None:
    with make_root() as temp:
        report = build_rag_evidence_integration_report(temp, source="operations", agent="kasumi")
        assert_true(report["source_valid"] is False, "operations should be invalid")
        assert_true(report["rag_response_packet_created"] is False, "Invalid source should not create available packet")


def test_unknown_source_blocked() -> None:
    with make_root() as temp:
        report = build_rag_evidence_integration_report(temp, source="unknown", agent="kasumi")
        assert_true(report["source_valid"] is False, "unknown source should be invalid")
        assert_true(report["ready_for_private_test_review"] is False, "Unknown source should not be ready")


def test_agent_source_routing() -> None:
    with make_root() as temp:
        kasumi = build_rag_evidence_integration_report(temp, source="operation", agent="kasumi")
        marin = build_rag_evidence_integration_report(temp, source="operation", agent="marin")
        unknown = build_rag_evidence_integration_report(temp, source="operation", agent="unknown")
        assert_true(kasumi["agent_source_allowed"] is True, "kasumi can use operation")
        assert_true(marin["agent_source_allowed"] is False, "marin cannot use operation")
        assert_true(unknown["agent_source_allowed"] is False, "unknown agent should block")


def test_evidence_included_in_rag_response_packet() -> None:
    with make_root() as temp:
        report = build_rag_evidence_integration_report(temp, source="operation", agent="kasumi")
        packet = report["rag_response_packet"]
        assert_true("evidence_packet" in packet, "Evidence packet should be included")
        assert_true("citation_summary" in packet, "Citation summary should be included")
        assert_true(packet["evidence_packet"]["content_preview_only"] is True, "Preview only should be true")


def test_relative_paths_and_limits() -> None:
    with make_root() as temp:
        report = build_rag_evidence_integration_report(temp, source="operation", agent="kasumi", max_documents=5, max_excerpt_chars=600)
        citations = report["rag_response_packet"]["evidence_packet"]["citations"]
        assert_true(len(citations) <= 5, "Max documents should be enforced")
        assert_true(all(item["char_count"] <= 600 for item in citations), "Max excerpt chars should be enforced")
        assert_true(report["relative_paths_only"] is True, "Relative paths only")


def test_full_content_and_runtime_flags_false() -> None:
    with make_root() as temp:
        report = build_rag_evidence_integration_report(temp, source="operation", agent="kasumi")
        assert_true(report["full_content_included"] is False, "Full content false")
        assert_true(report["content_preview_only"] is True, "Preview only true")
        assert_true(report["ready_for_llm_prompt"] is False, "LLM prompt false")
        assert_true(report["ready_for_private_test_review"] is True, "Private test review true")
        assert_true(report["ready_for_embedding"] is False, "Embedding ready false")
        assert_true(report["ready_for_external_sources"] is False, "External sources ready false")
        assert_true(report["embedding_api_called"] is False, "Embedding API false")
        assert_true(report["llm_api_called"] is False, "LLM API false")
        assert_true(report["discord_message_sent"] is False, "Discord false")
        assert_true(report["external_execution"] is False, "External false")


def test_secret_like_content_and_raw_id_not_logged() -> None:
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp) / "knowledge" / "operation"
        base.mkdir(parents=True)
        (base / "secret.md").write_text("STOXL brand tone token=secret 123456789012345678", encoding="utf-8")
        report = build_rag_evidence_integration_report(temp, source="operation", agent="kasumi", query="STOXL brand tone")
        text = json.dumps(report, ensure_ascii=False).lower()
        assert_true("token=secret" not in text, "Secret-like content should not be logged")
        assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like ID should not be logged")


def test_markdown_render() -> None:
    with make_root() as temp:
        markdown = render_rag_evidence_integration_markdown(build_rag_evidence_integration_report(temp))
        assert_true("RAG Evidence Integration" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_operation_source_accepted,
        test_operations_source_blocked_before_packet_creation,
        test_unknown_source_blocked,
        test_agent_source_routing,
        test_evidence_included_in_rag_response_packet,
        test_relative_paths_and_limits,
        test_full_content_and_runtime_flags_false,
        test_secret_like_content_and_raw_id_not_logged,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence integration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
