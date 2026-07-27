from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_citations import apply_grounded_answer_citations, build_grounding_instructions


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_unsupported_internal_fact_language_is_flagged_without_citation() -> None:
    env = {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"}
    result = apply_grounded_answer_citations("이미 결정됐습니다.", [{"source_id": "S1", "source_label": "Doc", "relative_path": "doc.md"}], env)
    instruction = build_grounding_instructions([{"source_id": "S1"}], env)
    assert_true(result["unsupported_internal_fact_detected"] is True, "unsupported fact flagged")
    assert_true("not confirmed by the retrieved internal material" in instruction, "prompt asks unconfirmed language")


def main() -> int:
    test_unsupported_internal_fact_language_is_flagged_without_citation()
    print("PASS test_unsupported_internal_fact_language_is_flagged_without_citation")
    print("All unsupported fact language tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
