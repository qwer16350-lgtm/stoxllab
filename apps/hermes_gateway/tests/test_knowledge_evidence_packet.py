"""Phase 34C knowledge evidence packet tests."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from knowledge_evidence_packet import build_knowledge_evidence_packet, render_knowledge_evidence_packet_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_retrieval_report(count: int = 7, chars: int = 800) -> dict:
    return {
        "report_type": "rag_local_retrieval_report",
        "source": "operation",
        "source_valid": True,
        "query_preview": "STOXL brand tone",
        "results": [
            {
                "source": "operation",
                "path": f"knowledge/operation/doc_{index}.md",
                "excerpt": "A" * chars,
                "char_count": chars,
            }
            for index in range(count)
        ],
    }


def test_evidence_packet_structure() -> None:
    packet = build_knowledge_evidence_packet(retrieval_report=make_retrieval_report(1), source="operation", agent="kasumi")
    assert_true(packet["report_type"] == "knowledge_evidence_packet", "Packet type should match")
    assert_true(packet["source"] == "operation", "Source should be operation")
    assert_true(packet["agent"] == "kasumi", "Agent should be kasumi")
    assert_true(packet["agent_source_allowed"] is True, "Kasumi operation should be allowed")


def test_relative_paths_only() -> None:
    report = make_retrieval_report(1)
    report["results"][0]["path"] = "C:/tmp/STOXL_LAB/knowledge/operation/doc.md"
    packet = build_knowledge_evidence_packet(retrieval_report=report, source="operation", agent="kasumi")
    assert_true(packet["citations"][0]["relative_path"] == "absolute_path_redacted", "Absolute path should redact")


def test_max_documents_enforced() -> None:
    packet = build_knowledge_evidence_packet(retrieval_report=make_retrieval_report(7), source="operation", agent="kasumi", max_documents=5)
    assert_true(len(packet["documents"]) == 5, "Max documents should be enforced")
    assert_true(len(packet["citations"]) == 5, "Max citations should be enforced")


def test_max_excerpt_chars_enforced() -> None:
    packet = build_knowledge_evidence_packet(retrieval_report=make_retrieval_report(1, chars=900), source="operation", agent="kasumi", max_excerpt_chars=600)
    assert_true(packet["citations"][0]["char_count"] == 600, "Excerpt should be limited")


def test_full_content_and_runtime_flags_false() -> None:
    packet = build_knowledge_evidence_packet(retrieval_report=make_retrieval_report(1), source="operation", agent="kasumi")
    assert_true(packet["full_content_included"] is False, "Full content false")
    assert_true(packet["content_preview_only"] is True, "Preview only true")
    assert_true(packet["ready_for_rag_response_packet"] is True, "Ready for RAG response packet")
    assert_true(packet["ready_for_llm_prompt"] is False, "LLM prompt false")
    assert_true(packet["embedding_api_called"] is False, "Embedding false")
    assert_true(packet["llm_api_called"] is False, "LLM false")
    assert_true(packet["discord_message_sent"] is False, "Discord false")
    assert_true(packet["external_execution"] is False, "External false")


def test_source_routing_blocks() -> None:
    blocked = build_knowledge_evidence_packet(retrieval_report=make_retrieval_report(1), source="marketing", agent="kasumi")
    assert_true(blocked["agent_source_allowed"] is False, "Kasumi marketing should block")
    assert_true(blocked["ready_for_rag_response_packet"] is False, "Blocked route should not be ready")
    operations = build_knowledge_evidence_packet(retrieval_report=make_retrieval_report(1), source="operations", agent="kasumi")
    assert_true(operations["source_valid"] is False, "operations should be invalid")


def test_secret_and_raw_id_redacted() -> None:
    report = make_retrieval_report(1)
    report["results"][0]["excerpt"] = "token=secret 123456789012345678"
    packet = build_knowledge_evidence_packet(retrieval_report=report, source="operation", agent="kasumi")
    text = json.dumps(packet, ensure_ascii=False).lower()
    assert_true("token=secret" not in text, "Token-like value should be redacted")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like ID should be absent")


def test_default_empty_packet_and_markdown() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "knowledge" / "operation").mkdir(parents=True)
        packet = build_knowledge_evidence_packet(root=temp, source="operation", agent="kasumi")
        assert_true(packet["documents"] == [], "Empty folder should return empty docs")
        assert_true("Knowledge Evidence Packet" in render_knowledge_evidence_packet_markdown(packet), "Markdown should render")


def main() -> int:
    tests = [
        test_evidence_packet_structure,
        test_relative_paths_only,
        test_max_documents_enforced,
        test_max_excerpt_chars_enforced,
        test_full_content_and_runtime_flags_false,
        test_source_routing_blocks,
        test_secret_and_raw_id_redacted,
        test_default_empty_packet_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All knowledge evidence packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
