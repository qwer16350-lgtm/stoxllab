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


class SemanticMockBackend:
    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            lowered = text.casefold()
            if "industrial" in lowered or "brutal" in lowered or "futuristic" in lowered or "분위기" in lowered:
                vectors.append([1.0, 0.0, 0.0])
            elif "grant" in lowered:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors


def test_hybrid_search_finds_semantic_match_without_exact_keywords() -> None:
    with tempfile.TemporaryDirectory() as index_dir, tempfile.TemporaryDirectory() as vector_dir:
        Path(index_dir, "nas_rag_index.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "source_label": "STOXL Brand Direction",
                            "relative_path": "01_BRAND/brand_direction.docx",
                            "file_name": "brand_direction.docx",
                            "asset_type": "document_metadata",
                            "media_type": "document",
                            "content_hash": "brand",
                            "content_preview": "industrial brutal futuristic visual language",
                        },
                        {
                            "source_label": "Grant Checklist",
                            "relative_path": "04_OPS/grant.md",
                            "file_name": "grant.md",
                            "asset_type": "document_metadata",
                            "media_type": "document",
                            "content_hash": "grant",
                            "content_preview": "grant application checklist",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        env = {"HERMES_RAG_INDEX_DIR": index_dir, "HERMES_RAG_VECTOR_INDEX_DIR": vector_dir, "HERMES_RAG_EMBEDDING_ENABLED": "true"}
        build_rag_vector_index(allow_write=True, env=env, embedding_backend=SemanticMockBackend())
        result = search_rag_hybrid("브랜드가 추구하는 분위기", env=env, embedding_backend=SemanticMockBackend())
    assert_true(result["mode"] == "hybrid", "hybrid mode")
    assert_true(result["result_count"] >= 1, "results")
    assert_true(result["results"][0]["source_label"] == "STOXL Brand Direction", "semantic top result")
    assert_true(result["results"][0]["semantic_score"] > 0.9, "semantic score")
    assert_true(result["external_embedding_api_called"] is False, "no external embedding")


def main() -> int:
    test_hybrid_search_finds_semantic_match_without_exact_keywords()
    print("PASS test_hybrid_search_finds_semantic_match_without_exact_keywords")
    print("All RAG hybrid search tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
