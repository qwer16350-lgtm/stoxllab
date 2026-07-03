from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CLI = REPO_ROOT / "apps" / "hermes_gateway" / "cli.py"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_cli(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged.update(env)
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=str(REPO_ROOT),
        env=merged,
        text=True,
        capture_output=True,
        timeout=30,
    )


def test_rag_scan_nas_argparse_registered() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        result = run_cli(
            [
                "--rag-scan-nas",
                "--dry-run",
                "--json",
                "--rag-max-files",
                "1234",
                "--rag-max-total-bytes",
                "5678",
                "--rag-max-file-size-mb",
                "9",
                "--rag-max-image-file-size-mb",
                "10",
                "--rag-max-image-pixels",
                "111222",
            ],
            {"HERMES_RAG_NAS_ROOT": nas_root},
        )
    assert_true(result.returncode == 0, result.stderr)
    assert_true("unrecognized arguments" not in result.stderr, "scan arg recognized")
    payload = json.loads(result.stdout)
    assert_true(payload["report_type"] == "rag_scan_nas_dry_run", "scan report type")
    assert_true(payload["max_files"] == 1234, "max files CLI override")
    assert_true(payload["max_total_bytes"] == 5678, "max total bytes CLI override")
    assert_true(payload["max_file_size_mb"] == 9, "max file size CLI override")
    assert_true(payload["max_image_file_size_mb"] == 10, "max image size CLI override")
    assert_true(payload["max_image_pixels"] == 111222, "max image pixels CLI override")


def test_rag_index_nas_argparse_registered() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        result = run_cli(["--rag-index-nas", "--json"], {"HERMES_RAG_NAS_ROOT": nas_root})
    assert_true(result.returncode == 0, result.stderr)
    assert_true("unrecognized arguments" not in result.stderr, "index arg recognized")
    payload = json.loads(result.stdout)
    assert_true(payload["blocked"] is True, "index blocks without allow flag")
    assert_true(payload["blocked_reason"] == "allow_rag_index_write_missing", "allow guard")


def test_rag_search_argparse_registered() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        result = run_cli(["--rag-search", "brand", "--json"], {"HERMES_RAG_INDEX_DIR": index_dir})
    assert_true(result.returncode == 0, result.stderr)
    assert_true("unrecognized arguments" not in result.stderr, "search arg recognized")
    payload = json.loads(result.stdout)
    assert_true(payload["report_type"] == "rag_search_nas_index", "search report type")
    assert_true(payload["query_present"] is True, "query accepted")


def main() -> int:
    test_rag_scan_nas_argparse_registered()
    print("PASS test_rag_scan_nas_argparse_registered")
    test_rag_index_nas_argparse_registered()
    print("PASS test_rag_index_nas_argparse_registered")
    test_rag_search_argparse_registered()
    print("PASS test_rag_search_argparse_registered")
    print("All RAG NAS CLI registration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
