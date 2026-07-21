from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_rag_vector_index import HashEmbeddingBackend


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_hash_embedding_backend_is_local_and_normalized() -> None:
    backend = HashEmbeddingBackend(dimension=16)
    vectors = backend.encode_texts(["industrial brutal futuristic", "brand mood"])
    assert_true(len(vectors) == 2, "two vectors")
    assert_true(len(vectors[0]) == 16, "dimension")
    norm = sum(value * value for value in vectors[0]) ** 0.5
    assert_true(abs(norm - 1.0) < 0.001, "normalized")


def main() -> int:
    test_hash_embedding_backend_is_local_and_normalized()
    print("PASS test_hash_embedding_backend_is_local_and_normalized")
    print("All RAG local embedding backend tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
