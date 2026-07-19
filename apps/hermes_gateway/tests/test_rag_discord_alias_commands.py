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
    Path(index_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "records": [
            {
                "source_label": "Homepage Copy",
                "relative_path": "02_WEB/homepage_copy.md",
                "file_name": "homepage_copy.md",
                "asset_type": "document_metadata",
                "media_type": "document",
                "content_preview": "homepage copy for STOXL web page",
            }
        ]
    }
    (Path(index_dir) / "nas_rag_index.json").write_text(json.dumps(payload), encoding="utf-8")


def test_docs_alias_uses_rag_search() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        write_index(index_dir)
        result = build_company_agent_message_result("operation-brief", "!docs homepage", env={"HERMES_RAG_INDEX_DIR": index_dir})
    assert_true(result["command"] == "docs", "docs command")
    assert_true(result["response"]["reply_text_source"] == "rag_search", "docs uses RAG search")
    assert_true("Homepage Copy" in result["response"]["content"], "docs result")


def test_recall_doc_alias_uses_rag_search() -> None:
    with tempfile.TemporaryDirectory() as index_dir:
        write_index(index_dir)
        result = build_company_agent_message_result("operation-brief", "!recall-doc homepage", env={"HERMES_RAG_INDEX_DIR": index_dir})
    assert_true(result["command"] == "recall-doc", "recall-doc command")
    assert_true(result["response"]["reply_text_source"] == "rag_search", "recall-doc uses RAG search")
    assert_true(result["llm_called"] is False, "no LLM")
    assert_true(result["embedding_called"] is False, "no embedding")


def main() -> int:
    test_docs_alias_uses_rag_search()
    print("PASS test_docs_alias_uses_rag_search")
    test_recall_doc_alias_uses_rag_search()
    print("PASS test_recall_doc_alias_uses_rag_search")
    print("All RAG Discord alias command tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
