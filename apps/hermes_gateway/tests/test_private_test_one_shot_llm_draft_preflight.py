from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_one_shot_llm_draft_preflight import build_private_test_one_shot_llm_draft_preflight, render_private_test_one_shot_llm_draft_preflight_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_preflight_success_fixture() -> None:
    report = build_private_test_one_shot_llm_draft_preflight()
    assert_true(report["preflight_available"] is True, "Preflight available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase36_started"] is False, "Phase 36 not started")
    assert_true(report["requires_explicit_user_approval"] is True, "Explicit approval required")


def test_preflight_never_calls_or_sends() -> None:
    report = build_private_test_one_shot_llm_draft_preflight()
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_call_count"] == 0, "LLM count zero")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["discord_api_send_called"] is False, "No Discord API send")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")


def test_preflight_readiness_false() -> None:
    report = build_private_test_one_shot_llm_draft_preflight()
    for key in ("approval_phrase_generated", "approval_phrase_value_logged", "ready_for_actual_approval", "ready_for_actual_llm_call", "ready_for_discord_send", "ready_for_unattended_auto_reply"):
        assert_true(report[key] is False, f"{key} false")


def test_candidate_agents() -> None:
    report = build_private_test_one_shot_llm_draft_preflight()
    candidates = report["preflight_candidates"]
    assert_true("kasumi" in report["candidate_agents"], "Kasumi candidate")
    assert_true(candidates["kasumi"]["candidate"] is True, "Kasumi candidate true")
    assert_true(candidates["kasumi"]["allowed_sources"] == ["operation"], "Kasumi operation")
    assert_true("knowledge/operation/stoxl_operation_tone_sample.md" in candidates["kasumi"]["evidence_citations"], "Kasumi citation")
    assert_true(candidates["kasumi"]["ready_for_future_manual_llm_draft"] is False, "Kasumi future ready false")
    assert_true(candidates["marin"]["candidate"] is False, "Marin candidate false")
    assert_true("no_evidence_citations" in candidates["marin"]["risk_flags"], "Marin no evidence")
    assert_true("not_ready_for_approval" in candidates["marin"]["risk_flags"], "Marin not ready")
    assert_true(candidates["decision_maker_review"]["candidate"] is False, "Decision maker candidate false")
    assert_true("broad_source_scope" in candidates["decision_maker_review"]["risk_flags"], "Decision maker broad")


def test_manual_gate_names_without_values() -> None:
    report = build_private_test_one_shot_llm_draft_preflight()
    names = report["future_manual_gate_names"]
    assert_true("HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVED" in names, "Approval gate name listed")
    assert_true("HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVAL_PHRASE" in names, "Phrase gate name listed")
    assert_true("OPENROUTER_API_KEY" in names, "API key name listed")
    text = json.dumps(report, ensure_ascii=False)
    assert_true("I_APPROVE_" not in text, "Approval phrase value not logged")


def test_blocked_scopes() -> None:
    blocked = build_private_test_one_shot_llm_draft_preflight()["blocked_scopes"]
    for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed", "discord_send_allowed", "unattended_auto_reply_allowed"):
        assert_true(blocked[key] is False, f"{key} false")


def test_no_sensitive_values() -> None:
    text = json.dumps(build_private_test_one_shot_llm_draft_preflight(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    assert_true("One-shot LLM Draft Preflight" in render_private_test_one_shot_llm_draft_preflight_markdown(build_private_test_one_shot_llm_draft_preflight()), "Markdown")


def main() -> int:
    tests = [
        test_preflight_success_fixture,
        test_preflight_never_calls_or_sends,
        test_preflight_readiness_false,
        test_candidate_agents,
        test_manual_gate_names_without_values,
        test_blocked_scopes,
        test_no_sensitive_values,
        test_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test one-shot LLM draft preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
