"""Phase 33D-safe RAG+LLM prompt envelope tests."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_llm_prompt_envelope import build_rag_llm_prompt_envelope, render_rag_llm_prompt_envelope_markdown


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_root() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    base = Path(temp.name) / "knowledge" / "operation"
    base.mkdir(parents=True)
    (base / "tone.md").write_text("STOXL brand tone preview context.", encoding="utf-8")
    return temp


def test_operation_source_accepted() -> None:
    with make_root() as temp:
        envelope = build_rag_llm_prompt_envelope(temp)
        assert_true(envelope["source_valid"] is True, "operation valid")


def test_operations_source_rejected() -> None:
    envelope = build_rag_llm_prompt_envelope(source="operations")
    assert_true(envelope["source_valid"] is False, "operations invalid")


def test_envelope_includes_review_only_safety() -> None:
    content = build_rag_llm_prompt_envelope()["messages_preview"][0]["content"]
    assert_true("Review-only" in content and "Do not publish" in content, "Safety instruction required")


def test_raw_full_context_not_included() -> None:
    envelope = build_rag_llm_prompt_envelope()
    limits = envelope["input_limits"]
    assert_true(limits["raw_content_included"] is False, "No raw full context")
    assert_true(limits["content_preview_only"] is True, "Preview only")


def test_limits_and_safety_flags() -> None:
    envelope = build_rag_llm_prompt_envelope()
    assert_true(envelope["input_limits"]["max_context_chars"] == 3000, "Max chars preserved")
    assert_true(envelope["llm_api_called"] is False, "No LLM")
    assert_true(envelope["discord_message_sent"] is False, "No Discord send")


def test_no_secret_or_raw_id_and_markdown() -> None:
    envelope = build_rag_llm_prompt_envelope()
    text = json.dumps(envelope, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text, "No secret")
    assert_true(not LONG_ID_RE.search(text), "No raw IDs")
    assert_true("RAG+LLM Prompt Envelope" in render_rag_llm_prompt_envelope_markdown(envelope), "Markdown")


def main() -> int:
    tests = [
        test_operation_source_accepted,
        test_operations_source_rejected,
        test_envelope_includes_review_only_safety,
        test_raw_full_context_not_included,
        test_limits_and_safety_flags,
        test_no_secret_or_raw_id_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM prompt envelope tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
