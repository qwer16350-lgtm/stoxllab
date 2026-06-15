"""Phase 34K private-test E2E preflight tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_private_test_e2e_preflight import build_rag_evidence_private_test_e2e_preflight, render_rag_evidence_private_test_e2e_preflight_markdown


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_e2e_preflight_components_available() -> None:
    report = build_rag_evidence_private_test_e2e_preflight(ROOT)
    for key in ("send_closeout_available", "knowledge_dry_chain_available", "prompt_envelope_available", "llm_dry_call_closeout_available", "would_send_preview_available", "private_test_send_preflight_available"):
        assert_true(report[key] is True, f"{key} should be true")


def test_e2e_preflight_blocks_public_team_reply() -> None:
    report = build_rag_evidence_private_test_e2e_preflight(ROOT)
    assert_true(report["public_channel_reply_allowed"] is False, "Public reply should be blocked")
    assert_true(report["team_channel_reply_allowed"] is False, "Team reply should be blocked")


def test_e2e_preflight_manual_approvals_required() -> None:
    report = build_rag_evidence_private_test_e2e_preflight(ROOT)
    assert_true(report["manual_approval_required_for_llm"] is True, "LLM manual approval required")
    assert_true(report["manual_approval_required_for_send"] is True, "Send manual approval required")


def test_e2e_preflight_no_live_runtime_api_send_or_llm() -> None:
    report = build_rag_evidence_private_test_e2e_preflight(ROOT)
    assert_true(report["discord_live_runtime_executed"] is False, "No live runtime")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["llm_api_called"] is False, "No LLM call")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external execution")


def test_e2e_preflight_readiness() -> None:
    report = build_rag_evidence_private_test_e2e_preflight(ROOT)
    assert_true(report["ready_for_phase34l1_manual_e2e_live_reply"] is True, "Manual E2E should be ready")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "Unattended auto reply should be false")


def test_no_sensitive_values() -> None:
    text = json.dumps(build_rag_evidence_private_test_e2e_preflight(ROOT), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "bearer " not in text, "Secret markers absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_e2e_preflight_markdown(build_rag_evidence_private_test_e2e_preflight(ROOT))
    assert_true("E2E Preflight" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_e2e_preflight_components_available,
        test_e2e_preflight_blocks_public_team_reply,
        test_e2e_preflight_manual_approvals_required,
        test_e2e_preflight_no_live_runtime_api_send_or_llm,
        test_e2e_preflight_readiness,
        test_no_sensitive_values,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence private-test E2E preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
