from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_citations import apply_grounded_answer_citations, build_source_status


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_grounded_and_citations_disabled_by_default() -> None:
    status = build_source_status({})
    result = apply_grounded_answer_citations("Fact [S1]", [{"source_id": "S1"}], {})
    assert_true(status["grounded_answers"] is False, "grounded default off")
    assert_true(status["internal_citations"] is False, "citations default off")
    assert_true(result["content"] == "Fact [S1]", "content unchanged")
    assert_true(result["citation_validation_attempted"] is False, "no validation")


def main() -> int:
    test_grounded_and_citations_disabled_by_default()
    print("PASS test_grounded_and_citations_disabled_by_default")
    print("All agent citation default disabled tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
