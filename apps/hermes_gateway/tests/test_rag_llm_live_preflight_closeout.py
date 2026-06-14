"""Phase 33D-2 RAG+LLM live preflight closeout tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_rag_llm_live_preflight_closeout.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from operations_packet_viewer import build_operations_packet_viewer_report, render_operations_summary_markdown
from rag_llm_live_preflight_closeout import (
    assert_rag_llm_live_preflight_closeout_safe,
    build_rag_llm_live_preflight_closeout,
    render_rag_llm_live_preflight_closeout_markdown,
)


ROOT = APP_DIR.parents[1]
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_default_preflight_blocked_and_mock_ready() -> None:
    report = build_rag_llm_live_preflight_closeout(root=str(ROOT))
    assert_true(report["default_preflight_blocked"] is True, "Default preflight must stay blocked")
    assert_true(report["mock_live_ready_fixture_passed"] is True, "Mock live-ready fixture should pass")
    assert_true(report["ready_for_single_live_private_test"] is True, "Single live private test should be ready for separate approval")


def test_runtime_option_present_but_not_executed() -> None:
    report = build_rag_llm_live_preflight_closeout(root=str(ROOT))
    assert_true(report["runtime_option_present"] is True, "Runtime option should be represented")
    assert_true(report["runtime_option"] == "--run-discord-private-test-rag-llm-reply", "Runtime option should match")
    assert_true(report["runtime_executed"] is False, "Closeout must not execute runtime")


def test_live_requirements_all_true() -> None:
    requirements = build_rag_llm_live_preflight_closeout(root=str(ROOT))["live_requirements"]
    assert_true(all(value is True for value in requirements.values()), "All live requirements should be true")


def test_blocked_before_retrieval_scope() -> None:
    blocked = build_rag_llm_live_preflight_closeout(root=str(ROOT))["blocked_before_retrieval"]
    for item in (
        "public_channel",
        "team_mapped_channel",
        "self_message",
        "bot_message",
        "duplicate_message",
        "cooldown",
        "budget_exhausted",
        "invalid_source",
        "operations_source",
    ):
        assert_true(item in blocked, f"{item} should block before retrieval")


def test_actual_execution_flags_false() -> None:
    report = build_rag_llm_live_preflight_closeout(root=str(ROOT))
    assert_true(report["actual_discord_send"] is False, "No Discord send")
    assert_true(report["actual_llm_api_call"] is False, "No LLM API call")
    assert_true(report["embedding_api_called"] is False, "No embedding API call")
    assert_true(report["external_execution"] is False, "No external execution")


def test_safety_assertions_false_and_safe() -> None:
    report = build_rag_llm_live_preflight_closeout(root=str(ROOT))
    assert_rag_llm_live_preflight_closeout_safe(report)
    safety = report["safety_assertions"]
    assert_true(safety["api_key_value_logged"] is False, "API key value must not be logged")
    assert_true(safety["raw_discord_ids_logged"] is False, "Raw Discord IDs must not be logged")
    assert_true(safety["embedding_called"] is False, "Embedding must not be called")
    assert_true(safety["llm_called"] is False, "LLM must not be called")
    assert_true(safety["discord_message_sent"] is False, "Discord message must not be sent")
    assert_true(safety["external_execution"] is False, "External execution must be false")


def test_no_secret_or_raw_discord_id() -> None:
    text = json.dumps(build_rag_llm_live_preflight_closeout(root=str(ROOT)), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text and "bearer " not in text, "No secret markers")
    assert_true("token=" not in text and "password=" not in text, "No token/password assignments")
    assert_true(not LONG_ID_RE.search(text), "No raw Discord-like IDs")


def test_markdown_render_works() -> None:
    markdown = render_rag_llm_live_preflight_closeout_markdown(build_rag_llm_live_preflight_closeout(root=str(ROOT)))
    assert_true("STOXL RAG+LLM Live Preflight Closeout" in markdown, "Markdown should render")
    assert_true("Runtime executed: false" in markdown, "Markdown should show runtime not executed")
    assert_true("Ready for single live private test: true" in markdown, "Markdown should show readiness")


def test_cli_json_and_markdown() -> None:
    json_result = subprocess.run(
        [sys.executable, str(APP_DIR / "cli.py"), "--rag-llm-live-preflight-closeout", "--json"],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    report = json.loads(json_result.stdout)
    assert_true(report["runtime_executed"] is False, "CLI JSON should not execute runtime")
    assert_true(report["ready_for_single_live_private_test"] is True, "CLI JSON should be ready")
    markdown_result = subprocess.run(
        [sys.executable, str(APP_DIR / "cli.py"), "--rag-llm-live-preflight-closeout", "--markdown"],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert_true("Actual Discord send: false" in markdown_result.stdout, "CLI Markdown should render safety")


def test_operations_viewer_includes_closeout_summary() -> None:
    viewer = build_operations_packet_viewer_report(root=str(ROOT))
    closeout = viewer["rag_llm_live_preflight_closeout"]
    assert_true(closeout["available"] is True, "Closeout summary should be available")
    assert_true(closeout["runtime_executed"] is False, "Viewer should not execute runtime")
    assert_true(closeout["ready_for_single_live_private_test"] is True, "Viewer should show ready")
    assert_true(closeout["actual_discord_send"] is False, "Viewer no Discord send")
    assert_true(closeout["actual_llm_api_call"] is False, "Viewer no LLM API")
    assert_true(closeout["embedding_api_called"] is False, "Viewer no embedding")
    assert_true(closeout["external_execution"] is False, "Viewer no external execution")
    markdown = render_operations_summary_markdown(viewer)
    assert_true("RAG+LLM Live Preflight Closeout" in markdown, "Viewer markdown should include closeout")


def main() -> int:
    tests = [
        test_default_preflight_blocked_and_mock_ready,
        test_runtime_option_present_but_not_executed,
        test_live_requirements_all_true,
        test_blocked_before_retrieval_scope,
        test_actual_execution_flags_false,
        test_safety_assertions_false_and_safe,
        test_no_secret_or_raw_discord_id,
        test_markdown_render_works,
        test_cli_json_and_markdown,
        test_operations_viewer_includes_closeout_summary,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM live preflight closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
