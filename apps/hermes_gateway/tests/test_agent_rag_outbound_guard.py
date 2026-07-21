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


def test_agent_rag_runtime_result_still_uses_outbound_guard_preview() -> None:
    result = build_company_agent_message_result("operation-brief", "!agent-rag-status")
    assert_true(result["outbound_guard_applied"] is True, "outbound guard")
    assert_true(result["discord_api_send_called"] is False, "no send")
    assert_true(result["external_execution"] is False, "no external execution")


def main() -> int:
    test_agent_rag_runtime_result_still_uses_outbound_guard_preview()
    print("PASS test_agent_rag_runtime_result_still_uses_outbound_guard_preview")
    print("All agent RAG outbound guard tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
