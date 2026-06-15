"""Phase 34G RAG evidence prompt envelope tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_prompt_envelope import SYSTEM_INSTRUCTION, build_rag_evidence_prompt_envelope, render_rag_evidence_prompt_envelope_markdown


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_operation_source_and_agent_allowed() -> None:
    envelope = build_rag_evidence_prompt_envelope(ROOT, source="operation", agent="kasumi")
    assert_true(envelope["source_valid"] is True, "operation should be valid")
    assert_true(envelope["agent_source_allowed"] is True, "kasumi operation should be allowed")


def test_operations_and_marin_blocked() -> None:
    operations = build_rag_evidence_prompt_envelope(ROOT, source="operations", agent="kasumi")
    marin = build_rag_evidence_prompt_envelope(ROOT, source="operation", agent="marin")
    assert_true(operations["source_valid"] is False, "operations should be invalid")
    assert_true(operations["ready_for_prompt_preview"] is False, "operations should not be ready")
    assert_true(marin["agent_source_allowed"] is False, "marin operation should be blocked")


def test_system_instruction_required_text() -> None:
    envelope = build_rag_evidence_prompt_envelope(ROOT)
    system = envelope["messages_preview"][0]["content"]
    assert_true("Review-only draft." in system, "Review-only instruction required")
    assert_true("No external action has been taken." in system, "No external action statement required")
    for term in ["publish", "submit", "send", "approve", "confirm", "execute external actions"]:
        assert_true(term in system, f"System instruction should mention {term}")
    assert_true(SYSTEM_INSTRUCTION == system, "System instruction should match constant")


def test_messages_preview_and_citation_summary() -> None:
    envelope = build_rag_evidence_prompt_envelope(ROOT)
    assert_true(len(envelope["messages_preview"]) == 2, "Messages preview should include system and user")
    assert_true(envelope["citation_summary"]["citation_count"] >= 1, "Citation count should be preserved")
    assert_true(envelope["citation_summary"]["relative_paths_only"] is True, "Relative paths only")


def test_safety_flags_and_no_sensitive_values() -> None:
    envelope = build_rag_evidence_prompt_envelope(ROOT)
    assert_true(envelope["full_content_included"] is False, "Full content false")
    assert_true(envelope["content_preview_only"] is True, "Preview only true")
    assert_true(envelope["ready_for_prompt_preview"] is True, "Prompt preview true")
    assert_true(envelope["ready_for_llm_api_call"] is False, "LLM API call false")
    assert_true(envelope["ready_for_discord_send"] is False, "Discord false")
    assert_true(envelope["ready_for_embedding"] is False, "Embedding false")
    assert_true(envelope["ready_for_external_sources"] is False, "External false")
    text = json.dumps(envelope, ensure_ascii=False).lower()
    assert_true("token=" not in text and "api_key=" not in text and "sk-" not in text, "Secret-like values should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_prompt_envelope_markdown(build_rag_evidence_prompt_envelope(ROOT))
    assert_true("RAG Evidence Prompt Envelope" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_operation_source_and_agent_allowed,
        test_operations_and_marin_blocked,
        test_system_instruction_required_text,
        test_messages_preview_and_citation_summary,
        test_safety_flags_and_no_sensitive_values,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence prompt envelope tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
