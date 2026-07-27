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


def test_max_citation_limit_applies_to_footer_and_valid_ids() -> None:
    registry = [{"source_id": f"S{i}", "source_label": f"Doc {i}", "relative_path": f"{i}.md"} for i in range(1, 6)]
    result = apply_grounded_answer_citations(
        "Facts [S1][S2][S3][S4]",
        registry,
        {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true", "HERMES_AGENT_MAX_CITATIONS": "2"},
    )
    assert_true(result["citation_ids_valid"] == ["S1", "S2"], "limited valid")
    assert_true("[S3]" not in result["content"], "overflow removed")
    assert_true(result["citation_limit_applied"] is True, "limit metadata")


def main() -> int:
    test_max_citation_limit_applies_to_footer_and_valid_ids()
    print("PASS test_max_citation_limit_applies_to_footer_and_valid_ids")
    print("All agent citation max limit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
