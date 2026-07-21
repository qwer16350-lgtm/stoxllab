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


class ProcessCacheModel:
    created = 0

    def __init__(self, _model_name: str, *, device: str, local_files_only: bool | None = None) -> None:
        self.device = device
        self.local_files_only = local_files_only
        ProcessCacheModel.created += 1

    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> list[list[float]]:
        return [[1.0] + [0.0] * 383 for _text in texts]


def test_process_cache_reuses_model_by_model_and_device() -> None:
    rag._MODEL_CACHE.clear()
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    first, first_reason = rag.load_local_embedding_model(model_name, "cpu", True, model_factory=ProcessCacheModel)
    second, second_reason = rag.load_local_embedding_model(model_name, "cpu", True, model_factory=ProcessCacheModel)
    third, third_reason = rag.load_local_embedding_model(model_name, "cuda", True, model_factory=ProcessCacheModel)
    assert_true(first_reason == second_reason == third_reason == "", "models loaded")
    assert_true(first is second, "same key reused")
    assert_true(third is not first, "different device uses different cache key")
    assert_true(ProcessCacheModel.created == 2, "two process cache entries")


def main() -> int:
    test_process_cache_reuses_model_by_model_and_device()
    print("PASS test_process_cache_reuses_model_by_model_and_device")
    print("All RAG model process cache tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
