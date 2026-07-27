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


def test_compact_footer_lists_internal_sources() -> None:
    footer = format_internal_source_footer(
        [{"source_id": "S1", "source_label": "Brand Direction", "relative_path": "01_BRAND/brand.docx"}],
        ["S1"],
        {"HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATION_STYLE": "compact"},
    )
    assert_true("참고한 내부 자료" in footer, "title")
    assert_true("[S1] Brand Direction" in footer, "source")


def main() -> int:
    test_compact_footer_lists_internal_sources()
    print("PASS test_compact_footer_lists_internal_sources")
    print("All agent citation footer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
