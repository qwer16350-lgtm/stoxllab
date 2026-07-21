from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_vector_index import build_rag_vector_index


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_image_embedding_uses_metadata_text_only() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        Path(index_dir, "nas_rag_index.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "source_label": "black shelf reference",
                            "relative_path": "references/furniture/steel/stoxl_black_shelf_reference.jpg",
                            "folder_name": "references/furniture/steel",
                            "file_name": "stoxl_black_shelf_reference.jpg",
                            "extension": ".jpg",
                            "asset_type": "image_metadata",
                            "media_type": "image",
                            "content_hash": "image-hash",
                            "width": 1920,
                            "height": 1080,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        report = build_rag_vector_index(
            allow_write=True,
            env={
                "HERMES_RAG_INDEX_DIR": index_dir,
                "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
                "HERMES_RAG_EMBEDDING_ENABLED": "true",
                "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock",
            },
        )
        record = json.loads(Path(vector_dir, "records.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert_true(record["media_type"] == "image", "image metadata")
    assert_true(record["chunk_id"] == "image#0", "image chunk")
    assert_true("stoxl_black_shelf_reference.jpg" in record["snippet"], "file metadata embedded")
    assert_true("1920x1080" in record["snippet"], "size metadata embedded")
    assert_true(report["vision_api_called"] is False, "no vision")
    assert_true(report["ocr_called"] is False, "no OCR")


def main() -> int:
    test_image_embedding_uses_metadata_text_only()
    print("PASS test_image_embedding_uses_metadata_text_only")
    print("All RAG image metadata embedding tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
