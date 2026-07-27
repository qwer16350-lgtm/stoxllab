from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_citations import build_source_registry


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_source_label_and_path_bounds() -> None:
    registry = build_source_registry(
        [{"source_label": "L" * 200, "relative_path": "folder/" + "p" * 300, "chunk_id": "c1", "score": 0.7, "snippet": "x"}],
        {"HERMES_AGENT_MAX_SOURCE_LABEL_CHARS": "30", "HERMES_AGENT_MAX_SOURCE_PATH_CHARS": "60"},
    )
    assert_true(len(registry[0]["source_label"]) == 30, "label bound")
    assert_true(len(registry[0]["relative_path"]) <= 60, "path bound")


def main() -> int:
    test_source_label_and_path_bounds()
    print("PASS test_source_label_and_path_bounds")
    print("All agent citation label bounds tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
