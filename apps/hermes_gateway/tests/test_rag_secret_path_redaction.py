from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_nas_index import build_nas_index, scan_nas_files, search_nas_index


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_raw_path(payload: dict, raw_path: str) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    assert_true(raw_path not in text, "raw NAS absolute path redacted")
    assert_true(payload.get("nas_root_value_logged") is False, "NAS root value not logged")
    assert_true(payload.get("raw_nas_root_logged") is False, "raw NAS root flag false")
    assert_true(payload.get("secret_value_logged") is False, "secret flag false")


def test_scan_index_and_search_do_not_log_raw_nas_path() -> None:
    with tempfile.TemporaryDirectory() as nas_root, tempfile.TemporaryDirectory() as index_dir:
        Path(nas_root, "브랜드 톤.txt").write_text("브랜드 톤", encoding="utf-8")
        scan = scan_nas_files(dry_run=True, env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": index_dir})
        index = build_nas_index(allow_write=True, env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": index_dir})
        search = search_nas_index("브랜드", env={"HERMES_RAG_INDEX_DIR": index_dir})
        assert_no_raw_path(scan, nas_root)
        assert_no_raw_path(index, nas_root)
        assert_no_raw_path(search, nas_root)
        index_text = (Path(index_dir) / "nas_rag_index.json").read_text(encoding="utf-8")
    assert_true(nas_root not in index_text, "index file does not store raw NAS absolute path")
    assert_true("raw_nas_absolute_path_logged" in index_text, "index stores safety flag")


def main() -> int:
    test_scan_index_and_search_do_not_log_raw_nas_path()
    print("PASS test_scan_index_and_search_do_not_log_raw_nas_path")
    print("All RAG secret/path redaction tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
