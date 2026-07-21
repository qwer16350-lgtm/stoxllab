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


def test_agent_rag_status_command_reports_safe_booleans() -> None:
    result = build_company_agent_message_result("operation-brief", "!agent-rag-status", env={"HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_RAG_AUTO_ENABLED": "true"})
    content = result["response"]["content"]
    assert_true(result["selected_agent"] == "hermes", "hermes")
    assert_true("Agent RAG status" in content, "status title")
    assert_true("runtime index build: false" in content, "no runtime build")
    assert_true(result["discord_message_sent"] is False, "no send")
    assert_true(result["raw_nas_absolute_path_logged"] is False, "no raw path")


def main() -> int:
    test_agent_rag_status_command_reports_safe_booleans()
    print("PASS test_agent_rag_status_command_reports_safe_booleans")
    print("All agent RAG status command tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
