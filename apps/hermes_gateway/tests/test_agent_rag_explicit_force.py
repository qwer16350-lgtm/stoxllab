from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_rag import retrieve_agent_rag_context, should_use_agent_rag


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_search(query: str, **_kwargs: object) -> dict[str, object]:
    return {
        "mode": "hybrid",
        "keyword_fallback": False,
        "fallback_reason": "",
        "results": [{"source_label": "Brand", "relative_path": "brand/guide.md", "media_type": "document", "chunk_id": "doc#1", "score": 0.9, "snippet": "STOXL brand direction"}],
    }


def test_explicit_force_uses_rag_when_enabled_even_auto_off() -> None:
    env = {"HERMES_AGENT_RAG_ENABLED": "true", "HERMES_AGENT_RAG_AUTO_ENABLED": "false"}
    decision = should_use_agent_rag(agent_name="marin", user_message="[내부자료] 전시 방향 정리", env=env)
    context = retrieve_agent_rag_context(agent_name="marin", user_message="[내부자료] 전시 방향 정리", env=env, search_fn=mock_search)
    assert_true(decision.use_rag is True, "forced")
    assert_true(decision.reason == "explicit_rag_requested", "force reason")
    assert_true(context.rag_used is True, "context used")
    assert_true("[INTERNAL_RAG_CONTEXT]" in context.prompt_context, "prompt context")


def main() -> int:
    test_explicit_force_uses_rag_when_enabled_even_auto_off()
    print("PASS test_explicit_force_uses_rag_when_enabled_even_auto_off")
    print("All agent RAG explicit force tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
