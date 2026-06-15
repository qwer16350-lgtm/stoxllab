"""Phase 33C RAG response packet tests."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from operations_packet_viewer import build_operations_packet_viewer_report
from rag_local_retrieval import run_rag_local_retrieval
from rag_response_packet import build_rag_response_packet, build_rag_response_packet_report, render_rag_response_packet_markdown


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_retrieval_root() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    base = Path(temp.name) / "knowledge" / "operation"
    base.mkdir(parents=True)
    (base / "example.md").write_text("STOXL brand tone citation text.", encoding="utf-8")
    return temp


def test_retrieval_report_to_packet() -> None:
    with make_retrieval_root() as temp:
        retrieval = run_rag_local_retrieval(temp, source="operation", query="STOXL brand tone")
        packet = build_rag_response_packet(retrieval)
        assert_true(packet["packet_type"] == "rag_response_packet", "Packet should be created")
        assert_true(packet["source_valid"] is True, "Source should be valid")
        assert_true(packet["response_available"] is True, "Valid source packet should be available")


def test_missing_folder_warning_reflected() -> None:
    with tempfile.TemporaryDirectory() as temp:
        packet = build_rag_response_packet_report(temp)
        assert_true(packet["retrieval_summary"]["missing_source_folder_warning"] is True, "Missing folder warning should be reflected")


def test_invalid_source_packet_available_false() -> None:
    with tempfile.TemporaryDirectory() as temp:
        packet = build_rag_response_packet_report(temp, source="operations")
        assert_true(packet["source_valid"] is False, "Invalid source should be reflected")
        assert_true(packet["response_available"] is False, "Invalid source should not be available")


def test_citations_and_human_review() -> None:
    with make_retrieval_root() as temp:
        packet = build_rag_response_packet_report(temp)
        assert_true(isinstance(packet["citations"], list), "Citations should be a list")
        assert_true(isinstance(packet["evidence_packet"], dict), "Evidence packet should be included")
        assert_true(isinstance(packet["citation_summary"], dict), "Citation summary should be included")
        assert_true(packet["evidence_packet"]["full_content_included"] is False, "Full content should be false")
        assert_true(packet["evidence_packet"]["content_preview_only"] is True, "Preview only should be true")
        assert_true(packet["citation_summary"]["relative_paths_only"] is True, "Relative paths only")
        assert_true(packet["human_review"]["required"] is True, "Human review should be required")
        disallowed = packet["human_review"]["disallowed_actions"]
        assert_true("auto_reply" in disallowed, "auto_reply should be disallowed")
        assert_true("public_publish" in disallowed, "public publish should be disallowed")
        assert_true("discord_send" in disallowed, "discord send should be disallowed")


def test_execution_flags_false_and_safe() -> None:
    packet = build_rag_response_packet_report()
    assert_true(packet["embedding_api_called"] is False, "Embedding false")
    assert_true(packet["llm_api_called"] is False, "LLM false")
    assert_true(packet["discord_message_sent"] is False, "Discord false")
    assert_true(packet["external_execution"] is False, "External false")
    text = json.dumps(packet, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text, "No secret values should appear")
    assert_true(not LONG_ID_RE.search(text), "No raw Discord IDs should appear")


def test_markdown_example_and_operations_viewer() -> None:
    packet = build_rag_response_packet_report()
    assert_true("STOXL RAG Response Packet" in render_rag_response_packet_markdown(packet), "Markdown should render")
    example = json.loads((APP_DIR / "examples" / "rag_response_packet.example.json").read_text(encoding="utf-8"))
    assert_true(example["safety_assertions"]["llm_called"] is False, "Example LLM false")
    viewer = build_operations_packet_viewer_report()
    rag = viewer["rag"]
    assert_true(rag["preflight_available"] is True, "Viewer should include RAG preflight")
    assert_true(rag["response_packet_available"] is True, "Viewer should include RAG packet")
    assert_true(rag["embedding_called"] is False, "Viewer embedding false")


def main() -> int:
    tests = [
        test_retrieval_report_to_packet,
        test_missing_folder_warning_reflected,
        test_invalid_source_packet_available_false,
        test_citations_and_human_review,
        test_execution_flags_false_and_safe,
        test_markdown_example_and_operations_viewer,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG response packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
