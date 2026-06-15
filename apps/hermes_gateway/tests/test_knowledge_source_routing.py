"""Phase 34B knowledge source routing tests."""

from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from knowledge_source_routing import (
    build_knowledge_source_routing_report,
    render_knowledge_source_routing_markdown,
    validate_agent_source_route,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_agent_source_routing_works() -> None:
    assert_true(validate_agent_source_route("marin", "marketing")["agent_source_allowed"] is True, "marin marketing")
    assert_true(validate_agent_source_route("lucy", "archive")["agent_source_allowed"] is True, "lucy archive")
    assert_true(validate_agent_source_route("kasumi", "operation")["agent_source_allowed"] is True, "kasumi operation")
    assert_true(validate_agent_source_route("meiko", "archive")["agent_source_allowed"] is True, "meiko archive")
    assert_true(validate_agent_source_route("reze", "strategy")["agent_source_allowed"] is True, "reze strategy")


def test_decision_maker_review_only() -> None:
    result = validate_agent_source_route("decision_maker_review", "brand")
    assert_true(result["agent_source_allowed"] is True, "Decision maker review should access brand")
    assert_true(result["review_only"] is True, "Decision maker route should be review-only")


def test_unknown_agent_blocks() -> None:
    result = validate_agent_source_route("unknown", "operation")
    assert_true(result["blocked"] is True, "Unknown agent should block")
    assert_true("unknown_or_unrouted_agent" in result["blocked_reasons"], "Unknown reason should appear")


def test_source_not_allowed_blocks() -> None:
    result = validate_agent_source_route("kasumi", "marketing")
    assert_true(result["blocked"] is True, "Kasumi marketing should block")
    assert_true("source_not_allowed_for_agent" in result["blocked_reasons"], "Source-not-allowed reason should appear")


def test_operations_source_blocks_for_all_agents() -> None:
    for agent in ["marin", "lucy", "kasumi", "meiko", "reze", "decision_maker_review"]:
        result = validate_agent_source_route(agent, "operations")
        assert_true(result["blocked"] is True, f"{agent} operations should block")
        assert_true("forbidden_source" in result["blocked_reasons"], "Forbidden source reason should appear")


def test_report_flags_and_markdown() -> None:
    report = build_knowledge_source_routing_report()
    assert_true(report["review_only"] is True, "Report should be review-only")
    assert_true(report["discord_message_sent"] is False, "Discord false")
    assert_true(report["llm_api_called"] is False, "LLM false")
    assert_true(report["embedding_api_called"] is False, "Embedding false")
    assert_true(report["external_execution"] is False, "External false")
    assert_true("Knowledge Source Routing" in render_knowledge_source_routing_markdown(report), "Markdown should render")


def main() -> int:
    tests = [
        test_agent_source_routing_works,
        test_decision_maker_review_only,
        test_unknown_agent_blocks,
        test_source_not_allowed_blocks,
        test_operations_source_blocks_for_all_agents,
        test_report_flags_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All knowledge source routing tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
