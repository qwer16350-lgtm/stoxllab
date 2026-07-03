from __future__ import annotations

import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_nas_index import build_nas_index, search_nas_index


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_index_write_blocks_without_allow_flag() -> None:
    with tempfile.TemporaryDirectory() as nas_root, tempfile.TemporaryDirectory() as index_dir:
        Path(nas_root, "brand.txt").write_text("브랜드 톤", encoding="utf-8")
        report = build_nas_index(
            allow_write=False,
            env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": index_dir},
        )
        index_contents = list(Path(index_dir).iterdir())
    assert_true(report["blocked"] is True, "blocked")
    assert_true(report["blocked_reason"] == "allow_rag_index_write_missing", "missing allow")
    assert_true(report["index_write_attempted"] is False, "write not attempted")
    assert_true(index_contents == [], "index dir empty")


def test_index_write_blocks_if_index_dir_inside_nas() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        Path(nas_root, "brand.txt").write_text("브랜드 톤", encoding="utf-8")
        report = build_nas_index(
            allow_write=True,
            env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": str(Path(nas_root) / "index")},
        )
    assert_true(report["blocked"] is True, "blocked")
    assert_true(report["blocked_reason"] == "index_dir_inside_nas_root_forbidden", "NAS write forbidden")
    assert_true(report["nas_write_attempted"] is False, "no NAS write")


def test_index_write_allowed_only_to_local_index_and_searches_keyword() -> None:
    with tempfile.TemporaryDirectory() as nas_root, tempfile.TemporaryDirectory() as index_dir:
        before_root = set(path.name for path in Path(nas_root).iterdir())
        Path(nas_root, "brand-tone.txt").write_text("STOXL 브랜드 톤 문서", encoding="utf-8")
        report = build_nas_index(
            allow_write=True,
            env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": index_dir},
        )
        search = search_nas_index("브랜드 톤", env={"HERMES_RAG_INDEX_DIR": index_dir})
        after_root = set(path.name for path in Path(nas_root).iterdir())
    assert_true(report["blocked"] is False, "not blocked")
    assert_true(report["index_file_written"] is True, "index written")
    assert_true(report["index_record_count"] == 1, "one record")
    assert_true(before_root | {"brand-tone.txt"} == after_root, "NAS has no new index artifacts")
    assert_true(search["blocked"] is False, "search not blocked")
    assert_true(search["result_count"] == 1, "search finds record")
    assert_true(search["results"][0]["raw_nas_absolute_path_logged"] is False, "no raw path")


def main() -> int:
    test_index_write_blocks_without_allow_flag()
    print("PASS test_index_write_blocks_without_allow_flag")
    test_index_write_blocks_if_index_dir_inside_nas()
    print("PASS test_index_write_blocks_if_index_dir_inside_nas")
    test_index_write_allowed_only_to_local_index_and_searches_keyword()
    print("PASS test_index_write_allowed_only_to_local_index_and_searches_keyword")
    print("All RAG NAS index write guard tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
