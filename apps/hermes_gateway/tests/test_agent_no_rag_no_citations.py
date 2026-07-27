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


def test_no_rag_response_has_no_source_footer() -> None:
    result = build_company_agent_message_result("marketing-brief", "!marin [RAG OFF] 문장만 다듬어줘", env={"HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"})
    content = result["response"]["content"]
    assert_true(result.get("agent_rag_used") is False, "RAG not used")
    assert_true("참고한 내부 자료" not in content, "no footer")


def main() -> int:
    test_no_rag_response_has_no_source_footer()
    print("PASS test_no_rag_response_has_no_source_footer")
    print("All no-RAG no-citation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
