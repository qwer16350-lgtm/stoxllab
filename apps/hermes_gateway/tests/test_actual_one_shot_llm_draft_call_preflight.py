from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_one_shot_llm_draft_call_preflight import build_actual_one_shot_llm_draft_call_preflight, render_actual_one_shot_llm_draft_call_preflight_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_preflight_success_fixture() -> None:
    report = build_actual_one_shot_llm_draft_call_preflight(env={})
    assert_true(report["preflight_available"] is True, "Preflight available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["phase36_live_execution_started"] is False, "No live execution")
    assert_true(report["source_phase36a_preflight_available"] is True, "36A available")
    assert_true(report["source_phase36b_mock_packet_available"] is True, "36B mock available")
    assert_true(report["source_phase36b_output_safety_allowed"] is True, "36B safety allowed")


def test_candidate_agent_and_sources() -> None:
    report = build_actual_one_shot_llm_draft_call_preflight(env={})
    assert_true(report["candidate_agent"] == "kasumi", "Kasumi candidate")
    assert_true(report["candidate_agent_allowed"] is True, "Kasumi allowed")
    assert_true(report["allowed_sources"] == ["operation"], "Operation source")
    assert_true(report["evidence_citations"] == ["knowledge/operation/stoxl_operation_tone_sample.md"], "Citation")
    assert_true("operations" not in report["allowed_sources"], "operations not allowed")
    assert_true(report["safety_assertions"]["full_content_included"] is False, "No full content")


def test_preflight_never_calls_or_sends() -> None:
    report = build_actual_one_shot_llm_draft_call_preflight(env={})
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(report["llm_api_call_count"] == 0, "LLM count zero")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["discord_api_send_called"] is False, "No Discord API send")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["vector_index_created"] is False, "No vector")
    assert_true(report["external_execution"] is False, "No external")


def test_approval_and_readiness_false() -> None:
    report = build_actual_one_shot_llm_draft_call_preflight(env={"OPENROUTER_API_KEY": "sk-test-not-logged"})
    assert_true(report["manual_approval_required"] is True, "Manual approval required")
    assert_true(report["manual_approval_actualized"] is False, "Manual approval not actualized")
    assert_true(report["approval_phrase_generated"] is False, "No phrase generated")
    assert_true(report["approval_phrase_value_logged"] is False, "No phrase logged")
    assert_true(report["ready_for_actual_llm_call"] is False, "Actual LLM false")
    assert_true(report["ready_for_discord_send"] is False, "Discord false")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "Unattended false")
    assert_true(report["blocked_reasons"] == ["manual_approval_not_actualized"], "Manual approval blocked")


def test_openrouter_aliases() -> None:
    missing = build_actual_one_shot_llm_draft_call_preflight(env={})
    assert_true(missing["openrouter_api_key_present"] is False, "Missing key false")
    assert_true(missing["preflight_ready_for_manual_llm_call"] is False, "Missing key blocks readiness")
    assert_true("openrouter_api_key_missing" in missing["blocked_reasons"], "Missing key reason")
    openrouter = build_actual_one_shot_llm_draft_call_preflight(env={"OPENROUTER_API_KEY": "sk-openrouter-value"})
    assert_true(openrouter["openrouter_api_key_present"] is True, "OPENROUTER key true")
    assert_true(openrouter["preflight_ready_for_manual_llm_call"] is True, "Ready with OPENROUTER key")
    hermes = build_actual_one_shot_llm_draft_call_preflight(env={"HERMES_OPENROUTER_API_KEY": "sk-hermes-value"})
    assert_true(hermes["openrouter_api_key_present"] is True, "HERMES key true")
    assert_true(hermes["preflight_ready_for_manual_llm_call"] is True, "Ready with HERMES key")
    assert_true(hermes["ready_for_actual_llm_call"] is False, "Actual LLM still false")


def test_model_provider_and_secret_redaction() -> None:
    report = build_actual_one_shot_llm_draft_call_preflight(env={"OPENROUTER_API_KEY": "sk-secret-never-output"})
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true(report["provider"] == "openrouter", "Provider")
    assert_true(report["model"] == "openai/gpt-5.4-mini", "Model")
    assert_true(report["model_value_logged"] is True, "Model safe logged")
    assert_true("sk-secret-never-output" not in text, "Key value not logged")
    assert_true("i_approve_" not in text, "Approval phrase not logged")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    markdown = render_actual_one_shot_llm_draft_call_preflight_markdown(build_actual_one_shot_llm_draft_call_preflight(env={}))
    assert_true("Actual One-shot LLM Draft Call Preflight" in markdown, "Markdown")


def main() -> int:
    tests = [
        test_preflight_success_fixture,
        test_candidate_agent_and_sources,
        test_preflight_never_calls_or_sends,
        test_approval_and_readiness_false,
        test_openrouter_aliases,
        test_model_provider_and_secret_redaction,
        test_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual one-shot LLM draft call preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
