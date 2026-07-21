from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_runtime_agent_rag_status_never_builds_or_downloads() -> None:
    result = build_company_agent_message_result("operation-brief", "!agent-rag-status", env={"HERMES_AGENT_RAG_ENABLED": "true"})
    response = result["response"]
    assert_true(result["runtime_index_build"] is False, "no runtime index build")
    assert_true(response["model_download"] is False, "no model download")
    assert_true(response["external_embedding_api"] is False, "no external embedding API")
    assert_true(response["vision"] is False and response["ocr"] is False, "no vision/OCR")


def main() -> int:
    test_runtime_agent_rag_status_never_builds_or_downloads()
    print("PASS test_runtime_agent_rag_status_never_builds_or_downloads")
    print("All agent RAG no runtime index build tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
