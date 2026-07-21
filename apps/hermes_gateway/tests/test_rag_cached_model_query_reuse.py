from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import company_rag_vector_index as rag


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeSentenceTransformer:
    created: list[dict[str, object]] = []

    def __init__(self, model_name: str, *, device: str, local_files_only: bool | None = None) -> None:
        self.model_name = model_name
        self.device = device
        self.local_files_only = local_files_only
        FakeSentenceTransformer.created.append(
            {"model_name": model_name, "device": device, "local_files_only": local_files_only}
        )

    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> list[list[float]]:
        return [[1.0] + [0.0] * 383 for _text in texts]


def test_cached_model_query_reuse_without_download_flag() -> None:
    rag._MODEL_CACHE.clear()
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    build_model, build_reason = rag.load_local_embedding_model(
        model_name,
        "cpu",
        True,
        model_factory=FakeSentenceTransformer,
    )
    query_model, query_reason = rag.load_local_embedding_model(
        model_name,
        "cpu",
        False,
        model_factory=FakeSentenceTransformer,
    )
    assert_true(build_reason == "", "build model loaded")
    assert_true(query_reason == "", "query model reused")
    assert_true(build_model is query_model, "same process model object reused")
    assert_true(len(FakeSentenceTransformer.created) == 1, "no second model load")


def main() -> int:
    test_cached_model_query_reuse_without_download_flag()
    print("PASS test_cached_model_query_reuse_without_download_flag")
    print("All RAG cached model query reuse tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
