from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_vector_index import build_rag_embedding_preflight


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_embedding_default_disabled_and_lazy() -> None:
    report = build_rag_embedding_preflight(env={})
    assert_true(report["embedding_enabled"] is False, "embedding disabled by default")
    assert_true(report["default_embedding_enabled"] is False, "default disabled")
    assert_true(report["embedding_dependency_lazy_import"] is True, "lazy import")
    assert_true(report["external_embedding_api_called"] is False, "no external embedding")
    assert_true(report["model_file_committed"] is False, "no model committed")
    assert_true(report["raw_vector_logged"] is False, "no raw vector")


def main() -> int:
    test_embedding_default_disabled_and_lazy()
    print("PASS test_embedding_default_disabled_and_lazy")
    print("All RAG embedding preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
