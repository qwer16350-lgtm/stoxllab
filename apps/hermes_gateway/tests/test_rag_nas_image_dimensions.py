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


def test_scan_reports_image_dimensions_without_vision_or_ocr() -> None:
    with tempfile.TemporaryDirectory() as nas_root:
        root = Path(nas_root)
        write_minimal_png(root / "sample.png", 320, 180)
        report = scan_nas_files(dry_run=True, env={"HERMES_RAG_NAS_ROOT": nas_root})
    asset = report["sample_assets"][0]
    assert_true(asset["extension"] == ".png", "png indexed")
    assert_true(asset["width"] == 320, "png width extracted")
    assert_true(asset["height"] == 180, "png height extracted")
    assert_true(asset["vision_api_called"] is False, "no vision")
    assert_true(asset["ocr_called"] is False, "no OCR")
    assert_true(report["would_write_index"] is False, "dry run does not write")
    assert_true(report["nas_write_attempted"] is False, "NAS write not attempted")


def test_unknown_image_dimensions_fallback_to_null() -> None:
    with tempfile.TemporaryDirectory() as nas_root, tempfile.TemporaryDirectory() as index_dir:
        root = Path(nas_root)
        (root / "camera.heic").write_bytes(b"not-real-heic")
        report = build_nas_index(
            allow_write=True,
            env={"HERMES_RAG_NAS_ROOT": nas_root, "HERMES_RAG_INDEX_DIR": index_dir},
        )
        payload = json.loads((Path(index_dir) / "nas_rag_index.json").read_text(encoding="utf-8"))
    record = payload["records"][0]
    assert_true(record["extension"] == ".heic", "heic supported")
    assert_true(record["width"] is None, "unknown image width remains null")
    assert_true(record["height"] is None, "unknown image height remains null")
    assert_true(record["vision_api_called"] is False, "no vision")
    assert_true(record["ocr_called"] is False, "no OCR")
    assert_true(report["vector_index_created"] is False, "no vector index")
    assert_true(report["external_execution"] is False, "no external execution")


def main() -> int:
    test_scan_reports_image_dimensions_without_vision_or_ocr()
    print("PASS test_scan_reports_image_dimensions_without_vision_or_ocr")
    test_unknown_image_dimensions_fallback_to_null()
    print("PASS test_unknown_image_dimensions_fallback_to_null")
    print("All RAG NAS image dimension tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
