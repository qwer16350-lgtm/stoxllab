from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_citations import build_source_registry, format_internal_source_footer


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_raw_absolute_path_is_redacted_to_safe_relative_path() -> None:
    raw = "C:/secret/nas/brand.md"
    registry = build_source_registry([{"source_label": "Brand", "relative_path": raw, "chunk_id": "c1", "score": 0.8, "snippet": "x"}])
    footer = format_internal_source_footer(registry, ["S1"], {"HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"})
    assert_true("C:" not in footer and "secret/nas" not in footer, "raw path hidden")
    assert_true("brand.md" in footer, "file remains")


def main() -> int:
    test_raw_absolute_path_is_redacted_to_safe_relative_path()
    print("PASS test_raw_absolute_path_is_redacted_to_safe_relative_path")
    print("All agent citation path redaction tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
