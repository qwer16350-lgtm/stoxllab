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


def test_conflicting_source_signal_and_instruction() -> None:
    registry = [{"source_id": "S1", "source_label": "A", "relative_path": "a.md", "excerpt": "일정이 서로 다릅니다"}]
    env = {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"}
    result = apply_grounded_answer_citations("Sources conflict. [S1]", registry, env)
    instruction = build_grounding_instructions(registry, env)
    assert_true(result["conflicting_source_signal_detected"] is True, "conflict detected")
    assert_true("sources conflict" in instruction, "conflict instruction")


def main() -> int:
    test_conflicting_source_signal_and_instruction()
    print("PASS test_conflicting_source_signal_and_instruction")
    print("All conflicting source tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
