from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_rag import retrieve_agent_rag_context


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mock_many(_query: str, **_kwargs: object) -> dict[str, object]:
    return {
        "mode": "hybrid",
        "results": [
            {"source_label": f"Doc {i}", "relative_path": f"docs/{i}.md", "media_type": "document", "chunk_id": f"doc#{i}", "score": 0.9 - i * 0.01, "snippet": "x" * 300}
            for i in range(8)
        ],
    }


def test_context_bounds_limit_results_and_chars() -> None:
    env = {
        "HERMES_AGENT_RAG_ENABLED": "true",
        "HERMES_AGENT_RAG_MAX_RESULTS": "3",
        "HERMES_AGENT_RAG_MAX_CONTEXT_CHARS": "650",
        "HERMES_AGENT_RAG_MAX_SNIPPET_CHARS": "250",
    }
    context = retrieve_agent_rag_context(agent_name="hermes", user_message="[RAG] 자료", env=env, search_fn=mock_many)
    assert_true(context.result_count <= 3, "result cap")
    assert_true(context.context_chars <= 650, "context cap")
    assert_true(all(len(item["snippet"]) <= 250 for item in context.results), "snippet cap")


def main() -> int:
    test_context_bounds_limit_results_and_chars()
    print("PASS test_context_bounds_limit_results_and_chars")
    print("All agent RAG context bounds tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
