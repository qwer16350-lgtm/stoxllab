from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_agent_source_status_command_reports_safe_citation_state() -> None:
    result = build_company_agent_message_result("operation-brief", "!agent-source-status", env={"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"})
    content = result["response"]["content"]
    assert_true("Agent source status" in content, "title")
    assert_true("grounded answers: true" in content, "grounded true")
    assert_true("raw absolute paths: false" in content, "no raw paths")
    assert_true(result["response"]["runtime_index_build"] is False, "no index build")


def main() -> int:
    test_agent_source_status_command_reports_safe_citation_state()
    print("PASS test_agent_source_status_command_reports_safe_citation_state")
    print("All source status command tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
