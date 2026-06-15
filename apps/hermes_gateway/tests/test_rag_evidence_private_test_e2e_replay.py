"""Phase 34L-0 private-test E2E replay tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_private_test_e2e_replay import build_rag_evidence_private_test_e2e_replay, render_rag_evidence_private_test_e2e_replay_markdown


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_e2e_replay_accepts_private_and_rejects_public_team() -> None:
    report = build_rag_evidence_private_test_e2e_replay(ROOT)
    assert_true(report["accepted_private_test_channel"] is True, "Private test accepted")
    assert_true(report["public_channel_rejected"] is True, "Public rejected")
    assert_true(report["team_channel_rejected"] is True, "Team rejected")


def test_e2e_replay_uses_fixtures_only() -> None:
    report = build_rag_evidence_private_test_e2e_replay(ROOT)
    assert_true(report["llm_response_fixture_replayed"] is True, "LLM fixture replayed")
    assert_true(report["send_closeout_fixture_replayed"] is True, "Send fixture replayed")
    assert_true(report["discord_live_runtime_executed"] is False, "No live runtime")
    assert_true(report["discord_message_sent"] is False, "No Discord send")
    assert_true(report["llm_api_called"] is False, "No LLM call")


def test_e2e_replay_chain_and_guards() -> None:
    report = build_rag_evidence_private_test_e2e_replay(ROOT)
    for key in ("knowledge_dry_chain_replayed", "evidence_packet_replayed", "prompt_envelope_replayed", "would_send_preview_replayed", "self_loop_guard_replayed", "duplicate_send_guard_replayed"):
        assert_true(report[key] is True, f"{key} should be true")


def test_e2e_replay_readiness() -> None:
    report = build_rag_evidence_private_test_e2e_replay(ROOT)
    assert_true(report["e2e_replay_passed"] is True, "Replay should pass")
    assert_true(report["ready_for_phase34l1_manual_e2e_live_reply"] is True, "Manual E2E should be ready")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "Unattended auto reply false")


def test_no_sensitive_values() -> None:
    text = json.dumps(build_rag_evidence_private_test_e2e_replay(ROOT), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "bearer " not in text, "Secret markers absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_e2e_replay_markdown(build_rag_evidence_private_test_e2e_replay(ROOT))
    assert_true("E2E Replay" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_e2e_replay_accepts_private_and_rejects_public_team,
        test_e2e_replay_uses_fixtures_only,
        test_e2e_replay_chain_and_guards,
        test_e2e_replay_readiness,
        test_no_sensitive_values,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence private-test E2E replay tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
