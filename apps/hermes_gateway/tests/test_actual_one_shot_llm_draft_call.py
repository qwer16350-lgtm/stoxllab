from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_one_shot_llm_draft_call import build_actual_one_shot_llm_draft_call, render_actual_one_shot_llm_draft_call_markdown


APPROVED_ENV = {
    "HERMES_LLM_API_KEY": "sk-test-never-logged",
    "HERMES_LLM_PROVIDER": "openrouter",
    "HERMES_LLM_MODEL": "redacted-model",
    "HERMES_LLM_BASE_URL": "https://redacted.example",
    "HERMES_PHASE45A_MANUAL_APPROVAL": "true",
    "HERMES_PHASE45A_APPROVAL_PHRASE": "I_APPROVE_PHASE45A_ACTUAL_LLM_ONE_SHOT",
    "HERMES_PHASE45A_COST_GUARD": "true",
    "HERMES_PHASE45A_CALL_COUNT_GUARD": "true",
    "HERMES_DISCORD_SEND_MESSAGES": "false",
    "HERMES_DISCORD_PRIVATE_TEST_SEND": "false",
    "HERMES_LLM_API_CALL_ENABLED": "false",
    "HERMES_DISCORD_RAG_ENABLED": "false",
    "HERMES_LLM_RAG_ENABLED": "false",
    "HERMES_EMBEDDING_ENABLED": "false",
    "HERMES_VECTOR_ENABLED": "false",
    "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
}
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_success(envelope: dict, config: dict) -> dict:
    assert_true(envelope["agent_route_candidate"] == "kasumi", "kasumi envelope")
    assert_true(envelope["allowed_sources"] == ["operation"], "operation envelope")
    assert_true(config["provider"] == "openrouter", "openrouter config")
    return {
        "result_type": "llm_client_result",
        "provider": "openrouter",
        "model": "openai/gpt-5.4-mini",
        "api_call_attempted": True,
        "api_call_succeeded": True,
        "api_call_failed": False,
        "error_type": None,
        "response_text": (
            "This is a review-only draft. No external action has been taken. "
            "Citation: knowledge/operation/stoxl_operation_tone_sample.md. "
            "Confirmed checks and uncertainty should be reviewed by a human before any next step."
        ),
        "usage": {"input_chars": 100, "output_chars": 180, "provider_usage": {"total_tokens": 42}},
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def mock_unsafe(envelope: dict, config: dict) -> dict:
    result = mock_success(envelope, config)
    result["response_text"] = "I sent this to the team channel. Citation: knowledge/operation/stoxl_operation_tone_sample.md"
    return result


def test_default_blocks_with_no_llm_call() -> None:
    report = build_actual_one_shot_llm_draft_call(env={})
    assert_true(report["blocked"] is True, "Default blocked")
    assert_true(report["reason"] == "phase45_actual_llm_one_shot_already_consumed", "Blocked reason")
    assert_true(report["ready"] is False, "Default not ready")
    assert_true(report["phase45_actual_llm_one_shot_already_consumed"] is True, "No-repeat consumed")
    assert_true(report["phase45_ready_for_repeat_llm_call"] is False, "Repeat not ready")
    assert_true(report["llm_api_call_attempted"] is False, "No API attempt")
    assert_true(report["llm_api_call_count"] == 0, "No API count")
    assert_true(report["actual_llm_api_call_attempted"] is False, "No actual API attempt")
    assert_true(report["actual_llm_api_called"] is False, "No actual API call")
    assert_true(report["real_llm_api_call_count"] == 0, "No real API count")
    assert_true("phase45_actual_llm_one_shot_already_consumed" in report["blocked_reasons"], "Repeat lock blocks")
    assert_true(report["provider_config_present"] is False, "Provider follows Phase45 preflight")
    assert_true(report["model_config_present"] is False, "Model follows Phase45 preflight")
    assert_true(report["base_url_present"] is False, "Base URL follows Phase45 preflight")
    assert_true("manual_approval_not_approved" in report["blocked_reasons"], "Manual approval blocks")
    assert_true("actual_llm_allow_flag_missing" in report["blocked_reasons"], "Allow flag blocks")
    assert_true("openrouter_api_key_missing" in report["blocked_reasons"], "Key missing blocks")


def test_manual_approval_and_phrase_gates() -> None:
    missing = build_actual_one_shot_llm_draft_call(
        env={"HERMES_LLM_API_KEY": "sk-x"},
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
    )
    assert_true(missing["manual_approval"]["approved"] is False, "Approval missing")
    mismatch = build_actual_one_shot_llm_draft_call(
        env={
            **APPROVED_ENV,
            "HERMES_PHASE45A_APPROVAL_PHRASE": "WRONG",
        },
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
    )
    assert_true(mismatch["manual_approval"]["approval_phrase_exact_match"] is False, "Phrase mismatch")
    assert_true(mismatch["llm_api_call_attempted"] is False, "Mismatch blocks call")


def test_phase45_gate_open_without_allow_returns_specific_blocked_json() -> None:
    report = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, phase45_no_repeat_lock_consumed=False)
    assert_true(report["manual_approval"]["approved"] is True, "Phase45 approval bridged")
    assert_true(report["manual_approval"]["authoritative_gate"] == "phase45a", "Phase45 authoritative")
    assert_true(report["phase45_preflight_ready_for_manual_gate"] is True, "Phase45 gate ready")
    assert_true(report["provider_config_present"] is True, "Provider config ready")
    assert_true(report["model_config_present"] is True, "Model config ready")
    assert_true(report["base_url_present"] is True, "Base URL config ready")
    assert_true(report["blocked"] is True, "Allow missing blocks")
    assert_true(report["reason"] == "actual_llm_allow_flag_missing", "Allow reason")
    assert_true("actual_llm_allow_flag_missing" in report["blocked_reasons"], "Allow blocked reason")
    assert_true(report["llm_api_call_attempted"] is False, "No attempt")
    assert_true(report["actual_llm_api_call_attempted"] is False, "No actual attempt")
    assert_true(report["discord_message_sent"] is False, "No Discord")


def test_kasumi_only_and_operation_only() -> None:
    marin = build_actual_one_shot_llm_draft_call(
        env=APPROVED_ENV,
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
        candidate_agent="marin",
    )
    assert_true(marin["candidate_agent_allowed"] is False, "Marin blocked")
    assert_true(marin["llm_api_call_attempted"] is False, "Marin no call")
    decision = build_actual_one_shot_llm_draft_call(
        env=APPROVED_ENV,
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
        candidate_agent="decision_maker_review",
    )
    assert_true(decision["llm_api_call_attempted"] is False, "Decision maker review no call")
    operation = build_actual_one_shot_llm_draft_call(
        env=APPROVED_ENV,
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
        llm_caller=mock_success,
    )
    assert_true(operation["allowed_sources"] == ["operation"], "Operation allowed")
    operations = build_actual_one_shot_llm_draft_call(
        env=APPROVED_ENV,
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
        source="operations",
    )
    assert_true("operations_source_forbidden" in operations["blocked_reasons"], "operations forbidden")


def test_mock_success_creates_safe_packet() -> None:
    report = build_actual_one_shot_llm_draft_call(
        env=APPROVED_ENV,
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
        llm_caller=mock_success,
    )
    assert_true(report["ready"] is True, "Ready")
    assert_true(report["blocked"] is False, "Not blocked")
    assert_true(report["manual_approval"]["approved"] is True, "Phase45 approval bridged")
    assert_true(report["llm_api_call_attempted"] is True, "API attempted")
    assert_true(report["llm_api_call_count"] == 1, "One call")
    assert_true(report["actual_llm_api_call_attempted"] is False, "No real API attempt")
    assert_true(report["actual_llm_api_called"] is False, "No real API call")
    assert_true(report["real_llm_api_call_count"] == 0, "No real API count")
    assert_true("provider" not in report["llm_client_result"], "Provider value omitted")
    assert_true("model" not in report["llm_client_result"], "Model value omitted")
    assert_true(report["llm_client_result"]["provider_config_value_logged"] is False, "Provider value not logged")
    assert_true(report["llm_client_result"]["model_config_value_logged"] is False, "Model value not logged")
    assert_true(report["llm_response_packet_created"] is True, "Packet created")
    assert_true(report["output_safety_checked"] is True, "Safety checked")
    assert_true(report["output_safety_allowed"] is True, "Safety allowed")
    assert_true(report["ready_for_phase36e_closeout"] is True, "Closeout ready")
    assert_true(report["ready_for_discord_send"] is False, "Discord send false")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "No unattended")
    assert_true(report["llm_response_packet"]["full_content_included"] is False, "No full content")


def test_output_safety_failure_prevents_closeout() -> None:
    report = build_actual_one_shot_llm_draft_call(
        env=APPROVED_ENV,
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
        llm_caller=mock_unsafe,
    )
    assert_true(report["llm_api_call_count"] == 1, "One call")
    assert_true(report["output_safety_checked"] is True, "Safety checked")
    assert_true(report["output_safety_allowed"] is False, "Safety blocked")
    assert_true(report["llm_response_packet_created"] is False, "No packet")
    assert_true(report["ready_for_phase36e_closeout"] is False, "Closeout false")
    assert_true(report["discord_message_sent"] is False, "No Discord")


def test_secret_values_not_logged_and_markdown() -> None:
    report = build_actual_one_shot_llm_draft_call(
        env=APPROVED_ENV,
        allow_actual_call=True,
        phase45_no_repeat_lock_consumed=False,
        llm_caller=mock_success,
    )
    text = json.dumps(report, ensure_ascii=False).lower()
    markdown = render_actual_one_shot_llm_draft_call_markdown(report)
    assert_true("sk-test-never-logged" not in text, "Key not logged")
    assert_true("i_approve" not in text, "Approval phrase not logged")
    assert_true("redacted.example" not in text, "Base URL not logged")
    assert_true("redacted-model" not in text, "Model value not logged")
    assert_true("openai/gpt-5.4-mini" not in text, "Provider result model not logged")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Actual One-shot LLM Draft Call" in markdown, "Markdown")


def test_repeat_lock_blocks_even_with_allow_and_fake_provider() -> None:
    called = {"count": 0}

    def should_not_call(envelope: dict, config: dict) -> dict:
        called["count"] += 1
        return mock_success(envelope, config)

    report = build_actual_one_shot_llm_draft_call(env=APPROVED_ENV, allow_actual_call=True, llm_caller=should_not_call)
    assert_true(report["blocked"] is True, "Repeat lock blocked")
    assert_true(report["reason"] == "phase45_actual_llm_one_shot_already_consumed", "Repeat reason")
    assert_true(report["llm_api_call_attempted"] is False, "No repeat attempt")
    assert_true(report["llm_api_call_count"] == 0, "No repeat call count")
    assert_true(report["actual_llm_api_call_attempted"] is False, "No actual repeat attempt")
    assert_true(report["actual_llm_api_called"] is False, "No actual repeat call")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(called["count"] == 0, "Provider not called")


def main() -> int:
    tests = [
        test_default_blocks_with_no_llm_call,
        test_manual_approval_and_phrase_gates,
        test_phase45_gate_open_without_allow_returns_specific_blocked_json,
        test_kasumi_only_and_operation_only,
        test_mock_success_creates_safe_packet,
        test_output_safety_failure_prevents_closeout,
        test_secret_values_not_logged_and_markdown,
        test_repeat_lock_blocks_even_with_allow_and_fake_provider,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All actual one-shot LLM draft call tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
