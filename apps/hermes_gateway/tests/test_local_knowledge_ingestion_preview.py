from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from local_knowledge_ingestion_preview import build_local_knowledge_ingestion_preview, render_local_knowledge_ingestion_preview_markdown, validate_knowledge_source


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_success_fixture() -> None:
    report = build_local_knowledge_ingestion_preview(source="operation")
    assert_true(report["ready_for_local_text_ingestion"] is True, "operation should be ready")
    assert_true(report["ready_for_embedding"] is False, "embedding false")
    assert_true(report["ready_for_external_sources"] is False, "external false")
    assert_true(report["ready_for_llm_prompt"] is False, "LLM prompt false")
    assert_true(report["ready_for_discord_send"] is False, "Discord send false")


def test_sources() -> None:
    assert_true(validate_knowledge_source("operation")["accepted"] is True, "operation accepted")
    assert_true(validate_knowledge_source("operations")["reason"] == "forbidden_source", "operations forbidden")
    assert_true(validate_knowledge_source("unknown")["reason"] == "unknown_source", "unknown rejected")


def test_relative_path_only_and_full_content_disabled() -> None:
    report = build_local_knowledge_ingestion_preview(source="operation", candidate_paths=["knowledge/operation/a.md", "C:/secret/a.md"])
    assert_true(len(report["candidate_files"]) == 1, "Relative path accepted")
    assert_true(len(report["blocked_candidates"]) == 1, "Absolute path blocked")
    assert_true(report["relative_paths_only"] is True, "Relative only")
    assert_true(report["full_content_included"] is False, "No full content")


def test_sensitive_values_not_logged() -> None:
    text = json.dumps(build_local_knowledge_ingestion_preview(), ensure_ascii=False)
    assert_true("sk-" not in text.lower() and "token=" not in text.lower(), "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_markdown() -> None:
    assert_true("Local Knowledge" in render_local_knowledge_ingestion_preview_markdown(build_local_knowledge_ingestion_preview()), "Markdown renders")


def main() -> int:
    for test in [test_success_fixture, test_sources, test_relative_path_only_and_full_content_disabled, test_sensitive_values_not_logged, test_markdown]:
        test()
        print(f"PASS {test.__name__}")
    print("All local knowledge ingestion preview tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
