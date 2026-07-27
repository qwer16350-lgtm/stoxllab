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


def test_empty_registry_never_adds_footer() -> None:
    result = apply_grounded_answer_citations("Claim [S1]", [], {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"})
    assert_true("참고한 내부 자료" not in result["content"], "no footer")
    assert_true(result["source_registry_count"] == 0, "empty registry")


def main() -> int:
    test_empty_registry_never_adds_footer()
    print("PASS test_empty_registry_never_adds_footer")
    print("All empty registry citation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
