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


def test_rag_search_passes_global_outbound_guard() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        records = []
        for index in range(5):
            records.append(
                {
                    "source_label": f"Long Source {index}",
                    "relative_path": f"docs/long_source_{index}.md",
                    "file_name": f"long_source_{index}.md",
                    "asset_type": "document_metadata",
                    "media_type": "document",
                    "chunk_index": index,
                    "content_preview": "brand " + ("detailed source snippet " * 40),
                }
            )
        Path(index_dir, "nas_rag_index.json").write_text(json.dumps({"records": records}), encoding="utf-8")
        result = build_company_agent_message_result("operation-brief", "!rag-search brand", env={"HERMES_RAG_INDEX_DIR": index_dir})
    assert_true(result["outbound_guard_applied"] is True, "guard applied")
    assert_true(result["outbound_chunk_count"] >= 1, "chunk count")
    assert_true(result["discord_message_sent"] is False, "dry no send")
    assert_true(result["response"]["index_write_attempted_from_runtime"] is False, "no index build")
    assert_true(result["response"]["llm_called"] is False, "no LLM")
    assert_true(result["response"]["embedding_called"] is False, "no embedding")
    assert_true(result["response"]["vector_index_created"] is False, "no vector")
    assert_true(result["response"]["web_search_called"] is False, "no web")
    assert_true(result["response"]["vision_api_called"] is False, "no vision")
    assert_true(result["response"]["ocr_called"] is False, "no OCR")
    assert_true(result["response"]["external_execution"] is False, "no external")


def main() -> int:
    test_rag_search_passes_global_outbound_guard()
    print("PASS test_rag_search_passes_global_outbound_guard")
    print("All RAG Discord outbound guard tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
