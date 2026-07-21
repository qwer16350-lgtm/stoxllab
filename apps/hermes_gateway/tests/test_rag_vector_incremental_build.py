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


def write_index(index_dir: str, content_hash: str) -> None:
    Path(index_dir, "nas_rag_index.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_label": "Doc",
                        "relative_path": "docs/doc.md",
                        "file_name": "doc.md",
                        "asset_type": "document_metadata",
                        "media_type": "document",
                        "content_hash": content_hash,
                        "content_preview": "brand direction text",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_incremental_build_reuses_unchanged_vectors_and_rebuilds_changed() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        env = {
            "HERMES_RAG_INDEX_DIR": index_dir,
            "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
            "HERMES_RAG_EMBEDDING_ENABLED": "true",
            "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock",
        }
        write_index(index_dir, "hash-a")
        first = build_rag_vector_index(allow_write=True, env=env)
        second = build_rag_vector_index(allow_write=True, env=env)
        write_index(index_dir, "hash-b")
        third = build_rag_vector_index(allow_write=True, env=env)
    assert_true(first["full_rebuild"] is True, "first full rebuild")
    assert_true(second["incremental_build"] is True, "incremental mode")
    assert_true(second["vectors_reused"] == 1, "unchanged vector reused")
    assert_true(second["vectors_created"] == 0, "no new vector")
    assert_true(third["vectors_created"] == 1, "changed vector rebuilt")


def main() -> int:
    test_incremental_build_reuses_unchanged_vectors_and_rebuilds_changed()
    print("PASS test_incremental_build_reuses_unchanged_vectors_and_rebuilds_changed")
    print("All RAG vector incremental build tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
