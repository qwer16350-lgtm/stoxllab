from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase45_actual_llm_one_shot_preflight import build_phase45_actual_llm_one_shot_preflight, build_phase45_llm_env_diagnostics


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase45_default_blocked_no_api_no_send() -> None:
    report = build_phase45_actual_llm_one_shot_preflight()
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true(report["blocked"] is True, "Blocked")
    assert_true(report["ready_for_actual_llm_one_shot_manual_gate"] is False, "No readiness")
    assert_true(report["api_key_present"] is False, "No key")
    assert_true(report["actual_llm_api_call"] is False, "No API call")
    assert_true(report["actual_llm_api_call_attempted"] is False, "No API attempt alias")
    assert_true(report["actual_llm_api_called"] is False, "No API called alias")
    assert_true(report["llm_api_call_attempted"] is False, "No API attempt")
    assert_true(report["discord_send_allowed"] is False, "Discord send false")
    assert_true(report["discord_message_sent"] is False, "No Discord message")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external")


def ready_env() -> dict[str, str]:
    return {
        "HERMES_PHASE45A_MANUAL_APPROVAL": "true",
        "HERMES_PHASE45A_APPROVAL_PHRASE": "I_APPROVE_PHASE45A_ACTUAL_LLM_ONE_SHOT",
        "HERMES_PHASE45A_COST_GUARD": "true",
        "HERMES_PHASE45A_CALL_COUNT_GUARD": "true",
        "HERMES_LLM_API_KEY": "SENSITIVE_KEY_VALUE_DO_NOT_LOG",
        "HERMES_LLM_PROVIDER": "openrouter",
        "HERMES_LLM_MODEL": "redacted-model",
        "HERMES_LLM_BASE_URL": "https://redacted.example",
        "HERMES_DISCORD_SEND_MESSAGES": "false",
        "HERMES_DISCORD_PRIVATE_TEST_SEND": "false",
        "HERMES_LLM_API_CALL_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_EMBEDDING_ENABLED": "false",
        "HERMES_VECTOR_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
    }


def test_phase45_ready_booleans_without_calling_api() -> None:
    report = build_phase45_actual_llm_one_shot_preflight(ready_env())
    assert_true(report["blocked"] is False, "Gates ready")
    assert_true(report["ready_for_actual_llm_one_shot_manual_gate"] is True, "Manual gate ready")
    assert_true(report["api_key_present"] is True, "Key presence boolean")
    assert_true(report["provider_config_present"] is True, "Provider presence boolean")
    assert_true(report["model_config_present"] is True, "Model presence boolean")
    assert_true(report["base_url_present"] is True, "Base URL presence boolean")
    assert_true(report["gate_checks"]["api_key_present"] is True, "Key gate")
    assert_true(report["gate_checks"]["provider_config_present"] is True, "Provider gate")
    assert_true(report["gate_checks"]["model_config_present"] is True, "Model gate")
    assert_true(report["gate_checks"]["base_url_present"] is True, "Base URL gate")
    assert_true(report["gate_checks"]["discord_send_disabled"] is True, "Discord send disabled")
    assert_true("provider_config_missing" not in report["blocked_reasons"], "Provider not missing")
    assert_true("model_config_missing" not in report["blocked_reasons"], "Model not missing")
    assert_true("base_url_missing" not in report["blocked_reasons"], "Base URL not missing")
    assert_true("discord_send_enabled" not in report["blocked_reasons"], "Discord send disabled reason absent")
    assert_true(report["actual_llm_api_call"] is False, "No API call")
    assert_true(report["actual_llm_api_call_attempted"] is False, "No API attempt")
    assert_true(report["discord_api_send_called"] is False, "No Discord API")
    assert_true(report["discord_message_sent"] is False, "No Discord message")


def test_phase45_guards_and_redaction() -> None:
    report = build_phase45_actual_llm_one_shot_preflight({"OPENROUTER_API_KEY": "SENSITIVE_KEY_VALUE_DO_NOT_LOG"})
    assert_true("cost_guard_missing" in report["blocked_reasons"], "Cost guard required")
    assert_true("provider_config_missing" in report["blocked_reasons"], "Provider required")
    assert_true("model_config_missing" in report["blocked_reasons"], "Model required")
    assert_true("base_url_missing" in report["blocked_reasons"], "Base URL required")
    assert_true("SENSITIVE_KEY_VALUE_DO_NOT_LOG" not in json.dumps(report, ensure_ascii=False), "No key value")
    assert_true("I_APPROVE_" not in json.dumps(report, ensure_ascii=False), "No phrase")


def test_phase45_key_aliases_and_env_diagnostics() -> None:
    aliases = ("HERMES_LLM_API_KEY", "OPENROUTER_API_KEY", "HERMES_OPENROUTER_API_KEY")
    for key in aliases:
        env = {**ready_env()}
        env.pop("HERMES_LLM_API_KEY", None)
        env[key] = "SENSITIVE_KEY_VALUE_DO_NOT_LOG"
        report = build_phase45_actual_llm_one_shot_preflight(env)
        diagnostics = build_phase45_llm_env_diagnostics(env)
        assert_true(report["api_key_present"] is True, key)
        assert_true(diagnostics["api_key_present"] is True, key)
        assert_true(diagnostics["provider_config_present"] is True, "Provider diagnostics")
        assert_true(diagnostics["model_config_present"] is True, "Model diagnostics")
        assert_true(diagnostics["base_url_present"] is True, "Base URL diagnostics")
        assert_true(diagnostics["discord_send_disabled"] is True, "Discord disabled")
        assert_true(diagnostics["actual_llm_api_call_attempted"] is False, "No attempt")
        assert_true(diagnostics["actual_llm_api_called"] is False, "No call")
        text = json.dumps(diagnostics, ensure_ascii=False)
        assert_true("SENSITIVE_KEY_VALUE_DO_NOT_LOG" not in text, "No key value in diagnostics")
        assert_true("redacted-model" not in text, "No model value")
        assert_true("redacted.example" not in text, "No base URL value")


def main() -> int:
    for test in (test_phase45_default_blocked_no_api_no_send, test_phase45_ready_booleans_without_calling_api, test_phase45_guards_and_redaction, test_phase45_key_aliases_and_env_diagnostics):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 45A tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
