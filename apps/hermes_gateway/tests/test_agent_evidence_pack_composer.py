from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agent_evidence_pack_composer import build_agent_evidence_pack_composer, render_agent_evidence_pack_composer_markdown, validate_agent_source


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_composer_success_fixture() -> None:
    report = build_agent_evidence_pack_composer()
    assert_true(report["composer_available"] is True, "Composer available")
    assert_true(report["rule_only"] is True, "Rule-only")
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["relative_paths_only"] is True, "Relative only")
    assert_true(report["full_content_included"] is False, "No full content")


def test_readiness_false() -> None:
    report = build_agent_evidence_pack_composer()
    for key in ("ready_for_llm_call", "ready_for_discord_send", "ready_for_embedding", "ready_for_external_sources"):
        assert_true(report[key] is False, f"{key} false")


def test_agent_packs() -> None:
    packs = build_agent_evidence_pack_composer()["agent_evidence_packs"]
    assert_true("operation" in packs["kasumi"]["allowed_sources"], "Kasumi operation allowed")
    assert_true("operations" in packs["kasumi"]["blocked_sources"], "Kasumi operations blocked")
    assert_true("operation" in packs["marin"]["blocked_sources"], "Marin operation blocked")
    assert_true("operation" in packs["decision_maker_review"]["allowed_sources"], "Decision maker operation")
    assert_true(packs["unrouted"]["allowed_sources"] == [], "Unrouted none")


def test_validate_agent_source() -> None:
    assert_true(validate_agent_source("kasumi", "operation")["allowed"] is True, "Kasumi operation")
    assert_true(validate_agent_source("kasumi", "operations")["reason"] == "forbidden_source", "operations forbidden")
    assert_true(validate_agent_source("kasumi", "unknown")["reason"] == "unknown_source", "unknown rejected")
    assert_true(validate_agent_source("marin", "operation")["reason"] == "source_not_allowed_for_agent", "Marin operation blocked")


def test_sensitive_values_not_logged() -> None:
    text = json.dumps(build_agent_evidence_pack_composer(), ensure_ascii=False)
    assert_true("sk-" not in text.lower() and "token=" not in text.lower(), "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    assert_true("Evidence Pack" in render_agent_evidence_pack_composer_markdown(build_agent_evidence_pack_composer()), "Markdown renders")


def main() -> int:
    for test in [test_composer_success_fixture, test_readiness_false, test_agent_packs, test_validate_agent_source, test_sensitive_values_not_logged, test_markdown]:
        test()
        print(f"PASS {test.__name__}")
    print("All agent evidence pack composer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
