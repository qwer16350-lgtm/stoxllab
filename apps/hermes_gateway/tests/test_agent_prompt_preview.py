from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agent_prompt_preview import build_agent_prompt_preview, render_agent_prompt_preview_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_prompt_preview_success_fixture() -> None:
    report = build_agent_prompt_preview()
    assert_true(report["prompt_preview_available"] is True, "Prompt preview available")
    assert_true(report["rule_only"] is True, "Rule-only")
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["full_prompt_executed"] is False, "No prompt execution")
    assert_true(report["full_content_included"] is False, "No full content")


def test_prompt_preview_readiness_false() -> None:
    report = build_agent_prompt_preview()
    for key in ("ready_for_llm_call", "ready_for_discord_send", "ready_for_embedding", "ready_for_external_sources", "ready_for_unattended_auto_reply"):
        assert_true(report[key] is False, f"{key} false")


def test_prompt_previews() -> None:
    previews = build_agent_prompt_preview()["agent_prompt_previews"]
    assert_true(previews["kasumi"]["allowed_sources"] == ["operation"], "Kasumi operation")
    assert_true("knowledge/operation/stoxl_operation_tone_sample.md" in previews["kasumi"]["evidence_citations"], "Kasumi citation")
    assert_true(previews["marin"]["evidence_citations"] == [], "Marin no operation citation")
    assert_true("operation" in previews["decision_maker_review"]["allowed_sources"], "Decision maker operation")


def test_sensitive_values_not_logged() -> None:
    text = json.dumps(build_agent_prompt_preview(), ensure_ascii=False)
    assert_true("sk-" not in text.lower() and "token=" not in text.lower(), "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    assert_true("Agent Prompt" in render_agent_prompt_preview_markdown(build_agent_prompt_preview()), "Markdown renders")


def main() -> int:
    for test in [test_prompt_preview_success_fixture, test_prompt_preview_readiness_false, test_prompt_previews, test_sensitive_values_not_logged, test_markdown]:
        test()
        print(f"PASS {test.__name__}")
    print("All agent prompt preview tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
