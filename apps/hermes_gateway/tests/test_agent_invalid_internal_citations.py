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


def test_invalid_internal_citation_is_removed_without_failure() -> None:
    result = apply_grounded_answer_citations(
        "Unsupported source [S9] but valid source [S1].",
        [{"source_id": "S1", "source_label": "Brand", "relative_path": "brand.md"}],
        {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"},
    )
    assert_true("[S9]" not in result["content"], "invalid removed")
    assert_true(result["citation_ids_invalid"] == ["S9"], "invalid metadata")
    assert_true(result["citation_ids_valid"] == ["S1"], "valid kept")


def main() -> int:
    test_invalid_internal_citation_is_removed_without_failure()
    print("PASS test_invalid_internal_citation_is_removed_without_failure")
    print("All agent invalid citation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
