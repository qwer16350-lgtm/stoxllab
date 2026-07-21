from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_vector_index import build_rag_vector_index, search_rag_hybrid


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_vector_index_and_search_do_not_expose_raw_paths_or_vectors() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        raw_path = str(Path(index_dir) / "secret" / "brand.md")
        Path(index_dir, "nas_rag_index.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "source_label": "Safe Brand",
                            "relative_path": "safe/brand.md",
                            "absolute_path": raw_path,
                            "file_name": "brand.md",
                            "content_hash": "hash",
                            "asset_type": "document_metadata",
                            "media_type": "document",
                            "content_preview": "brand guide",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        env = {"HERMES_RAG_INDEX_DIR": index_dir, "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir, "HERMES_RAG_EMBEDDING_ENABLED": "true", "HERMES_RAG_EMBEDDING_BACKEND": "deterministic_hash_mock"}
        report = build_rag_vector_index(allow_write=True, env=env)
        search = search_rag_hybrid("brand", env=env)
    encoded = json.dumps({"report": report, "search": search}, ensure_ascii=False)
    assert_true(raw_path not in encoded, "raw NAS path hidden")
    assert_true(str(vector_dir) not in encoded, "raw vector path hidden")
    assert_true(report["raw_nas_absolute_path_logged"] is False, "raw NAS flag")
    assert_true(search["raw_vector_logged"] is False, "raw vector flag")


def main() -> int:
    test_vector_index_and_search_do_not_expose_raw_paths_or_vectors()
    print("PASS test_vector_index_and_search_do_not_expose_raw_paths_or_vectors")
    print("All RAG vector path redaction tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
