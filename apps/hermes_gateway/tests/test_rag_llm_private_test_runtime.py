"""Phase 33D-1 guarded RAG+LLM private test runtime tests."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_reply_safety import build_private_test_reply_safety_state
from rag_llm_private_test_runtime import (
    build_rag_llm_private_reply_preflight,
    build_rag_llm_private_test_runtime_report,
    build_rag_llm_reply_pipeline_plan,
    build_rag_llm_reply_send_payload,
    is_single_live_test_manually_approved,
    record_rag_llm_reply_attempt,
    render_rag_llm_private_test_runtime_markdown,
    run_discord_private_test_rag_llm_reply_bot,
    should_allow_rag_llm_private_reply,
)


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ready_env(**overrides: object) -> dict[str, object]:
    env: dict[str, object] = {
        "HERMES_RAG_LLM_REPLY_ENABLED": "true",
        "HERMES_RAG_LLM_REPLY_MODE": "private_test_only",
        "HERMES_RAG_LLM_REQUIRE_RAG_PACKET": "true",
        "HERMES_RAG_LLM_REQUIRE_CONTEXT_SAFETY": "true",
        "HERMES_RAG_LLM_REQUIRE_OUTPUT_SAFETY": "true",
        "HERMES_RAG_LLM_MAX_CONTEXT_CHARS": "3000",
        "HERMES_RAG_LLM_MAX_DOCUMENTS": "5",
        "HERMES_RAG_LLM_MAX_REPLIES_PER_SESSION": "2",
        "HERMES_RAG_LLM_COOLDOWN_SECONDS": "0",
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_channel",
        "HERMES_RAG_ENABLED": "true",
        "HERMES_RAG_MODE": "local_readonly",
        "HERMES_RAG_PRIVATE_TEST_ONLY": "true",
        "HERMES_RAG_REQUIRE_RESPONSE_PACKET": "true",
        "HERMES_LLM_ENABLED": "true",
        "HERMES_LLM_API_CALL_ENABLED": "true",
        "HERMES_LLM_PROVIDER": "openrouter",
        "HERMES_LLM_MODEL": "openai/gpt-5.4-mini",
        "HERMES_LLM_API_KEY": "present",
        "HERMES_LLM_PRIVATE_TEST_ONLY": "true",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "true",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "true",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "HERMES_LLM_EXTERNAL_EXECUTION": "false",
    }
    env.update(overrides)
    return env


def event(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "msg-1",
        "channel_id": "private_channel",
        "channel_name": "hermes-private-test",
        "channel_scope": "private_test_only",
        "content": "마린, RAG LLM private test draft.",
        "author": {"id": "human", "bot": False},
    }
    data.update(overrides)
    return data


def make_root(content: str = "STOXL brand tone safe local context.") -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    base = Path(temp.name) / "knowledge" / "operation"
    base.mkdir(parents=True)
    (base / "tone.md").write_text(content, encoding="utf-8")
    return temp


def llm_success(_: dict) -> dict:
    return {
        "api_call_attempted": True,
        "api_call_succeeded": True,
        "api_call_failed": False,
        "provider": "openrouter",
        "model": "openai/gpt-5.4-mini",
        "response_text": "This is a review-only draft. No external action has been taken.\n\nSTOXL draft preview.",
    }


def llm_error(_: dict) -> dict:
    result = llm_success(_)
    result.update({"api_call_succeeded": False, "api_call_failed": True, "error_type": "provider_error", "response_text": ""})
    return result


def llm_unsafe(_: dict) -> dict:
    result = llm_success(_)
    result["response_text"] = "I published it."
    return result


def send_success(_: dict) -> dict:
    return {"message_sent": True}


def send_429(_: dict) -> dict:
    return {"message_sent": False, "error_type": "429 rate limit"}


def approved_env(**overrides: object) -> dict[str, object]:
    env = ready_env(
        HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="true",
        HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE="I_APPROVE_ONE_PRIVATE_TEST_RAG_LLM_REPLY",
    )
    env.update(overrides)
    return env


def test_preflight_default_blocked() -> None:
    assert_true(build_rag_llm_private_reply_preflight({})["ready"] is False, "Default should block")


def test_preflight_required_blocks() -> None:
    assert_true("rag_llm_reply_enabled" in build_rag_llm_private_reply_preflight(ready_env(HERMES_RAG_LLM_REPLY_ENABLED="false"))["blocked_reasons"], "RAG LLM disabled blocks")
    assert_true("discord_send_enabled" in build_rag_llm_private_reply_preflight(ready_env(HERMES_DISCORD_SEND_MESSAGES="false"))["blocked_reasons"], "Discord send disabled blocks")
    assert_true("llm_api_call_enabled" in build_rag_llm_private_reply_preflight(ready_env(HERMES_LLM_API_CALL_ENABLED="false"))["blocked_reasons"], "LLM API disabled blocks")
    assert_true("private_test_channel_id_present" in build_rag_llm_private_reply_preflight(ready_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=""))["blocked_reasons"], "Missing channel blocks")


def test_preflight_source_operations_and_ready() -> None:
    assert_true(build_rag_llm_private_reply_preflight(ready_env(), source="operations")["ready"] is False, "operations blocks")
    assert_true(build_rag_llm_private_reply_preflight(ready_env())["ready"] is True, "All gates ready")


def test_pre_blocks_before_retrieval() -> None:
    preflight = build_rag_llm_private_reply_preflight(ready_env())
    cases = [
        (event(channel_scope="public"), "public_channel_blocked_before_retrieval"),
        (event(channel_scope="mapped"), "public_channel_blocked_before_retrieval"),
        (event(channel_id="other"), "private_channel_id_mismatch_blocked"),
        (event(author={"id": "bot", "bot": True}), "self_or_bot_blocked_before_retrieval"),
    ]
    for item, reason in cases:
        decision = should_allow_rag_llm_private_reply(item, preflight, env=ready_env())
        assert_true(decision["reason"] == reason, reason)
        assert_true(decision["will_retrieve"] is False, "Should block before retrieval")


def test_duplicate_cooldown_budget_source_blocks() -> None:
    preflight = build_rag_llm_private_reply_preflight(ready_env())
    state = build_private_test_reply_safety_state()
    state["processed_message_ids"] = ["message_hash:3a0de37932e8b197"]
    assert_true("duplicate" in should_allow_rag_llm_private_reply(event(), preflight, env=ready_env(), safety_state=state)["reason"], "Duplicate blocks")
    state = build_private_test_reply_safety_state()
    state["last_reply_at"] = "2999-01-01T00:00:00+00:00"
    assert_true("cooldown" in should_allow_rag_llm_private_reply(event(id="msg-2"), preflight, env=ready_env(HERMES_RAG_LLM_COOLDOWN_SECONDS="20"), safety_state=state)["reason"], "Cooldown blocks")
    state = build_private_test_reply_safety_state()
    state["reply_count"] = 2
    assert_true("budget" in should_allow_rag_llm_private_reply(event(id="msg-3"), preflight, env=ready_env(), safety_state=state)["reason"], "Budget blocks")
    assert_true("operations" in should_allow_rag_llm_private_reply(event(), preflight, source="operations", env=ready_env())["reason"], "operations blocks")
    assert_true("invalid_source" in should_allow_rag_llm_private_reply(event(), preflight, source="unknown", env=ready_env())["reason"], "unknown blocks")


def test_context_and_packet_blocks() -> None:
    with make_root("STOXL brand tone " + ("x" * 4000)) as temp:
        attempt = build_rag_llm_reply_pipeline_plan(event(), temp, ready_env(HERMES_RAG_LLM_MAX_CONTEXT_CHARS="10"), llm_client=llm_success, send_adapter=send_success)
        assert_true(attempt["reason"] == "context_safety_blocked", "Large context blocks")
    with make_root("STOXL brand tone safe") as temp:
        attempt = build_rag_llm_reply_pipeline_plan(event(), temp, ready_env(), source="unknown", llm_client=llm_success, send_adapter=send_success)
        assert_true(attempt["retrieval_executed"] is False, "Invalid source pre-blocks")


def test_llm_and_output_blocks() -> None:
    with make_root() as temp:
        provider = build_rag_llm_reply_pipeline_plan(event(id="msg-4"), temp, ready_env(), llm_client=llm_error, send_adapter=send_success)
        unsafe = build_rag_llm_reply_pipeline_plan(event(id="msg-5"), temp, ready_env(), llm_client=llm_unsafe, send_adapter=send_success)
        assert_true(provider["reason"] == "llm_provider_error", "Provider error blocks")
        assert_true(unsafe["reason"] == "output_safety_blocked", "Output safety blocks")
        assert_true(provider["message_sent"] is False and unsafe["message_sent"] is False, "No blocked send")


def test_payload_safety_failure_blocks() -> None:
    payload = build_rag_llm_reply_send_payload("This has raw id 123456789012345678.", {"source": "operation", "citations": []})
    assert_true(payload["safe"] is True, "Payload should redact raw IDs")


def test_success_mock_path_sends_once_and_audit_temp() -> None:
    with make_root() as temp:
        state = build_private_test_reply_safety_state()
        attempt = build_rag_llm_reply_pipeline_plan(event(id="msg-6"), temp, ready_env(), safety_state=state, llm_client=llm_success, send_adapter=send_success)
        assert_true(attempt["allowed"] is True, "Allowed success")
        assert_true(attempt["message_sent"] is True, "Mock send true")
        assert_true(state["reply_count"] == 1, "One send recorded")
        audit = record_rag_llm_reply_attempt(attempt, root=temp, write=True)
        assert_true(audit["written"] is True, "Audit writes in temp")


def test_send_exception_opens_circuit_breaker() -> None:
    with make_root() as temp:
        state = build_private_test_reply_safety_state()
        attempt = build_rag_llm_reply_pipeline_plan(event(id="msg-7"), temp, ready_env(), safety_state=state, llm_client=llm_success, send_adapter=send_429)
        assert_true(attempt["reason"] == "send_exception", "Send exception blocks")
        assert_true(state["circuit_breaker_open"] is True, "Circuit breaker opens")


def test_report_cli_safe_and_markdown() -> None:
    report = build_rag_llm_private_test_runtime_report(env={})
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true(report["actual_discord_send"] is False, "No actual send")
    assert_true(report["actual_llm_api_call"] is False, "No actual LLM")
    assert_true("sk-" not in text and "token=" not in text, "No secret")
    assert_true(not LONG_ID_RE.search(text), "No raw Discord ID")
    assert_true("RAG+LLM Private Test Runtime" in render_rag_llm_private_test_runtime_markdown(report), "Markdown")


def test_manual_approval_default_blocks_live_start() -> None:
    result = run_discord_private_test_rag_llm_reply_bot(env=ready_env())
    assert_true(result["started"] is False, "Default approval should not start")
    assert_true(result["blocked"] is True, "Default approval should block")
    assert_true(result["reason"] == "live_execution_requires_separate_manual_approval", "Manual approval reason should remain")
    approval = result["single_live_test_manual_approval"]
    assert_true(approval["required"] is True, "Approval required")
    assert_true(approval["approved"] is False, "Approval should be false")
    assert_true(approval["approval_phrase_value_logged"] is False, "Approval phrase value should not be logged")


def test_manual_approval_bad_combinations_block() -> None:
    cases = [
        ready_env(HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="true"),
        ready_env(HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="true", HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE="WRONG"),
        ready_env(HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="false", HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE="I_APPROVE_ONE_PRIVATE_TEST_RAG_LLM_REPLY"),
    ]
    for env in cases:
        assert_true(is_single_live_test_manually_approved(env) is False, "Bad approval combination should be false")
        result = run_discord_private_test_rag_llm_reply_bot(env=env)
        assert_true(result["reason"] == "live_execution_requires_separate_manual_approval", "Bad approval should block")
        assert_true(result["message_sent"] is False, "No message sent")


def test_manual_approval_exact_phrase_allows_mock_start_path() -> None:
    called: dict[str, object] = {"value": False}

    def mock_start(root: str | Path | None, env: dict[str, object] | None, preflight: dict[str, object]) -> dict[str, object]:
        called["value"] = True
        assert_true(preflight["ready"] is True, "Preflight must be ready before start boundary")
        return {
            "started": True,
            "blocked": False,
            "reason": "mock_runtime_start_path_reached",
            "message_sent": False,
            "actual_discord_send": False,
            "actual_llm_api_call": False,
            "embedding_api_called": False,
            "external_execution": False,
        }

    result = run_discord_private_test_rag_llm_reply_bot(env=approved_env(), start_adapter=mock_start)
    assert_true(called["value"] is True, "Approved path should reach mock start adapter")
    assert_true(result["started"] is True, "Mock start path should report started")
    assert_true(result["blocked"] is False, "Mock start path should not block")
    assert_true(result["message_sent"] is False, "No actual message sent in test")
    assert_true(result["actual_discord_send"] is False, "No actual Discord send in test")
    assert_true(result["actual_llm_api_call"] is False, "No actual LLM API call in test")
    assert_true(result["single_live_test_manual_approval"]["approved"] is True, "Manual approval should be true")


def test_approval_phrase_value_not_logged() -> None:
    report = build_rag_llm_private_test_runtime_report(env=approved_env())
    text = json.dumps(report, ensure_ascii=False)
    assert_true("I_APPROVE_ONE_PRIVATE_TEST_RAG_LLM_REPLY" not in text, "Approval phrase value should not be logged")
    approval = report["single_live_test_manual_approval"]
    assert_true(approval["required"] is True, "Approval required")
    assert_true(approval["approved"] is True, "Approved boolean should be present")
    assert_true(approval["approval_phrase_present"] is True, "Phrase presence boolean should be present")
    assert_true(approval["approval_phrase_value_logged"] is False, "Phrase value should not be logged")


def main() -> int:
    tests = [
        test_preflight_default_blocked,
        test_preflight_required_blocks,
        test_preflight_source_operations_and_ready,
        test_pre_blocks_before_retrieval,
        test_duplicate_cooldown_budget_source_blocks,
        test_context_and_packet_blocks,
        test_llm_and_output_blocks,
        test_payload_safety_failure_blocks,
        test_success_mock_path_sends_once_and_audit_temp,
        test_send_exception_opens_circuit_breaker,
        test_report_cli_safe_and_markdown,
        test_manual_approval_default_blocks_live_start,
        test_manual_approval_bad_combinations_block,
        test_manual_approval_exact_phrase_allows_mock_start_path,
        test_approval_phrase_value_not_logged,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM private test runtime tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
