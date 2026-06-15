"""Phase 34E RAG evidence review packet tests."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_review_packet import build_rag_evidence_review_packet, render_rag_evidence_review_packet_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_root() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    base = Path(temp.name) / "knowledge" / "operation"
    base.mkdir(parents=True)
    (base / "sample.md").write_text("STOXL brand tone review-only operation evidence.", encoding="utf-8")
    return temp


def test_review_packet_operation_accepted() -> None:
    with make_root() as temp:
        packet = build_rag_evidence_review_packet(temp, source="operation", agent="kasumi")
        assert_true(packet["source_valid"] is True, "operation should be valid")
        assert_true(packet["agent_source_allowed"] is True, "kasumi operation should be allowed")
        assert_true(packet["ready_for_private_test_review"] is True, "Review should be ready")


def test_review_packet_operations_blocked() -> None:
    with make_root() as temp:
        packet = build_rag_evidence_review_packet(temp, source="operations", agent="kasumi")
        assert_true(packet["source_valid"] is False, "operations should be invalid")
        assert_true(packet["ready_for_private_test_review"] is False, "Blocked source should not be ready")


def test_review_packet_requires_rag_and_evidence() -> None:
    integration = {
        "source": "operation",
        "source_valid": True,
        "agent": "kasumi",
        "agent_source_allowed": True,
        "rag_response_packet_created": False,
        "evidence_packet_available": False,
        "rag_response_packet": {},
    }
    packet = build_rag_evidence_review_packet(integration_report=integration)
    assert_true(packet["rag_response_packet_available"] is False, "RAG packet should be required")
    assert_true(packet["evidence_packet_available"] is False, "Evidence packet should be required")
    assert_true(packet["ready_for_private_test_review"] is False, "Missing packet should not be ready")


def test_review_only_and_runtime_flags() -> None:
    with make_root() as temp:
        packet = build_rag_evidence_review_packet(temp, source="operation", agent="kasumi")
        assert_true(packet["review_only"] is True, "Review only true")
        assert_true(packet["human_review_required"] is True, "Human review required")
        assert_true(packet["ready_for_llm_prompt"] is False, "LLM prompt false")
        assert_true(packet["ready_for_discord_send"] is False, "Discord send false")
        assert_true(packet["ready_for_embedding"] is False, "Embedding false")
        assert_true(packet["ready_for_external_sources"] is False, "External sources false")
        assert_true(packet["embedding_api_called"] is False, "Embedding API false")
        assert_true(packet["llm_api_called"] is False, "LLM API false")
        assert_true(packet["discord_message_sent"] is False, "Discord false")
        assert_true(packet["external_execution"] is False, "External false")


def test_markdown_render() -> None:
    with make_root() as temp:
        markdown = render_rag_evidence_review_packet_markdown(build_rag_evidence_review_packet(temp))
        assert_true("RAG Evidence Review Packet" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_review_packet_operation_accepted,
        test_review_packet_operations_blocked,
        test_review_packet_requires_rag_and_evidence,
        test_review_only_and_runtime_flags,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence review packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
