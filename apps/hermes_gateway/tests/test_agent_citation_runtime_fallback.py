from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_citations import apply_grounded_answer_citations


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_formatter_runtime_issue_keeps_body_response() -> None:
    result = apply_grounded_answer_citations(
        "Body [S1]",
        [{"source_id": "S1", "source_label": object(), "relative_path": object()}],
        {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"},
    )
    assert_true("Body" in result["content"], "body continued")
    assert_true(result["citation_validation_attempted"] is True, "validation attempted")


def main() -> int:
    test_formatter_runtime_issue_keeps_body_response()
    print("PASS test_formatter_runtime_issue_keeps_body_response")
    print("All citation runtime fallback tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
