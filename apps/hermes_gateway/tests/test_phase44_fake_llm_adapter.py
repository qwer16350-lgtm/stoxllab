from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase44_fake_llm_adapter import run_phase44_fake_llm_adapter


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_fake_adapter_deterministic_no_side_effects() -> None:
    first = run_phase44_fake_llm_adapter()
    second = run_phase44_fake_llm_adapter()
    assert_true(first["output"] == second["output"], "Deterministic")
    assert_true(first["output_schema_valid"] is True, "Schema valid")
    assert_true(first["actual_llm_api_call"] is False, "No LLM API")
    assert_true(first["discord_message_sent"] is False, "No Discord send")
    assert_true(first["external_execution"] is False, "No external")


def main() -> int:
    test_fake_adapter_deterministic_no_side_effects()
    print("PASS test_fake_adapter_deterministic_no_side_effects")
    print("All Phase 44 fake adapter tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
