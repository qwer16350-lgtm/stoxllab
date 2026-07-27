from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_citations import format_internal_source_footer


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_footer_only_lists_used_valid_sources() -> None:
    footer = format_internal_source_footer(
        [
            {"source_id": "S1", "source_label": "Used", "relative_path": "used.md"},
            {"source_id": "S2", "source_label": "Unused", "relative_path": "unused.md"},
        ],
        ["S1"],
        {"HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"},
    )
    assert_true("Used" in footer, "used source")
    assert_true("Unused" not in footer, "unused hidden")


def main() -> int:
    test_footer_only_lists_used_valid_sources()
    print("PASS test_footer_only_lists_used_valid_sources")
    print("All agent citation used source footer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
