"""Phase 34I RAG evidence would-send preview tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_evidence_would_send_preview.py
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_llm_dry_call_closeout import build_rag_evidence_llm_dry_call_closeout
from rag_evidence_would_send_preview import build_rag_evidence_would_send_preview, render_rag_evidence_would_send_preview_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(func, message: str) -> None:
    try:
        func()
    except ValueError:
        return
    raise AssertionError(message)


def closeout() -> dict:
    return build_rag_evidence_llm_dry_call_closeout()


def test_would_send_preview_requires_closeout() -> None:
    assert_raises(lambda: build_rag_evidence_would_send_preview({}), "Missing closeout should fail")


def test_would_send_preview_requires_llm_response_packet() -> None:
    bad = closeout()
    bad["llm_response_packet_created"] = False
    report = build_rag_evidence_would_send_preview(bad)
    assert_true(report["llm_response_packet_available"] is False, "Missing packet should block preview creation")
    assert_true(report["would_send_preview_created"] is False, "Preview should not be created")


def test_would_send_preview_requires_output_safety_allowed() -> None:
    bad = closeout()
    bad["output_safety_allowed"] = False
    report = build_rag_evidence_would_send_preview(bad)
    assert_true(report["output_safety_allowed"] is False, "Output safety should be reflected")
    assert_true(report["would_send_preview_created"] is False, "Unsafe output should block preview creation")


def test_would_send_preview_created() -> None:
    report = build_rag_evidence_would_send_preview()
    assert_true(report["would_send_preview_created"] is True, "Preview should be created")
    assert_true(report["ready_for_phase34j_private_test_send_preflight"] is True, "Preflight readiness should be true")


def test_review_only_and_not_sent_markers_included() -> None:
    content = build_rag_evidence_would_send_preview()["would_send_message"]["content_preview"]
    assert_true("[REVIEW ONLY / NOT SENT]" in content, "Review/not-sent marker should be included")
    assert_true("No external action has been taken." in content, "Safety disclaimer should be included")


def test_evidence_relative_paths_included() -> None:
    report = build_rag_evidence_would_send_preview()
    content = report["would_send_message"]["content_preview"]
    for path in report["would_send_message"]["citations"]:
        assert_true(path in content, "Evidence relative path should be included in preview")
        assert_true(path.startswith("knowledge/") and ":" not in path, "Evidence path should be relative")


def test_absolute_paths_blocked() -> None:
    bad = copy.deepcopy(closeout())
    bad["evidence_paths"] = ["C:/tmp/STOXL_LAB/knowledge/operation/file.md"]
    assert_raises(lambda: build_rag_evidence_would_send_preview(bad), "Absolute path should block")


def test_full_content_dump_not_included_and_max_chars_enforced() -> None:
    report = build_rag_evidence_would_send_preview(extra_text="x" * 5000)
    message = report["would_send_message"]
    assert_true(message["full_content_included"] is False, "Full content should not be included")
    assert_true(message["content_char_count"] <= 1200, "Preview should enforce max chars")


def test_sensitive_values_not_logged() -> None:
    text = json.dumps(build_rag_evidence_would_send_preview(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "bearer " not in text, "Token markers should be absent")
    assert_true("api_key=" not in text and "token=" not in text, "Secret labels should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_mentions_blocked_or_escaped() -> None:
    report = build_rag_evidence_would_send_preview(extra_text="@everyone @here <@123456789012345678>")
    content = report["would_send_message"]["content_preview"]
    assert_true("@everyone" not in content and "@here" not in content and "<@" not in content, "Raw mentions should be blocked")
    assert_true(report["would_send_message"]["mention_spam_blocked_or_escaped"] is True, "Mention blocking should be recorded")


def test_send_flags_false() -> None:
    report = build_rag_evidence_would_send_preview()
    assert_true(report["private_test_channel_only"] is True, "Private-test only should be true")
    assert_true(report["public_channel_send_allowed"] is False, "Public send should be false")
    assert_true(report["team_channel_send_allowed"] is False, "Team send should be false")
    assert_true(report["discord_api_send_allowed"] is False, "Discord API send allowed should be false")
    assert_true(report["discord_api_send_called"] is False, "Discord API send called should be false")
    assert_true(report["discord_message_sent"] is False, "Discord message sent should be false")
    assert_true(report["llm_api_called"] is False, "Additional LLM call should be false")
    assert_true(report["embedding_api_called"] is False, "Embedding call should be false")
    assert_true(report["external_execution"] is False, "External execution should be false")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_would_send_preview_markdown(build_rag_evidence_would_send_preview())
    assert_true("RAG Evidence Would-send Preview" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_would_send_preview_requires_closeout,
        test_would_send_preview_requires_llm_response_packet,
        test_would_send_preview_requires_output_safety_allowed,
        test_would_send_preview_created,
        test_review_only_and_not_sent_markers_included,
        test_evidence_relative_paths_included,
        test_absolute_paths_blocked,
        test_full_content_dump_not_included_and_max_chars_enforced,
        test_sensitive_values_not_logged,
        test_mentions_blocked_or_escaped,
        test_send_flags_false,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence would-send preview tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
