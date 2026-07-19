from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_index(index_dir: str) -> None:
    records = [
        {
            "source_label": "STOXL Brand Guide",
            "relative_path": "01_BRAND/brand_guide.md",
            "file_name": "brand_guide.md",
            "folder_name": "01_BRAND",
            "extension": ".md",
            "asset_type": "document_metadata",
            "media_type": "document",
            "chunk_index": 2,
            "content_preview": "STOXL brand guide homepage copy and tone notes.",
        },
        {
            "source_label": "poster reference 01",
            "relative_path": "03_MARKETING/posters/poster_reference_01.jpg",
            "file_name": "poster_reference_01.jpg",
            "folder_name": "03_MARKETING/posters",
            "extension": ".jpg",
            "asset_type": "image_metadata",
            "media_type": "image",
            "chunk_index": 0,
            "width": 1920,
            "height": 1080,
            "content_preview": "KakaoTalk poster image asset metadata.",
        },
    ]
    root = Path(index_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "nas_rag_index.json").write_text(json.dumps({"records": records}, ensure_ascii=False), encoding="utf-8")


def test_rag_search_formats_document_result() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        write_index(index_dir)
        result = build_company_agent_message_result("operation-brief", "!rag-search brand guide", env={"HERMES_RAG_INDEX_DIR": index_dir})
    response = result["response"]
    content = response["content"]
    assert_true(response["search_attempted"] is True, "search attempted")
    assert_true(response["result_count"] == 1, "one result")
    assert_true("STOXL Brand Guide" in content, "source label")
    assert_true("01_BRAND/brand_guide.md" in content, "relative path")
    assert_true("type: document" in content, "document type")
    assert_true("chunk: doc#2" in content, "chunk id")
    assert_true("score:" in content, "score")
    assert_true("snippet:" in content, "snippet")
    assert_true(result["index_write_attempted_from_runtime"] is False, "no index write")
    assert_true(result["web_search_called"] is False, "no web")
    assert_true(result["llm_called"] is False, "no LLM")


def test_rag_search_formats_image_result() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        write_index(index_dir)
        result = build_company_agent_message_result("operation-brief", "!rag-search KakaoTalk", env={"HERMES_RAG_INDEX_DIR": index_dir})
    content = result["response"]["content"]
    assert_true("poster reference 01" in content, "image source label")
    assert_true("03_MARKETING/posters/poster_reference_01.jpg" in content, "image relative path")
    assert_true("type: image" in content, "image type")
    assert_true("chunk: image#0" in content, "image chunk")
    assert_true("size: 1920x1080" in content, "image dimensions")
    assert_true(result["vision_api_called"] is False, "no vision")
    assert_true(result["ocr_called"] is False, "no OCR")


def main() -> int:
    test_rag_search_formats_document_result()
    print("PASS test_rag_search_formats_document_result")
    test_rag_search_formats_image_result()
    print("PASS test_rag_search_formats_image_result")
    print("All RAG Discord search command tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
