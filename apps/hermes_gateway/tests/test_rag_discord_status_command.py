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


def write_index(index_dir: str, records: list[dict]) -> None:
    root = Path(index_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "nas_rag_index.json").write_text(json.dumps({"records": records}, ensure_ascii=False), encoding="utf-8")


def test_rag_status_reports_available_index() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        write_index(index_dir, [{"file_name": "brand.md", "content_preview": "brand"}])
        result = build_company_agent_message_result("operation-brief", "!rag-status", env={"HERMES_RAG_INDEX_DIR": index_dir})
    response = result["response"]
    content = response["content"]
    assert_true(result["selected_agent"] == "hermes", "Hermes handles RAG")
    assert_true(result["rag_runtime_command"] is True, "RAG runtime command")
    assert_true(response["index_available"] is True, "index available")
    assert_true(response["record_count"] == 1, "record count")
    assert_true("index: available" in content, "available text")
    assert_true("records: 1" in content, "record count text")
    assert_true("mode: keyword_only" in content, "mode text")
    assert_true(result["outbound_guard_applied"] is True, "outbound guard")
    assert_true(result["index_write_attempted_from_runtime"] is False, "no runtime index write")
    assert_true(result["llm_called"] is False, "no LLM")
    assert_true(result["embedding_called"] is False, "no embedding")
    assert_true(result["vision_api_called"] is False, "no vision")
    assert_true(result["ocr_called"] is False, "no OCR")
    assert_true(result["external_execution"] is False, "no external")


def main() -> int:
    test_rag_status_reports_available_index()
    print("PASS test_rag_status_reports_available_index")
    print("All RAG Discord status command tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
