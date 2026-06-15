from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agent_review_packet import build_agent_review_packet, render_agent_review_packet_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_review_packet_success_fixture() -> None:
    report = build_agent_review_packet()
    assert_true(report["review_packet_available"] is True, "Review packet available")
    assert_true(report["rule_only"] is True, "Rule only")
    assert_true(report["human_review_required"] is True, "Human review required")
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["relative_paths_only"] is True, "Relative paths")
    assert_true(report["full_content_included"] is False, "No full content")


def test_review_packet_readiness_false() -> None:
    report = build_agent_review_packet()
    for key in ("ready_for_llm_call", "ready_for_discord_send", "ready_for_embedding", "ready_for_external_sources", "ready_for_unattended_auto_reply"):
        assert_true(report[key] is False, f"{key} false")


def test_agent_boundaries_and_risk_flags() -> None:
    packets = build_agent_review_packet()["agent_review_packets"]
    kasumi = packets["kasumi"]
    marin = packets["marin"]
    decision = packets["decision_maker_review"]
    assert_true(kasumi["allowed_sources"] == ["operation"], "Kasumi operation only")
    assert_true("operations" in kasumi["blocked_sources"], "Kasumi blocks operations")
    assert_true("knowledge/operation/stoxl_operation_tone_sample.md" in kasumi["evidence_citations"], "Kasumi citation")
    assert_true(kasumi["ready_for_approval_packet"] is True, "Kasumi ready for approval packet")
    assert_true("operation" in marin["blocked_sources"], "Marin blocks operation")
    assert_true("operations" in marin["blocked_sources"], "Marin blocks operations")
    assert_true("no_evidence_citations" in marin["risk_flags"], "Marin no evidence flag")
    assert_true("not_ready_for_approval" in marin["risk_flags"], "Marin not ready flag")
    assert_true("broad_source_scope" in decision["risk_flags"], "Decision maker broad scope flag")
    assert_true("operation" in decision["allowed_sources"], "Decision maker can review operation")
    assert_true("not_ready_for_approval" in decision["risk_flags"], "Decision maker not ready flag")


def test_forbidden_unknown_and_no_full_content_flags() -> None:
    report = build_agent_review_packet()
    catalog = report["risk_flag_catalog"]
    for expected in (
        "no_evidence_citations",
        "forbidden_source_requested",
        "unknown_source_requested",
        "broad_source_scope",
        "full_content_requested",
        "not_ready_for_approval",
    ):
        assert_true(expected in catalog, f"{expected} in catalog")
    assert_true("forbidden_source_requested" in report["agent_review_packets"]["kasumi"]["risk_flags"], "operations forbidden flag")


def test_sensitive_values_not_logged() -> None:
    text = json.dumps(build_agent_review_packet(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    markdown = render_agent_review_packet_markdown(build_agent_review_packet())
    assert_true("Agent Review Packet" in markdown, "Markdown renders")


def main() -> int:
    tests = [
        test_review_packet_success_fixture,
        test_review_packet_readiness_false,
        test_agent_boundaries_and_risk_flags,
        test_forbidden_unknown_and_no_full_content_flags,
        test_sensitive_values_not_logged,
        test_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All agent review packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
