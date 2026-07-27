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


def test_source_registry_uses_retrieval_results_only_and_stable_ids() -> None:
    registry = build_source_registry(
        [
            {"source_label": "Brand", "relative_path": "01/brand.md", "media_type": "document", "chunk_id": "c1", "score": 0.9, "snippet": "brand"},
            {"source_label": "Ops", "relative_path": "02/ops.md", "media_type": "document", "chunk_id": "c2", "score": 0.8, "snippet": "ops"},
        ],
        {"HERMES_AGENT_MAX_CITATIONS": "5"},
    )
    assert_true([item["source_id"] for item in registry] == ["S1", "S2"], "stable IDs")
    assert_true(registry[0]["source_label"] == "Brand", "label")
    assert_true(registry[1]["relative_path"] == "02/ops.md", "path")


def main() -> int:
    test_source_registry_uses_retrieval_results_only_and_stable_ids()
    print("PASS test_source_registry_uses_retrieval_results_only_and_stable_ids")
    print("All agent source registry tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
