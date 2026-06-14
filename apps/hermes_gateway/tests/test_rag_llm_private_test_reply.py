"""Phase 33D-safe RAG+LLM private test reply preflight tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_llm_private_test_reply import build_rag_llm_private_test_reply_preflight, render_rag_llm_private_test_reply_markdown


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def live_like_env() -> dict[str, str]:
    return {
        "HERMES_RAG_ENABLED": "false",
        "HERMES_RAG_MODE": "local_readonly",
        "HERMES_RAG_PRIVATE_TEST_ONLY": "true",
        "HERMES_RAG_ALLOWED_SOURCES": "marketing,operation,strategy,brand,archive",
        "HERMES_RAG_REQUIRE_RESPONSE_PACKET": "true",
        "HERMES_RAG_LLM_REPLY_ENABLED": "true",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "true",
        "HERMES_LLM_PRIVATE_TEST_REPLY_MODE": "private_test_only",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "configured",
    }


def test_default_blocked_disabled() -> None:
    report = build_rag_llm_private_test_reply_preflight(env={})
    assert_true(report["ready"] is False and report["blocked"] is True, "Default should block")
    assert_true("rag_llm_reply_disabled_by_default" in report["blocked_reasons"], "Default disabled reason")


def test_live_like_still_not_ready_in_safe_scaffold() -> None:
    report = build_rag_llm_private_test_reply_preflight(env=live_like_env())
    assert_true(report["ready"] is False, "Safe scaffold should never mark ready")
    assert_true(report["ready_for_phase33d_live_implementation"] is False, "Live implementation not ready")
    assert_true(report["discord_message_sent"] is False, "No send")


def test_source_operations_blocked() -> None:
    report = build_rag_llm_private_test_reply_preflight(source="operations", env=live_like_env())
    assert_true(report["source_valid"] is False, "operations invalid")
    assert_true("operations_source_not_allowed" in report["blocked_reasons"], "operations explicitly blocked")


def test_gate_reasons_present() -> None:
    report = build_rag_llm_private_test_reply_preflight(env={"HERMES_RAG_MODE": "remote"})
    assert_true("rag_mode_not_local_readonly" in report["blocked_reasons"], "RAG mode should block")
    assert_true("private_test_channel_id_missing" in report["blocked_reasons"], "Missing channel should block")


def test_report_has_no_secret_or_raw_id() -> None:
    text = json.dumps(build_rag_llm_private_test_reply_preflight(env=live_like_env()), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text, "No secret values")
    assert_true(not LONG_ID_RE.search(text), "No raw Discord IDs")


def test_markdown_renders() -> None:
    assert_true("RAG+LLM Private Test Reply Preflight" in render_rag_llm_private_test_reply_markdown(build_rag_llm_private_test_reply_preflight(env={})), "Markdown")


def main() -> int:
    tests = [
        test_default_blocked_disabled,
        test_live_like_still_not_ready_in_safe_scaffold,
        test_source_operations_blocked,
        test_gate_reasons_present,
        test_report_has_no_secret_or_raw_id,
        test_markdown_renders,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM private test reply preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
