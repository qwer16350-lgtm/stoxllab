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


def test_vector_index_build_writes_local_manifest_records_and_vectors() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        Path(index_dir, "nas_rag_index.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "source_label": "STOXL Brand Direction",
                            "relative_path": "01_BRAND/brand_direction.md",
                            "file_name": "brand_direction.md",
                            "asset_type": "document_metadata",
                            "media_type": "document",
                            "content_hash": "doc-hash",
                            "content_preview": "industrial brutal futuristic direction",
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
        manifest = json.loads(Path(vector_dir, "vector_manifest.json").read_text(encoding="utf-8"))
        records = Path(vector_dir, "records.jsonl").read_text(encoding="utf-8").splitlines()
    assert_true(report["blocked"] is False, "not blocked")
    assert_true(report["index_file_written"] is True, "index written")
    assert_true(report["vector_index_written_local_only"] is True, "local only")
    assert_true(report["vectors_created"] == 1, "vector created")
    assert_true(manifest["index_version"] == "v0.8C", "manifest version")
    assert_true(manifest["raw_nas_path_stored"] is False, "no raw NAS path")
    assert_true(len(records) == 1, "record mapping")
    assert_true(report["external_embedding_api_called"] is False, "no external embedding")


def main() -> int:
    test_vector_index_build_writes_local_manifest_records_and_vectors()
    print("PASS test_vector_index_build_writes_local_manifest_records_and_vectors")
    print("All RAG vector index build tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
