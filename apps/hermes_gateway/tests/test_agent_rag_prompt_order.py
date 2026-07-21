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


def test_prompt_order_tracks_rag_below_user_request_and_separate_from_web() -> None:
    prompt = build_agent_llm_messages(
        "reze",
        "기존 사업 자료 참고해줘",
        {
            "source_channel": "reze-전략기획",
            "internal_rag_prompt_context": "[INTERNAL_RAG_CONTEXT]\ninternal\n[/INTERNAL_RAG_CONTEXT]",
            "web_reference_results_block": "[WEB_REFERENCE_RESULTS]\nweb\n[/WEB_REFERENCE_RESULTS]",
            "agent_rag_used": True,
        },
    )
    user = prompt["messages_preview"][1]["content"]
    assert_true(user.index("Request:") < user.index("[INTERNAL_RAG_CONTEXT]"), "request before RAG")
    assert_true(user.index("[INTERNAL_RAG_CONTEXT]") < user.index("[WEB_REFERENCE_RESULTS]"), "RAG separate from web")
    assert_true(prompt["context_order"][0] == "system_policy", "policy first")
    assert_true(prompt["context_order"][4] == "internal_rag_reference", "RAG lower than request")


def main() -> int:
    test_prompt_order_tracks_rag_below_user_request_and_separate_from_web()
    print("PASS test_prompt_order_tracks_rag_below_user_request_and_separate_from_web")
    print("All agent RAG prompt order tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
