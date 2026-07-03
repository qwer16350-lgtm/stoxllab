from __future__ import annotations

import json
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


def write_minimal_png(path: Path, width: int, height: int) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
    )


def test_image_under_pixel_limit_is_indexed() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        root = Path(nas_root)
        write_minimal_png(root / "small.png", 100, 50)
        report = scan_nas_files(
            dry_run=True,
            env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_MAX_IMAGE_PIXELS": "5000"},
        )
    assert_true(report["max_image_pixels"] == 5000, "max image pixels applied")
    assert_true(report["image_pixel_limit_enabled"] is True, "pixel limit enabled")
    assert_true(report["decompression_bomb_warning_suppressed"] is True, "warning suppression reported")
    assert_true(report["files_supported"] == 1, "image at limit supported")
    assert_true(report["skip_summary"].get("[image_pixel_too_large]", 0) == 0, "no pixel skip")
    assert_true(report["sample_assets"][0]["width"] == 100, "width retained")
    assert_true(report["sample_assets"][0]["height"] == 50, "height retained")


def test_image_over_pixel_limit_is_skipped_in_scan_and_index() -> None:
    with tempfile.TemporaryDirectory() as nas_root, tempfile.TemporaryDirectory() as index_dir:
        root = Path(nas_root)
        image = root / "oversized.png"
        write_minimal_png(image, 101, 50)
        before = image.read_bytes()
        scan = scan_nas_files(
            dry_run=True,
            env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_MAX_IMAGE_PIXELS": "5000"},
        )
        index = build_nas_index(
            allow_write=True,
            env={
                "HERMES_RAG_NAS_ROOT": nas_root,
                "HERMES_RAG_INDEX_DIR": index_dir,
                "HERMES_RAG_MAX_IMAGE_PIXELS": "5000",
            },
        )
        after = image.read_bytes()
        payload = json.loads((Path(index_dir) / "nas_rag_index.json").read_text(encoding="utf-8"))
    assert_true(scan["files_supported"] == 0, "oversized scan skipped")
    assert_true(scan["skip_summary"]["[image_pixel_too_large]"] == 1, "scan pixel skip reason")
    assert_true(index["index_record_count"] == 0, "oversized index skipped")
    assert_true(index["skip_summary"]["[image_pixel_too_large]"] == 1, "index pixel skip reason")
    assert_true(payload["records"] == [], "no oversized record written")
    assert_true(before == after, "NAS original unchanged")
    assert_true(scan["vision_api_called"] is False and index["vision_api_called"] is False, "no vision")
    assert_true(scan["ocr_called"] is False and index["ocr_called"] is False, "no OCR")
    assert_true(scan["llm_called"] is False and index["llm_called"] is False, "no LLM")
    assert_true(scan["embedding_called"] is False and index["embedding_called"] is False, "no embedding")
    assert_true(scan["web_search_called"] is False and index["web_search_called"] is False, "no web")
    assert_true(scan["external_execution"] is False and index["external_execution"] is False, "no external")
    assert_true(scan["raw_nas_absolute_path_logged"] is False, "scan raw path not logged")
    assert_true(index["raw_nas_absolute_path_logged"] is False, "index raw path not logged")


def test_byte_limit_still_applies_before_pixel_limit() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        root = Path(nas_root)
        write_minimal_png(root / "large-bytes.png", 100, 50)
        (root / "large-bytes.png").write_bytes((root / "large-bytes.png").read_bytes() + b"x" * 2048)
        report = scan_nas_files(
            dry_run=True,
            env={
                "HERMES_RAG_NAS_ROOT": nas_root,
                "HERMES_RAG_MAX_IMAGE_FILE_SIZE_MB": "1",
                "HERMES_RAG_MAX_IMAGE_PIXELS": "1",
            },
        )
    assert_true(report["skip_summary"]["[image_pixel_too_large]"] == 1, "pixel skip still applies under byte cap")


def main() -> int:
    test_image_under_pixel_limit_is_indexed()
    print("PASS test_image_under_pixel_limit_is_indexed")
    test_image_over_pixel_limit_is_skipped_in_scan_and_index()
    print("PASS test_image_over_pixel_limit_is_skipped_in_scan_and_index")
    test_byte_limit_still_applies_before_pixel_limit()
    print("PASS test_byte_limit_still_applies_before_pixel_limit")
    print("All RAG NAS image pixel limit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
