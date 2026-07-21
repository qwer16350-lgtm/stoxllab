from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import company_rag_vector_index as rag


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_vector_build_blocks_without_allow_write() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        Path(index_dir, "nas_rag_index.json").write_text(json.dumps({"records": []}), encoding="utf-8")
        report = rag.build_rag_vector_index(
            allow_write=False,
            env={
                "HERMES_RAG_INDEX_DIR": index_dir,
                "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
                "HERMES_RAG_EMBEDDING_ENABLED": "true",
            },
        )
    assert_true(report["blocked"] is True, "blocked")
    assert_true(report["blocked_reason"] == "allow_rag_vector_index_write_missing", "write guard")
    assert_true(report["vector_index_written_local_only"] is False, "nothing written")
    assert_true(report["external_embedding_api_called"] is False, "no external embedding")


def test_model_missing_without_download_allow_blocks() -> None:
    original_loader = rag.load_local_embedding_model

    def missing_loader(_model_name: str, _device: str, allow_download: bool, **_kwargs: object) -> tuple[object | None, str]:
        assert_true(allow_download is False, "download remains disallowed")
        return None, "local_embedding_model_not_available"

    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        Path(index_dir, "nas_rag_index.json").write_text(json.dumps({"records": []}), encoding="utf-8")
        try:
            rag.load_local_embedding_model = missing_loader  # type: ignore[assignment]
            report = rag.build_rag_vector_index(
                allow_write=True,
                allow_local_model_download=False,
                env={
                    "HERMES_RAG_INDEX_DIR": index_dir,
                    "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
                    "HERMES_RAG_EMBEDDING_ENABLED": "true",
                },
            )
        finally:
            rag.load_local_embedding_model = original_loader  # type: ignore[assignment]
    assert_true(report["blocked"] is True, "blocked")
    assert_true(report["blocked_reason"] in {"local_model_download_not_allowed", "local_embedding_model_not_available"}, "model/download guard")


def main() -> int:
    test_vector_build_blocks_without_allow_write()
    print("PASS test_vector_build_blocks_without_allow_write")
    test_model_missing_without_download_allow_blocks()
    print("PASS test_model_missing_without_download_allow_blocks")
    print("All RAG vector index write guard tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
