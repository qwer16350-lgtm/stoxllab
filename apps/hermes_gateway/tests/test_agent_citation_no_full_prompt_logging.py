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


def test_citation_metadata_does_not_log_full_prompt_or_raw_values() -> None:
    result = apply_grounded_answer_citations(
        "Fact [S1]",
        [{"source_id": "S1", "source_label": "Doc", "relative_path": "safe/doc.md", "excerpt": "x" * 2000}],
        {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"},
    )
    assert_true("prompt" not in result, "no prompt logged")
    assert_true("excerpt" not in result, "no full document text logged")
    assert_true(result["raw_nas_absolute_path_logged"] is False, "no raw path")
    assert_true(result["raw_vector_logged"] is False, "no vector")


def main() -> int:
    test_citation_metadata_does_not_log_full_prompt_or_raw_values()
    print("PASS test_citation_metadata_does_not_log_full_prompt_or_raw_values")
    print("All citation no full prompt logging tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
