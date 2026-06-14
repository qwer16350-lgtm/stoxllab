"""Phase 33D-safe RAG+LLM would-send preview tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_llm_would_send_preview import build_rag_llm_would_send_preview, render_rag_llm_would_send_preview_markdown


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_never_sends() -> None:
    preview = build_rag_llm_would_send_preview()
    assert_true(preview["will_send"] is False, "will_send false")
    assert_true(preview["message_sent"] is False, "message_sent false")
    assert_true(preview["discord_send_attempted"] is False, "send attempted false")


def test_operations_source_blocked() -> None:
    preview = build_rag_llm_would_send_preview(source="operations")
    assert_true("operations_source_not_allowed" in preview["blocked_reasons"], "operations blocked")


def test_public_channel_blocked() -> None:
    preview = build_rag_llm_would_send_preview(channel_scope="public_team")
    assert_true("public_or_team_channel_blocked" in preview["blocked_reasons"], "public blocked")


def test_self_or_bot_blocked() -> None:
    assert_true("self_or_bot_message_blocked" in build_rag_llm_would_send_preview(self_message=True)["blocked_reasons"], "self blocked")
    assert_true("self_or_bot_message_blocked" in build_rag_llm_would_send_preview(author_is_bot=True)["blocked_reasons"], "bot blocked")


def test_no_llm_api_discord_external() -> None:
    preview = build_rag_llm_would_send_preview()
    assert_true(preview["would_call_llm"] is False, "No LLM")
    assert_true(preview["embedding_api_called"] is False, "No embedding")
    assert_true(preview["external_execution"] is False, "No external")


def test_safe_text_and_markdown() -> None:
    preview = build_rag_llm_would_send_preview()
    text = json.dumps(preview, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text, "No secret")
    assert_true(not LONG_ID_RE.search(text), "No raw IDs")
    assert_true("RAG+LLM Would-send Preview" in render_rag_llm_would_send_preview_markdown(preview), "Markdown")


def main() -> int:
    tests = [
        test_never_sends,
        test_operations_source_blocked,
        test_public_channel_blocked,
        test_self_or_bot_blocked,
        test_no_llm_api_discord_external,
        test_safe_text_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM would-send preview tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
