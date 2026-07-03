from __future__ import annotations

import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_nas_index import build_nas_index, scan_nas_files


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_image_extensions_are_supported_as_metadata_assets() -> None:
    with tempfile.TemporaryDirectory() as nas_root, tempfile.TemporaryDirectory() as index_parent:
        root = Path(nas_root)
        (root / "product.jpg").write_bytes(b"fake-jpg")
        (root / "scene.webp").write_bytes(b"fake-webp")
        report = scan_nas_files(dry_run=True, env={"HERMES_RAG_NAS_ROOT": nas_root})
        index = build_nas_index(
            allow_write=True,
            env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": str(Path(index_parent) / "idx")},
        )
    asset_types = {item["asset_type"] for item in report["sample_assets"]}
    assert_true(report["files_supported"] == 2, "images supported")
    assert_true("image_metadata" in asset_types, "image metadata asset")
    assert_true(index["index_file_written"] is True, "index written locally")
    assert_true(index["index_record_count"] == 2, "image records indexed")
    assert_true(index["thumbnail_created_on_nas"] is False, "no NAS thumbnail")
    assert_true(index["thumbnail_created_local"] is False, "no thumbnail in v0.8A test")
    assert_true(index["embedding_called"] is False, "no embedding")
    assert_true(index["vision_api_called"] is False, "no vision")
    assert_true(index["ocr_called"] is False, "no OCR")


def main() -> int:
    test_image_extensions_are_supported_as_metadata_assets()
    print("PASS test_image_extensions_are_supported_as_metadata_assets")
    print("All RAG NAS image asset indexing tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
