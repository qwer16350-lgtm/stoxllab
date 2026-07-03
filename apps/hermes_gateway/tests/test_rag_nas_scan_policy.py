from __future__ import annotations

import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_nas_index import scan_nas_files


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_dry_run_scan_reads_only_and_writes_nothing() -> None:
    with tempfile.TemporaryDirectory() as nas_root, tempfile.TemporaryDirectory() as index_dir:
        root = Path(nas_root)
        (root / "brand.md").write_text("브랜드 톤 기준", encoding="utf-8")
        (root / "ignored.tmp").write_text("skip", encoding="utf-8")
        before = sorted(path.name for path in root.iterdir())
        report = scan_nas_files(
            dry_run=True,
            env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": index_dir},
        )
        after = sorted(path.name for path in root.iterdir())
        index_contents = list(Path(index_dir).iterdir())
    assert_true(report["report_type"] == "rag_scan_nas_dry_run", "dry-run report")
    assert_true(report["nas_root_present"] is True, "root present")
    assert_true(report["nas_root_accessible"] is True, "root accessible")
    assert_true(report["files_seen"] == 2, "files seen")
    assert_true(report["files_supported"] == 1, "supported count")
    assert_true(report["files_skipped"] == 1, "skipped count")
    assert_true(report["would_write_index"] is False, "dry-run no index write")
    assert_true(report["nas_write_attempted"] is False, "no NAS write")
    assert_true(before == after, "NAS unchanged")
    assert_true(index_contents == [], "index dir unchanged")
    assert_true(report["embedding_called"] is False, "no embeddings")
    assert_true(report["llm_called"] is False, "no LLM")
    assert_true(report["web_search_called"] is False, "no web")
    assert_true(report["external_execution"] is False, "no external")


def main() -> int:
    test_dry_run_scan_reads_only_and_writes_nothing()
    print("PASS test_dry_run_scan_reads_only_and_writes_nothing")
    print("All RAG NAS scan policy tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
