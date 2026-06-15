"""Phase 34H-0 no-API RAG evidence LLM dry readiness tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_llm_dry_readiness import build_rag_evidence_llm_dry_readiness_report, render_rag_evidence_llm_dry_readiness_markdown


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_dry_readiness_uses_prompt_envelope() -> None:
    report = build_rag_evidence_llm_dry_readiness_report(ROOT)
    assert_true(report["prompt_envelope_available"] is True, "Prompt envelope should be available")
    assert_true(report["prompt_safety_allowed"] is True, "Prompt safety should be allowed")


def test_mock_response_and_packet_created() -> None:
    report = build_rag_evidence_llm_dry_readiness_report(ROOT)
    assert_true(report["mock_response_created"] is True, "Mock response should be created")
    assert_true(report["mock_response_safety_allowed"] is True, "Mock response safety should pass")
    assert_true(report["llm_response_packet_created"] is True, "LLM response packet should be created")
    assert_true(report["mock_response"]["review_only"] is True, "Mock response should be review-only")


def test_readiness_flags() -> None:
    report = build_rag_evidence_llm_dry_readiness_report(ROOT)
    assert_true(report["ready_for_actual_llm_dry_call"] is True, "Next-phase dry call readiness should be true")
    assert_true(report["actual_llm_api_call"] is False, "Actual LLM API call false")
    assert_true(report["ready_for_discord_send"] is False, "Discord send false")
    assert_true(report["ready_for_embedding"] is False, "Embedding false")
    assert_true(report["ready_for_external_sources"] is False, "External sources false")
    assert_true(report["embedding_api_called"] is False, "Embedding API false")
    assert_true(report["discord_message_sent"] is False, "Discord false")
    assert_true(report["external_execution"] is False, "External false")


def test_no_sensitive_values() -> None:
    report = build_rag_evidence_llm_dry_readiness_report(ROOT)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("token=" not in text and "api_key=" not in text and "sk-" not in text, "Secret-like values should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_llm_dry_readiness_markdown(build_rag_evidence_llm_dry_readiness_report(ROOT))
    assert_true("RAG Evidence LLM Dry Readiness" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_dry_readiness_uses_prompt_envelope,
        test_mock_response_and_packet_created,
        test_readiness_flags,
        test_no_sensitive_values,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence LLM dry readiness tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
