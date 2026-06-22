from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_llm import (
    build_agent_llm_messages,
    build_company_agent_llm_dry_run,
    build_company_agent_llm_report,
    generate_agent_reply,
)
from company_agent_prompts import get_agent_system_prompt
from company_agent_responder import build_company_agent_response


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_safe(report: dict) -> None:
    text = json.dumps(report, ensure_ascii=False)
    assert_true("123456789012345678" not in text, "raw Discord ID hidden")
    assert_true("secret-token" not in text, "secret hidden")
    assert_true("sk-secret" not in text, "API key hidden")
    assert_true("https://" not in text and "http://" not in text, "URL hidden")
    assert_true(report.get("secret_values_logged") is False, "secret flag")
    assert_true(report.get("raw_discord_ids_logged") is False, "raw IDs flag")


def llm_env() -> dict[str, str]:
    return {
        "HERMES_COMPANY_AGENT_LLM_ENABLED": "true",
        "HERMES_COMPANY_AGENT_LLM_MODE": "manual_command_only",
        "HERMES_COMPANY_AGENT_REPLY_MODE": "llm_with_deterministic_fallback",
        "HERMES_LLM_API_KEY": "sk-secret",
    }


def test_report_defaults_and_supported_mode() -> None:
    report = build_company_agent_llm_report({})
    assert_true(report["company_agent_llm_available"] is True, "available")
    assert_true(report["default_llm_enabled"] is False, "default disabled")
    assert_true(report["default_llm_mode"] == "off", "default off")
    assert_true(report["supported_llm_modes"] == ["off", "manual_command_only"], "modes")
    assert_true(report["current_llm_enabled"] is False, "current disabled")
    assert_safe(report)


def test_agent_prompts_exist_and_roles_are_specific() -> None:
    prompts = {agent: get_agent_system_prompt(agent) for agent in ("marin", "lucy", "kasumi", "meiko", "reze")}
    for agent, prompt in prompts.items():
        assert_true(bool(prompt), f"{agent} prompt exists")
        assert_true("external execution" in prompt.lower(), f"{agent} external rule")
        assert_true("raw Discord IDs" in prompt, f"{agent} raw ID rule")
    assert_true("marketing junior" in prompts["marin"], "Marin role")
    assert_true("marketing senior" in prompts["lucy"], "Lucy role")
    assert_true("research candidate opportunities" in prompts["kasumi"], "Kasumi role")
    assert_true("operation judgment" in prompts["meiko"], "Meiko role")
    assert_true("strategy office" in prompts["reze"], "Reze role")


def test_dry_run_assembles_prompt_without_calls() -> None:
    dry = build_company_agent_llm_dry_run(
        "marin",
        "MML Instagram copy please",
        {"command": "marin", "source_channel": "marketing-brief"},
    )
    assert_true(dry["prompt_available"] is True, "prompt")
    assert_true(dry["manual_command"] is True, "manual")
    assert_true(dry["would_attempt_llm"] is True, "would attempt")
    assert_true(dry["actual_llm_called"] is False, "no actual call")
    assert_true(dry["rag_called"] is False, "no rag")
    assert_true(dry["embedding_called"] is False, "no embedding")
    assert_true(dry["vector_index_created"] is False, "no vector")
    assert_true(dry["external_execution"] is False, "no external")
    assert_safe(dry)


def test_external_execution_request_is_refused_in_prompt() -> None:
    prompt = build_agent_llm_messages(
        "lucy",
        "publish this SNS and email it now",
        {"command": "lucy", "source_channel": "marketing-brief"},
    )
    prompt_text = json.dumps(prompt, ensure_ascii=False).lower()
    assert_true("do not perform external execution" in prompt_text, "external refused")
    assert_true("sns publishing" in prompt_text, "SNS publishing forbidden")
    assert_true("email sending" in prompt_text, "email forbidden")
    assert_true(prompt["rag_called"] is False, "no rag")
    assert_true(prompt["embedding_called"] is False, "no embedding")
    assert_true(prompt["external_execution"] is False, "no external")
    assert_safe(prompt)


def test_llm_failure_and_exception_fall_back_to_deterministic() -> None:
    failed = generate_agent_reply(
        "marin",
        "!marin draft copy",
        {"command": "marin"},
        llm_env(),
        llm_caller=lambda _prompt, _config: {
            "api_call_attempted": True,
            "api_call_succeeded": False,
            "api_call_failed": True,
        },
    )
    assert_true(failed["llm_attempted"] is True, "attempted")
    assert_true(failed["llm_succeeded"] is False, "failed")
    assert_true(failed["fallback_used"] == "deterministic", "fallback")
    assert_safe(failed)

    raised = generate_agent_reply(
        "meiko",
        "!meiko decide",
        {"command": "meiko"},
        llm_env(),
        llm_caller=lambda _prompt, _config: (_ for _ in ()).throw(RuntimeError("provider failed")),
    )
    assert_true(raised["llm_attempted"] is True, "exception attempted")
    assert_true(raised["fallback_used"] == "deterministic", "exception fallback")
    assert_safe(raised)


def test_runtime_uses_deterministic_when_llm_disabled() -> None:
    response = build_company_agent_response(
        "marin",
        "!marin draft copy",
        {"selected_agent": "marin", "command": "marin", "target_channel": "marketing-brief"},
        {
            "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
            "HERMES_COMPANY_AGENT_LLM_MODE": "off",
            "HERMES_COMPANY_AGENT_REPLY_MODE": "llm_with_deterministic_fallback",
        },
    )
    assert_true(response["reply_text_source"] == "deterministic_fallback", "deterministic")
    assert_true(response["llm_api_call_attempted"] is False, "no call")
    assert_true(response["rag_called"] is False, "no rag")
    assert_true(response["external_execution"] is False, "no external")
    assert_safe(response)


def test_llm_attempts_only_when_enabled_and_manual_command() -> None:
    success = generate_agent_reply(
        "reze",
        "!reze critique product direction",
        {"command": "reze"},
        llm_env(),
        llm_caller=lambda _prompt, _config: {
            "api_call_attempted": True,
            "api_call_succeeded": True,
            "response_text": "[REZE_STOXL / Reze] concise strategy note",
        },
    )
    assert_true(success["llm_attempted"] is True, "manual attempted")
    assert_true(success["llm_succeeded"] is True, "manual success")
    assert_true(success["response_text"].startswith("[REZE_STOXL"), "response text")
    assert_safe(success)

    plain = generate_agent_reply(
        "kasumi",
        "find support programs",
        {},
        llm_env(),
        llm_caller=lambda _prompt, _config: {
            "api_call_attempted": True,
            "api_call_succeeded": True,
            "response_text": "should not run",
        },
    )
    assert_true(plain["llm_attempted"] is False, "plain no attempt")
    assert_true(plain["fallback_used"] == "deterministic", "plain fallback")
    assert_safe(plain)


def main() -> int:
    tests = [
        test_report_defaults_and_supported_mode,
        test_agent_prompts_exist_and_roles_are_specific,
        test_dry_run_assembles_prompt_without_calls,
        test_external_execution_request_is_refused_in_prompt,
        test_llm_failure_and_exception_fall_back_to_deterministic,
        test_runtime_uses_deterministic_when_llm_disabled,
        test_llm_attempts_only_when_enabled_and_manual_command,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All company agent LLM v0.5 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
