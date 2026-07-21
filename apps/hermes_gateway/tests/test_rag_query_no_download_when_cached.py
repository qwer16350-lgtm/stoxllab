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


class DownloadTrackingModel:
    calls: list[bool | None] = []

    def __init__(self, _model_name: str, *, device: str, local_files_only: bool | None = None) -> None:
        self.device = device
        DownloadTrackingModel.calls.append(local_files_only)

    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> list[list[float]]:
        return [[1.0] + [0.0] * 383 for _text in texts]


def test_query_does_not_download_when_cached() -> None:
    rag._MODEL_CACHE.clear()
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    first, first_reason = rag.load_local_embedding_model(model_name, "cpu", True, model_factory=DownloadTrackingModel)
    second, second_reason = rag.load_local_embedding_model(model_name, "cpu", False, model_factory=DownloadTrackingModel)
    assert_true(first_reason == "" and second_reason == "", "model available")
    assert_true(first is second, "cached model returned")
    assert_true(DownloadTrackingModel.calls == [None], "query did not call model factory or download path")


def main() -> int:
    test_query_does_not_download_when_cached()
    print("PASS test_query_does_not_download_when_cached")
    print("All RAG query no-download tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
