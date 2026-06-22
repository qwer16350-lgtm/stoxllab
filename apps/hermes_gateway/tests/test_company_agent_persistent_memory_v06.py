from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

TEST_MEMORY_DIR = tempfile.TemporaryDirectory()
os.environ["HERMES_COMPANY_MEMORY_DIR"] = TEST_MEMORY_DIR.name

from company_agent_responder import build_approval_draft, build_company_agent_response
from company_agent_runtime import build_company_agent_message_result
from company_context_store import clear_handoff_context_store, get_latest_context_for_channel
from company_handoff import build_handoff_post_payload
from company_persistent_memory import (
    DEFAULT_MEMORY_DIR,
    append_memory_record,
    build_company_agent_memory_report,
    build_memory_query_report,
    build_memory_summary,
    ensure_memory_dir,
    load_recent_records,
    memory_dir_is_gitignored,
    search_memory_records,
)


SAFE_ENV = {
    "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
    "HERMES_COMPANY_AGENT_LLM_MODE": "off",
    "HERMES_COMPANY_AGENT_REPLY_MODE": "deterministic_fallback",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_memory_report_and_location() -> None:
    report = build_company_agent_memory_report(TEST_MEMORY_DIR.name)
    normalized_default = str(DEFAULT_MEMORY_DIR).replace("\\", "/")
    assert_true(report["persistent_memory_available"] is True, "memory available")
    assert_true(report["memory_backend"] == "jsonl", "JSONL backend")
    assert_true("apps/hermes_gateway/local/company_memory" in normalized_default, "default local path")
    assert_true(report["memory_dir_gitignored"] is True, "memory gitignored")
    assert_true(memory_dir_is_gitignored() is True, "gitignore helper")
    assert_true(report["rag_called"] is False, "no RAG")
    assert_true(report["embedding_called"] is False, "no embedding")
    assert_true(report["external_execution"] is False, "no external")


def test_append_load_search_and_redaction() -> None:
    secret_content = (
        "지원사업 후보 token=secret-token 123456789012345678 "
        "https://discord.com/api/webhooks/123/secret"
    )
    handoff = append_memory_record(
        "handoff",
        {
            "source_agent": "kasumi",
            "target_agent": "meiko",
            "source_channel": "kasumi-리서치",
            "target_channel": "meiko-검토",
            "title": "지원사업 후보 정리",
            "summary": "카스미가 지원사업 후보를 넘김",
            "content": secret_content,
            "next_action": "메이코 검토 필요",
            "status": "open",
            "DISCORD_BOT_TOKEN": "must-not-persist",
        },
        TEST_MEMORY_DIR.name,
    )
    approval = append_memory_record(
        "approval",
        {"source_agent": "lucy", "title": "문구 승인 요청", "summary": "발행 검토", "status": "pending"},
        TEST_MEMORY_DIR.name,
    )
    decision = append_memory_record(
        "decision",
        {"agent": "meiko", "title": "지원사업 1차 판단", "summary": "현재 보류", "decision": "보류", "status": "open"},
        TEST_MEMORY_DIR.name,
    )
    assert_true(handoff["record_written"] is True, "handoff append")
    assert_true(approval["record_written"] is True, "approval append")
    assert_true(decision["record_written"] is True, "decision append")
    assert_true(len(load_recent_records("handoff", 5, TEST_MEMORY_DIR.name)) >= 1, "handoff load")
    assert_true(len(load_recent_records("approval", 5, TEST_MEMORY_DIR.name)) >= 1, "approval load")
    assert_true(len(load_recent_records("decision", 5, TEST_MEMORY_DIR.name)) >= 1, "decision load")
    assert_true(len(load_recent_records("recent_item", 10, TEST_MEMORY_DIR.name)) >= 3, "recent index")
    matches = search_memory_records("지원사업", limit=10, memory_dir=TEST_MEMORY_DIR.name)
    assert_true(len(matches) >= 2, "keyword search")
    raw_files = "\n".join(path.read_text(encoding="utf-8") for path in Path(TEST_MEMORY_DIR.name).glob("*.jsonl"))
    assert_true("secret-token" not in raw_files, "token redacted")
    assert_true("123456789012345678" not in raw_files, "raw ID redacted")
    assert_true("must-not-persist" not in raw_files, "sensitive key omitted")
    assert_true("discord.com/api/webhooks" not in raw_files, "webhook URL redacted")


def test_runtime_hooks_persist_handoff_approval_and_decision() -> None:
    clear_handoff_context_store()
    payload = build_handoff_post_payload(
        {
            "selected_agent": "kasumi",
            "source_channel": "kasumi-리서치",
            "handoff_channel": "meiko-검토",
            "response": {"content": "시제품 지원사업 후보, 최신 공고 확인 필요"},
        },
        "지원사업 후보 정리",
    )
    approval = build_approval_draft(
        "lucy",
        "MML 인스타 문구 발행 검토",
        {"source_channel": "lucy-검토"},
    )
    decision = build_company_agent_response(
        "meiko",
        "지원사업 지원 여부 판단",
        {"source_channel": "meiko-검토", "target_channel": "meiko-검토"},
        SAFE_ENV,
    )
    assert_true(payload["handoff_context_saved"] is True, "handoff hook")
    assert_true(approval["persistent_approval_written"] is True, "approval hook")
    assert_true(decision["persistent_decision_written"] is True, "decision hook")
    assert_true(any(record.get("title") == "지원사업 후보 정리" for record in load_recent_records("handoff", 20)), "handoff persisted")


def test_memory_commands_format_results() -> None:
    recent = build_company_agent_message_result("meiko-검토", "!memory recent", env=SAFE_ENV)
    handoffs = build_company_agent_message_result("meiko-검토", "!memory handoffs", env=SAFE_ENV)
    approvals = build_company_agent_message_result("meiko-검토", "!memory approvals", env=SAFE_ENV)
    decisions = build_company_agent_message_result("meiko-검토", "!memory decisions", env=SAFE_ENV)
    recall = build_company_agent_message_result("meiko-검토", "!recall 지원사업", env=SAFE_ENV)
    for result in (recent, handoffs, approvals, decisions, recall):
        response = result["response"]
        assert_true(str(response["content"]).startswith("[MEMORY]"), "memory format")
        assert_true(response["rag_called"] is False, "memory no RAG")
        assert_true(response["embedding_called"] is False, "memory no embedding")
        assert_true(response["external_execution"] is False, "memory no external")
    assert_true("[handoff]" in handoffs["response"]["content"], "handoff command")
    assert_true("[approval]" in approvals["response"]["content"], "approval command")
    assert_true("[decision]" in decisions["response"]["content"], "decision command")
    assert_true("지원사업" in recall["response"]["content"], "recall result")


def test_persistent_context_fallback_after_in_memory_clear() -> None:
    append_memory_record(
        "handoff",
        {
            "source_agent": "kasumi",
            "target_agent": "meiko",
            "source_channel": "kasumi-리서치",
            "target_channel": "meiko-검토",
            "title": "재시작 후 지원사업 후보",
            "summary": "persistent fallback fixture",
            "content": "재시작 후에도 남는 시제품 지원사업 후보",
            "next_action": "메이코 재판단",
            "status": "open",
        },
        TEST_MEMORY_DIR.name,
    )
    clear_handoff_context_store()
    context = get_latest_context_for_channel("meiko-검토")
    result = build_company_agent_message_result(
        "meiko-검토",
        "!meiko 이 지원사업 다시 판단해줘",
        env=SAFE_ENV,
    )
    assert_true(context is not None and "재시작 후에도" in context["handoff_content"], "persistent context loaded")
    assert_true(result["handoff_context_used"] is True, "persistent context used")
    assert_true("재시작 후에도" in result["response"]["content"], "persistent content in response")
    assert_true(result["response"]["rag_called"] is False, "fallback no RAG")
    assert_true(result["response"]["embedding_called"] is False, "fallback no embedding")
    assert_true(result["response"]["external_execution"] is False, "fallback no external")


def test_query_report_and_empty_summary_are_safe() -> None:
    report = build_memory_query_report("지원사업", memory_dir=TEST_MEMORY_DIR.name)
    assert_true(report["results_count"] >= 1, "query report")
    assert_true(all(record["summary_present"] or record["content_preview_present"] for record in report["records"]), "safe previews")
    assert_true("저장된 관련 기록 없음" in build_memory_summary([]), "empty result text")
    assert_true(report["raw_discord_ids_logged"] is False, "no raw IDs")
    assert_true(report["secret_values_logged"] is False, "no secrets")


def main() -> int:
    ensure_memory_dir(TEST_MEMORY_DIR.name)
    tests = [
        test_memory_report_and_location,
        test_append_load_search_and_redaction,
        test_runtime_hooks_persist_handoff_approval_and_decision,
        test_memory_commands_format_results,
        test_persistent_context_fallback_after_in_memory_clear,
        test_query_report_and_empty_summary_are_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    clear_handoff_context_store()
    TEST_MEMORY_DIR.cleanup()
    print("All company agent persistent memory v0.6 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
