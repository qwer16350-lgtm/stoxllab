from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_llm import build_agent_llm_messages


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_internal_rag_and_web_context_blocks_remain_separate() -> None:
    prompt = build_agent_llm_messages(
        "kasumi",
        "기존 조사와 오늘 가격 비교",
        {
            "internal_rag_prompt_context": "[INTERNAL_RAG_CONTEXT]\ninternal\n[/INTERNAL_RAG_CONTEXT]",
            "web_reference_results_block": "[WEB_REFERENCE_RESULTS]\nweb\n[/WEB_REFERENCE_RESULTS]",
            "agent_rag_used": True,
        },
    )
    content = prompt["messages_preview"][1]["content"]
    assert_true("[INTERNAL_RAG_CONTEXT]" in content, "internal block")
    assert_true("[WEB_REFERENCE_RESULTS]" in content, "web block")
    assert_true("[/INTERNAL_RAG_CONTEXT]\n\n[WEB_REFERENCE_RESULTS]" in content, "separate blocks")


def main() -> int:
    test_internal_rag_and_web_context_blocks_remain_separate()
    print("PASS test_internal_rag_and_web_context_blocks_remain_separate")
    print("All agent RAG web context separation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
