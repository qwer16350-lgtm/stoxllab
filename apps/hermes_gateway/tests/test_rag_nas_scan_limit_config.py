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


def make_files(root: Path, count: int) -> None:
    for index in range(count):
        (root / f"doc-{index}.txt").write_text(f"문서 {index}", encoding="utf-8")


def test_env_max_files_controls_scan_limit() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        root = Path(nas_root)
        make_files(root, 4)
        report = scan_nas_files(dry_run=True, env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_MAX_FILES": "2"})
    assert_true(report["max_files"] == 2, "max files env")
    assert_true(report["files_seen"] == 2, "limited files seen")
    assert_true(report["scan_truncated"] is True, "truncated when over limit")


def test_scan_not_truncated_when_within_limit() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        root = Path(nas_root)
        make_files(root, 3)
        report = scan_nas_files(dry_run=True, env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_MAX_FILES": "10"})
    assert_true(report["max_files"] == 10, "max files env")
    assert_true(report["files_seen"] == 3, "all files seen")
    assert_true(report["scan_truncated"] is False, "not truncated")
    assert_true(report["max_total_bytes"] == 0, "default total byte cap")
    assert_true(report["max_file_size_mb"] == 25, "default file size")
    assert_true(report["max_image_file_size_mb"] == 25, "default image size")


def test_cli_style_limit_env_names_are_reported() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        root = Path(nas_root)
        make_files(root, 1)
        report = scan_nas_files(
            dry_run=True,
            env={
                "HERMES_RAG_NAS_ROOT": nas_root,
                "HERMES_RAG_MAX_FILES": "5000",
                "HERMES_RAG_MAX_TOTAL_BYTES": "12345",
                "HERMES_RAG_MAX_FILE_SIZE_MB": "30",
                "HERMES_RAG_MAX_IMAGE_FILE_SIZE_MB": "40",
            },
        )
    assert_true(report["max_files"] == 5000, "max files reported")
    assert_true(report["max_total_bytes"] == 12345, "max total bytes reported")
    assert_true(report["max_file_size_mb"] == 30, "file size reported")
    assert_true(report["max_image_file_size_mb"] == 40, "image size reported")


def main() -> int:
    test_env_max_files_controls_scan_limit()
    print("PASS test_env_max_files_controls_scan_limit")
    test_scan_not_truncated_when_within_limit()
    print("PASS test_scan_not_truncated_when_within_limit")
    test_cli_style_limit_env_names_are_reported()
    print("PASS test_cli_style_limit_env_names_are_reported")
    print("All RAG NAS scan limit config tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
