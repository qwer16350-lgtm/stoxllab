from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_citations import build_grounding_instructions


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_grounding_prompt_requires_registry_ids_and_unconfirmed_language() -> None:
    text = build_grounding_instructions(
        [{"source_id": "S1"}, {"source_id": "S2"}],
        {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"},
    )
    assert_true("Available internal source IDs: S1, S2" in text, "ids")
    assert_true("Do not invent source IDs" in text, "no invented source")
    assert_true("not confirmed by the retrieved internal material" in text, "unconfirmed")
    assert_true("[INTERNAL_GROUNDING_INSTRUCTIONS]" in text, "block")


def main() -> int:
    test_grounding_prompt_requires_registry_ids_and_unconfirmed_language()
    print("PASS test_grounding_prompt_requires_registry_ids_and_unconfirmed_language")
    print("All agent grounding prompt tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
