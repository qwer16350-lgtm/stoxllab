"""Phase 32A LLM safety preflight tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_llm_preflight.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from llm_preflight import assert_llm_preflight_safe, build_llm_preflight_report, render_llm_preflight_markdown, run_llm_preflight


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_default_llm_disabled() -> None:
    report = build_llm_preflight_report({})
    assert_true(report["llm_enabled"] is False, "Default LLM should be disabled")
    assert_true("llm_disabled" in report["blocked_reasons"], "Disabled LLM should be a blocked reason")


def test_provider_disabled_not_ready() -> None:
    result = run_llm_preflight({"HERMES_LLM_ENABLED": "true"})
    assert_true(result["ready_for_llm_call"] is False, "Phase 32A should not be ready for actual call")
    assert_true("provider_disabled" in result["blocked_reasons"], "Provider disabled should block")


def test_api_key_present_boolean_only() -> None:
    report = build_llm_preflight_report({"HERMES_LLM_API_KEY": "sk-secret-value"})
    text = json.dumps(report, ensure_ascii=False)
    assert_true(report["api_key_present"] is True, "API key presence should be boolean")
    assert_true("sk-secret-value" not in text, "API key value must never appear")
    assert_true("sk-" not in text.lower(), "Token marker must not appear")


def test_dry_run_only_blocks_actual_call() -> None:
    result = run_llm_preflight(
        {
            "HERMES_LLM_ENABLED": "true",
            "HERMES_LLM_PROVIDER": "openrouter",
            "HERMES_LLM_MODEL": "example-model",
            "HERMES_LLM_API_KEY": "present",
            "HERMES_LLM_DRY_RUN_ONLY": "true",
        }
    )
    assert_true("dry_run_only_enabled" in result["blocked_reasons"], "Dry-run only should block actual LLM call")
    assert_true(result["ready_for_llm_call"] is False, "Dry-run only should not be ready for real call")


def test_private_test_only_false_blocked() -> None:
    result = run_llm_preflight({"HERMES_LLM_PRIVATE_TEST_ONLY": "false"})
    assert_true("not_private_test_only" in result["blocked_reasons"], "private_test_only=false should block")


def test_discord_send_allowed_true_blocked() -> None:
    result = run_llm_preflight({"HERMES_LLM_ALLOW_DISCORD_SEND": "true"})
    assert_true("discord_send_allowed" in result["blocked_reasons"], "LLM must not allow Discord send in Phase 32A")


def test_cost_guard_disabled_blocked() -> None:
    result = run_llm_preflight({"HERMES_LLM_COST_GUARD_ENABLED": "false"})
    assert_true("cost_guard_disabled" in result["blocked_reasons"], "Cost guard disabled should block")


def test_invalid_max_input_chars_blocked() -> None:
    result = run_llm_preflight({"HERMES_LLM_MAX_INPUT_CHARS": "0"})
    assert_true("invalid_max_input_chars" in result["blocked_reasons"], "Invalid input limit should block")


def test_invalid_max_output_chars_blocked() -> None:
    result = run_llm_preflight({"HERMES_LLM_MAX_OUTPUT_CHARS": "0"})
    assert_true("invalid_max_output_chars" in result["blocked_reasons"], "Invalid output limit should block")


def test_invalid_max_calls_blocked() -> None:
    result = run_llm_preflight({"HERMES_LLM_MAX_CALLS_PER_SESSION": "0"})
    assert_true("invalid_max_calls_per_session" in result["blocked_reasons"], "Invalid call budget should block")


def test_safety_assertions_all_false() -> None:
    report = build_llm_preflight_report({})
    assert_llm_preflight_safe(report)
    for value in report["safety_assertions"].values():
        assert_true(value is False, "All safety assertions should be false")


def test_markdown_render_possible() -> None:
    markdown = render_llm_preflight_markdown(build_llm_preflight_report({}))
    assert_true("# LLM Safety Preflight Report" in markdown, "Markdown renderer should return a report")
    assert_true("llm_api_called: false" in markdown, "Markdown should preserve no-call assertion")


def main() -> int:
    tests = [
        test_default_llm_disabled,
        test_provider_disabled_not_ready,
        test_api_key_present_boolean_only,
        test_dry_run_only_blocks_actual_call,
        test_private_test_only_false_blocked,
        test_discord_send_allowed_true_blocked,
        test_cost_guard_disabled_blocked,
        test_invalid_max_input_chars_blocked,
        test_invalid_max_output_chars_blocked,
        test_invalid_max_calls_blocked,
        test_safety_assertions_all_false,
        test_markdown_render_possible,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All LLM preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
