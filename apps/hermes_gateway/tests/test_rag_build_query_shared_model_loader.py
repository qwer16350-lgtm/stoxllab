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


class SharedLoaderModel:
    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> list[list[float]]:
        return [[1.0] + [0.0] * 383 for _text in texts]


def test_build_and_query_share_model_loader() -> None:
    calls: list[bool] = []
    model = SharedLoaderModel()
    original_loader = rag.load_local_embedding_model

    def fake_loader(model_name: str, device: str, allow_download: bool, **_kwargs: object) -> tuple[object, str]:
        assert_true(model_name == rag.DEFAULT_EMBEDDING_MODEL, "model name")
        assert_true(device == "cpu", "device")
        calls.append(allow_download)
        return model, ""

    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        Path(index_dir, "nas_rag_index.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "source_label": "STOXL Brand",
                            "relative_path": "brand.md",
                            "file_name": "brand.md",
                            "content_hash": "brand",
                            "content_preview": "industrial future mood",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        env = {
            "HERMES_RAG_INDEX_DIR": index_dir,
            "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir,
            "HERMES_RAG_EMBEDDING_ENABLED": "true",
            "HERMES_RAG_EMBEDDING_BACKEND": "local_sentence_transformers",
        }
        try:
            rag.load_local_embedding_model = fake_loader  # type: ignore[assignment]
            build = rag.build_rag_vector_index(allow_write=True, allow_local_model_download=True, env=env)
            search = rag.search_rag_hybrid("industrial future", env=env)
        finally:
            rag.load_local_embedding_model = original_loader  # type: ignore[assignment]
    assert_true(build["blocked"] is False, "build succeeds")
    assert_true(search["mode"] == "hybrid", "query uses hybrid")
    assert_true(calls == [True, False], "build and query use the shared loader")


def main() -> int:
    test_build_and_query_share_model_loader()
    print("PASS test_build_and_query_share_model_loader")
    print("All RAG shared model loader tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
