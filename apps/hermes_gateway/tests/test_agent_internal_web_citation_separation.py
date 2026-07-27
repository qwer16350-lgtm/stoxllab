from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_llm import build_agent_llm_messages
from company_agent_citations import build_grounding_instructions


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_internal_and_web_contexts_stay_separate_with_grounding() -> None:
    prompt = build_agent_llm_messages(
        "kasumi",
        "기존 조사와 최신 정보 비교",
        {
            "internal_rag_prompt_context": "[INTERNAL_RAG_CONTEXT]\ninternal\n[/INTERNAL_RAG_CONTEXT]",
            "internal_rag_grounding_instructions": build_grounding_instructions([{"source_id": "S1"}], {"HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true", "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true"}),
            "web_reference_results_block": "[WEB_REFERENCE_RESULTS]\nweb\n[/WEB_REFERENCE_RESULTS]",
            "agent_rag_used": True,
        },
    )
    content = prompt["messages_preview"][1]["content"]
    assert_true("[INTERNAL_RAG_CONTEXT]" in content, "internal")
    assert_true("[WEB_REFERENCE_RESULTS]" in content, "web")
    assert_true("Do not mix internal source citations with web reference citations." in content, "separation instruction")


def main() -> int:
    test_internal_and_web_contexts_stay_separate_with_grounding()
    print("PASS test_internal_and_web_contexts_stay_separate_with_grounding")
    print("All internal/web citation separation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
