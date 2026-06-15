from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agent_routing_dry_preview import build_agent_routing_dry_preview, render_agent_routing_dry_preview_markdown, route_allowed


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_routes() -> None:
    report = build_agent_routing_dry_preview()
    routes = report["agent_routes"]
    assert_true(routes["kasumi"] == ["operation"], "Kasumi operation")
    assert_true("operation" in routes["decision_maker_review"], "Decision maker all canonical")
    assert_true(routes["unrouted"] == [], "Unrouted none")


def test_allowed_blocked() -> None:
    assert_true(route_allowed("kasumi", "operation")["allowed"] is True, "Kasumi operation allowed")
    assert_true(route_allowed("kasumi", "operations")["reason"] == "forbidden_source", "Kasumi operations blocked")
    assert_true(route_allowed("marin", "operation")["reason"] == "source_not_allowed_for_agent", "Marin operation blocked")


def test_rule_only_safety() -> None:
    report = build_agent_routing_dry_preview()
    assert_true(report["routing_rule_only"] is True, "Rule only")
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["discord_message_sent"] is False, "No Discord")
    assert_true(report["ready_for_unattended_auto_reply"] is False, "No unattended")
    assert_true(not LONG_NUMBER_RE.search(json.dumps(report, ensure_ascii=False)), "No IDs")


def test_markdown() -> None:
    assert_true("Agent Routing" in render_agent_routing_dry_preview_markdown(build_agent_routing_dry_preview()), "Markdown renders")


def main() -> int:
    for test in [test_routes, test_allowed_blocked, test_rule_only_safety, test_markdown]:
        test()
        print(f"PASS {test.__name__}")
    print("All agent routing dry preview tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
